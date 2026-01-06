from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field
from typing import List, Optional, Union
import yt_dlp
import os
import tempfile
import shutil
import re
from urllib.parse import unquote
from dotenv import load_dotenv
from deepgram import DeepgramClient
from database import (
    init_database,
    get_video_record,
    create_video_record,
    update_video_record,
    delete_audio_file_path,
    get_all_videos,
    get_stats
)
from auth import authenticate_user, create_session, delete_session, get_current_user

# Load environment variables from .env file
load_dotenv()

app = FastAPI(title="YouTube Audio Transcription Service", version="1.0.0")

# Serve static files
os.makedirs("static", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_database()


class VideoRequest(BaseModel):
    """
    Request model for transcribing YouTube videos.
    
    You can provide videos in any of these ways:
    - videos: List of YouTube video IDs or URLs (recommended - accepts both)
    - video_ids: List of YouTube video IDs or URLs  
    - video_urls: List of YouTube video URLs
    
    Examples:
    - Video ID: "dQw4w9WgXcQ"
    - Full URL: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    - Short URL: "https://youtu.be/dQw4w9WgXcQ"
    """
    videos: Optional[List[str]] = Field(
        None,
        description="List of YouTube video IDs or URLs (recommended - accepts both). Examples: 'dQw4w9WgXcQ', 'https://www.youtube.com/watch?v=VIDEO_ID', 'https://youtu.be/VIDEO_ID'",
        example=["dQw4w9WgXcQ", "https://www.youtube.com/watch?v=VIDEO_ID_2", "https://youtu.be/VIDEO_ID_3"]
    )
    video_ids: Optional[List[str]] = Field(
        None,
        description="List of YouTube video IDs or URLs. Examples: 'dQw4w9WgXcQ', 'https://www.youtube.com/watch?v=VIDEO_ID'",
        example=["dQw4w9WgXcQ", "https://www.youtube.com/watch?v=VIDEO_ID"]
    )
    video_urls: Optional[List[str]] = Field(
        None,
        description="List of YouTube video URLs. Examples: 'https://www.youtube.com/watch?v=VIDEO_ID', 'https://youtu.be/VIDEO_ID'",
        example=["https://www.youtube.com/watch?v=VIDEO_ID", "https://youtu.be/VIDEO_ID"]
    )
    deepgram_api_key: Optional[str] = Field(
        None,
        description="Deepgram API key (optional if set via DEEPGRAM_API_KEY environment variable)",
        example="your-deepgram-api-key"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "videos": [
                    "dQw4w9WgXcQ",
                    "https://www.youtube.com/watch?v=VIDEO_ID_2",
                    "https://youtu.be/VIDEO_ID_3"
                ],
                "deepgram_api_key": "your-deepgram-api-key"
            }
        }


class TranscriptResponse(BaseModel):
    video_id: str
    video_url: Optional[str] = None
    transcript: str
    status: str
    from_cache: bool = False


class ErrorResponse(BaseModel):
    video_id: str
    video_url: Optional[str] = None
    error: str
    status: str


class TranscriptionResponse(BaseModel):
    success: List[TranscriptResponse]
    errors: List[ErrorResponse]


def extract_video_id(url_or_id: str) -> str:
    """
    Extract video ID from YouTube URL or return the ID if already provided.
    Supports various YouTube URL formats:
    - https://www.youtube.com/watch?v=VIDEO_ID
    - https://youtu.be/VIDEO_ID
    - https://www.youtube.com/embed/VIDEO_ID
    - https://www.youtube.com/v/VIDEO_ID
    - https://m.youtube.com/watch?v=VIDEO_ID
    - VIDEO_ID (direct ID)
    """
    # Strip whitespace
    url_or_id = url_or_id.strip()
    
    # If it's already just an ID (no special characters that URLs have)
    if not re.search(r'[?&=/]', url_or_id):
        return url_or_id
    
    # Try to extract from various YouTube URL formats
    patterns = [
        r'(?:youtube\.com\/watch\?v=|youtu\.be\/|youtube\.com\/embed\/|youtube\.com\/v\/|m\.youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})',
        r'youtube\.com\/watch\?.*[&?]v=([a-zA-Z0-9_-]{11})',
        r'youtu\.be\/([a-zA-Z0-9_-]{11})',
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url_or_id)
        if match:
            return match.group(1)
    
    # If no pattern matches, assume it's already an ID
    return url_or_id


def normalize_video_input(video_ids: Optional[List[str]], video_urls: Optional[List[str]], videos: Optional[List[str]] = None) -> List[tuple]:
    """
    Normalize video input to list of (video_id, video_url) tuples.
    Returns list of tuples: [(video_id, original_input), ...]
    Accepts video IDs, URLs, or a mix of both.
    """
    result = []
    
    # Handle the unified 'videos' field (accepts both IDs and URLs)
    if videos:
        for video in videos:
            video_id = extract_video_id(video)
            result.append((video_id, video))
    
    # Handle separate video_ids field (can contain IDs or URLs)
    if video_ids:
        for vid in video_ids:
            video_id = extract_video_id(vid)
            result.append((video_id, vid))
    
    # Handle separate video_urls field
    if video_urls:
        for url in video_urls:
            video_id = extract_video_id(url)
            result.append((video_id, url))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_result = []
    for video_id, original in result:
        if video_id not in seen:
            seen.add(video_id)
            unique_result.append((video_id, original))
    
    return unique_result


def download_audio(video_id: str, output_dir: str) -> str:
    """Download audio from YouTube video and return the file path."""
    url = f"https://www.youtube.com/watch?v={video_id}"
    os.makedirs(output_dir, exist_ok=True)

    ydl_opts = {
        "format": "bestaudio/best",
        "outtmpl": f"{output_dir}/{video_id}.%(ext)s",
        "postprocessors": [{
            "key": "FFmpegExtractAudio",
            "preferredcodec": "mp3",
            "preferredquality": "192",
        }],
        "noplaylist": True,
        "quiet": True,
        "no_warnings": True,
    }

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        
        # Find the downloaded file
        audio_file = None
        for ext in ['mp3', 'm4a', 'webm', 'opus']:
            potential_file = f"{output_dir}/{video_id}.{ext}"
            if os.path.exists(potential_file):
                audio_file = potential_file
                break
        
        if not audio_file:
            raise FileNotFoundError(f"Audio file not found for video {video_id}")
        
        return audio_file
    except Exception as e:
        raise Exception(f"Failed to download audio: {str(e)}")


def transcribe_audio(audio_file_path: str, api_key: str) -> str:
    """Transcribe audio file using Deepgram API."""
    try:
        # Initialize Deepgram client with API key
        client = DeepgramClient(api_key=api_key)
        
        # Read audio file
        with open(audio_file_path, "rb") as audio_file:
            audio_data = audio_file.read()
        
        # Transcribe using the new API format
        response = client.listen.v1.media.transcribe_file(
            request=audio_data,
            model="nova-2",
            smart_format=True,
            language="en"
        )
        
        # Extract transcript text
        transcript = response.results.channels[0].alternatives[0].transcript
        
        return transcript
    except Exception as e:
        raise Exception(f"Failed to transcribe audio: {str(e)}")


@app.post("/transcribe", response_model=TranscriptionResponse)
async def transcribe_videos(request: VideoRequest):
    """
    Download audio from YouTube videos and transcribe them using Deepgram.
    
    You can provide videos in any of these ways:
    - **videos**: List of YouTube video IDs or URLs (recommended - accepts both)
    - **video_ids**: List of YouTube video IDs or URLs
    - **video_urls**: List of YouTube video URLs
    
    Examples of valid inputs:
    - Video ID: "dQw4w9WgXcQ"
    - Full URL: "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    - Short URL: "https://youtu.be/dQw4w9WgXcQ"
    - Embed URL: "https://www.youtube.com/embed/dQw4w9WgXcQ"
    
    - **deepgram_api_key**: Deepgram API key (can also be set via DEEPGRAM_API_KEY env var)
    
    The service tracks processed videos in a database to avoid re-downloading and re-transcribing.
    """
    # Validate input
    if not request.videos and not request.video_ids and not request.video_urls:
        raise HTTPException(
            status_code=400,
            detail="At least one of 'videos', 'video_ids', or 'video_urls' must be provided"
        )
    
    # Get Deepgram API key
    api_key = request.deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
    if not api_key:
        raise HTTPException(
            status_code=400,
            detail="Deepgram API key is required. Provide it in the request or set DEEPGRAM_API_KEY environment variable."
        )
    
    # Normalize video input
    video_list = normalize_video_input(request.video_ids, request.video_urls, request.videos)
    
    # Create temporary directory for audio files
    temp_dir = tempfile.mkdtemp(prefix="youtube_audio_")
    
    success_results = []
    error_results = []
    
    for video_id, original_input in video_list:
        audio_file_path = None
        transcript = None
        from_cache = False
        
        try:
            # Check database for existing record
            db_record = get_video_record(video_id)
            
            if db_record:
                # If we have a successful transcript, return it
                if db_record['status'] == 'success' and db_record['transcript']:
                    success_results.append(TranscriptResponse(
                        video_id=video_id,
                        video_url=db_record.get('video_url') or original_input,
                        transcript=db_record['transcript'],
                        status="success",
                        from_cache=True
                    ))
                    continue
                
                # If status is failed, skip downloading (don't re-download)
                if db_record['status'] == 'failed':
                    error_results.append(ErrorResponse(
                        video_id=video_id,
                        video_url=db_record.get('video_url') or original_input,
                        error=db_record.get('error_message', 'Previous attempt failed'),
                        status="error"
                    ))
                    continue
                
                # If we have an audio file path from previous attempt, use it
                if db_record.get('audio_file_path') and os.path.exists(db_record['audio_file_path']):
                    audio_file_path = db_record['audio_file_path']
                else:
                    # Create or update record
                    create_video_record(video_id, original_input, "processing")
                    # Download audio
                    audio_file_path = download_audio(video_id, temp_dir)
                    update_video_record(video_id, audio_file_path=audio_file_path)
            else:
                # Create new record
                create_video_record(video_id, original_input, "processing")
                # Download audio
                audio_file_path = download_audio(video_id, temp_dir)
                update_video_record(video_id, audio_file_path=audio_file_path)
            
            # Transcribe audio
            transcript = transcribe_audio(audio_file_path, api_key)
            
            # Update database with success
            update_video_record(
                video_id,
                status="success",
                transcript=transcript
            )
            
            # Delete audio file only after successful transcription
            if audio_file_path and os.path.exists(audio_file_path):
                try:
                    os.remove(audio_file_path)
                    delete_audio_file_path(video_id)
                except Exception as e:
                    print(f"Warning: Could not delete audio file {audio_file_path}: {e}")
            
            success_results.append(TranscriptResponse(
                video_id=video_id,
                video_url=original_input,
                transcript=transcript,
                status="success",
                from_cache=False
            ))
            
        except Exception as e:
            error_msg = str(e)
            
            # Update database with failure
            if db_record and db_record['status'] != 'failed':
                update_video_record(
                    video_id,
                    status="failed",
                    error_message=error_msg
                )
            elif not db_record:
                create_video_record(video_id, original_input, "failed")
                update_video_record(
                    video_id,
                    error_message=error_msg
                )
            
            # Don't delete audio file on failure - keep it for retry
            error_results.append(ErrorResponse(
                video_id=video_id,
                video_url=original_input,
                error=error_msg,
                status="error"
            ))
    
    # Clean up temp directory (only if empty or after processing)
    try:
        # Only remove if directory is empty or after a delay
        if os.path.exists(temp_dir):
            # Check if directory is empty
            if not os.listdir(temp_dir):
                shutil.rmtree(temp_dir)
            # If not empty, files are kept for failed attempts
    except Exception as e:
        print(f"Warning: Could not clean up temp directory: {e}")
    
    return TranscriptionResponse(
        success=success_results,
        errors=error_results
    )


@app.get("/video/{video_id}")
async def get_video_status(video_id: str):
    """
    Get the status and transcript of a video by video_id or URL.
    
    You can provide either:
    - Video ID: `/video/dQw4w9WgXcQ`
    - Video URL: `/video/https://www.youtube.com/watch?v=dQw4w9WgXcQ`
    
    Returns 404 if the video hasn't been processed yet. Use POST /transcribe to process it first.
    """
    # Decode URL-encoded path parameter
    decoded_id = unquote(video_id)
    
    # Extract video ID from URL if provided
    extracted_id = extract_video_id(decoded_id)
    
    db_record = get_video_record(extracted_id)
    
    if not db_record:
        raise HTTPException(
            status_code=404,
            detail=f"Video '{extracted_id}' not found in database. Please transcribe it first using POST /transcribe endpoint."
        )
    
    return {
        "video_id": db_record['video_id'],
        "video_url": db_record.get('video_url'),
        "status": db_record['status'],
        "transcript": db_record.get('transcript'),
        "error_message": db_record.get('error_message'),
        "created_at": db_record['created_at'],
        "updated_at": db_record['updated_at']
    }


# Authentication endpoints
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str


@app.post("/api/login", response_model=LoginResponse)
async def login(request: LoginRequest):
    """Admin login endpoint."""
    if authenticate_user(request.username, request.password):
        token = create_session(request.username)
        return LoginResponse(token=token, username=request.username)
    raise HTTPException(status_code=401, detail="Invalid credentials")


class LogoutRequest(BaseModel):
    token: str


@app.post("/api/logout")
async def logout(request: LogoutRequest):
    """Logout endpoint."""
    delete_session(request.token)
    return {"message": "Logged out successfully"}


# Admin dashboard endpoints
@app.get("/api/admin/videos")
async def get_all_videos_endpoint(user: str = Depends(get_current_user)):
    """Get all videos with their status."""
    return get_all_videos()


@app.get("/api/admin/stats")
async def get_stats_endpoint(user: str = Depends(get_current_user)):
    """Get statistics about videos."""
    return get_stats()


# Admin dashboard GUI
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard page."""
    return FileResponse("static/admin.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}
