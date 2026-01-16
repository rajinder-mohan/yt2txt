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
    get_stats,
    get_setting,
    set_setting
)
from auth import authenticate_user, create_session, delete_session, get_current_user, authenticate_api_request, update_user_password, active_sessions
from email_service import send_channel_processing_results

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


class ChannelRequest(BaseModel):
    """Request model for getting video IDs from a YouTube channel."""
    channel_url: str = Field(
        ...,
        description="YouTube channel URL. Examples: 'https://www.youtube.com/@channelname', 'https://www.youtube.com/channel/CHANNEL_ID', 'https://www.youtube.com/c/channelname', 'https://www.youtube.com/user/username'",
        example="https://www.youtube.com/@channelname"
    )
    max_results: Optional[int] = Field(
        None,
        description="Maximum number of videos to return (optional, returns all if not specified)",
        example=50
    )


class ChannelVideoInfo(BaseModel):
    """Information about a video from a channel."""
    video_id: str
    video_url: str
    title: str
    duration: Optional[int] = None
    view_count: Optional[int] = None
    upload_date: Optional[str] = None


class ChannelResponse(BaseModel):
    """Response model for channel video IDs."""
    channel_url: str
    channel_name: Optional[str] = None
    total_videos: int
    videos: List[ChannelVideoInfo]


def normalize_channel_url(channel_url: str) -> str:
    """
    Normalize channel URL to ensure we get the videos page (excluding shorts).
    If the URL is a channel URL without /videos, append it.
    """
    channel_url = channel_url.strip()
    
    # Remove /shorts if present - we don't want shorts
    if '/shorts' in channel_url:
        channel_url = channel_url.replace('/shorts', '/videos')
    
    # If it's already a videos page, return as is
    if '/videos' in channel_url or '/streams' in channel_url:
        return channel_url
    
    # If it's a channel URL, append /videos to get all videos (not shorts)
    if '@' in channel_url or '/channel/' in channel_url or '/c/' in channel_url or '/user/' in channel_url:
        # Remove trailing slash if present
        if channel_url.endswith('/'):
            channel_url = channel_url[:-1]
        # Append /videos if not already there
        if not channel_url.endswith('/videos'):
            channel_url = f"{channel_url}/videos"
    
    return channel_url


def extract_all_channel_videos(channel_url: str, max_results: Optional[int] = None, exclude_shorts: bool = True):
    """
    Extract all videos from a channel with pagination support.
    Excludes shorts by default.
    
    Returns:
        tuple: (videos_list, channel_name)
    """
    videos = []
    channel_name = None
    
    # Configure yt-dlp to extract all videos with pagination
    ydl_opts = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": False,  # Get full video info
        "playlistend": max_results if max_results else None,
        # Use extractor args to get all videos (not just recent) and exclude shorts
        "extractor_args": {
            "youtube": {
                "tab": "all",  # Get all videos, not just recent
            }
        },
        # Ignore shorts playlist
        "ignoreerrors": True,
    }
    
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        # Extract channel information with automatic pagination
        # process=True (default) ensures yt-dlp paginates through all videos
        info = ydl.extract_info(channel_url, download=False)
        
        # Get channel name
        channel_name = info.get('channel') or info.get('uploader') or info.get('channel_id')
        
        # Process entries (yt-dlp automatically handles pagination)
        if 'entries' in info:
            entries = info['entries']
            if entries:
                for entry in entries:
                    if entry is None:
                        continue
                    
                    video_id = entry.get('id')
                    if not video_id:
                        continue
                    
                    # Get video metadata
                    video_url = entry.get('url') or f"https://www.youtube.com/watch?v={video_id}"
                    title = entry.get('title', 'Unknown Title')
                    duration = entry.get('duration')
                    view_count = entry.get('view_count')
                    upload_date = entry.get('upload_date')
                    
                    # Skip shorts if enabled
                    if exclude_shorts:
                        # Check URL for shorts
                        if '/shorts/' in video_url or '/shorts' in video_url:
                            continue
                        
                        # Check title for shorts indicator
                        title_lower = title.lower()
                        if '#shorts' in title_lower or '#Shorts' in title_lower:
                            continue
                        
                        # Check duration (shorts are typically < 60 seconds)
                        if duration and duration < 60:
                            continue
                        
                        # Additional check: if duration is None, try to get it
                        if duration is None:
                            try:
                                video_info = ydl.extract_info(video_url, download=False)
                                duration = video_info.get('duration')
                                if duration and duration < 60:
                                    continue
                            except:
                                pass
                    
                    # Format upload date if available
                    if upload_date and len(upload_date) == 8:
                        formatted_date = f"{upload_date[:4]}-{upload_date[4:6]}-{upload_date[6:8]}"
                    else:
                        formatted_date = upload_date
                    
                    videos.append({
                        'video_id': video_id,
                        'video_url': video_url,
                        'title': title,
                        'duration': duration,
                        'view_count': view_count,
                        'upload_date': formatted_date
                    })
                    
                    # Stop if we've reached max_results
                    if max_results and len(videos) >= max_results:
                        break
    
    return videos, channel_name


@app.post("/channel/videos", response_model=ChannelResponse)
async def get_channel_videos(request: ChannelRequest):
    """
    Get video IDs from a YouTube channel URL using yt-dlp.
    
    - Gets ALL videos with pagination (not just recent)
    - Excludes shorts by default (videos < 60 seconds)
    - Supports various YouTube channel URL formats
    
    Supports various YouTube channel URL formats:
    - https://www.youtube.com/@channelname
    - https://www.youtube.com/channel/CHANNEL_ID
    - https://www.youtube.com/c/channelname
    - https://www.youtube.com/user/username
    - https://www.youtube.com/@channelname/videos
    
    Returns a list of video IDs with their titles, URLs, and metadata.
    """
    try:
        channel_url = normalize_channel_url(request.channel_url)
        max_results = request.max_results
        
        # Extract all videos (with pagination, excluding shorts)
        videos_data, channel_name = extract_all_channel_videos(
            channel_url, 
            max_results=max_results,
            exclude_shorts=True
        )
        
        # Convert to ChannelVideoInfo objects
        videos = [
            ChannelVideoInfo(
                video_id=video['video_id'],
                video_url=video['video_url'],
                title=video['title'],
                duration=video.get('duration'),
                view_count=video.get('view_count'),
                upload_date=video.get('upload_date')
            )
            for video in videos_data
        ]
        
        if not videos:
            raise HTTPException(
                status_code=404,
                detail=f"No full-length videos found for channel URL: {channel_url} (shorts are excluded)"
            )
        
        return ChannelResponse(
            channel_url=channel_url,
            channel_name=channel_name,
            total_videos=len(videos),
            videos=videos
        )
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Private video" in error_msg or "Video unavailable" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=f"Channel or videos not accessible: {error_msg}"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract videos from channel: {error_msg}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing channel URL: {str(e)}"
        )


@app.get("/channel/videos")
async def get_channel_videos_get(channel_url: str, max_results: Optional[int] = None):
    """
    Get video IDs from a YouTube channel URL using yt-dlp (GET endpoint).
    
    Query parameters:
    - channel_url: YouTube channel URL (required)
    - max_results: Maximum number of videos to return (optional)
    
    Supports various YouTube channel URL formats:
    - https://www.youtube.com/@channelname
    - https://www.youtube.com/channel/CHANNEL_ID
    - https://www.youtube.com/c/channelname
    - https://www.youtube.com/user/username
    - https://www.youtube.com/@channelname/videos
    
    The endpoint automatically appends /videos to channel URLs if not present.
    """
    request = ChannelRequest(channel_url=channel_url, max_results=max_results)
    return await get_channel_videos(request)


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


class ChangePasswordRequest(BaseModel):
    """Request model for changing password."""
    current_password: str
    new_password: str
    username: Optional[str] = Field(None, description="Username (required if using API key, optional if using Bearer token)")


@app.post("/api/change-password")
async def change_password(
    request: ChangePasswordRequest,
    user: str = Depends(authenticate_api_request)
):
    """
    Change password for the authenticated user.
    
    Requires authentication (Bearer token or API key).
    - If using Bearer token: username is determined from token
    - If using API key: username must be provided in request body
    
    User must provide current password for verification.
    """
    # Determine which username to update
    if user == "api_user":
        # API key authentication - require username in request
        if not request.username:
            raise HTTPException(
                status_code=400,
                detail="Username is required when using API key authentication"
            )
        target_username = request.username
    else:
        # Bearer token authentication - use authenticated user
        target_username = user
    
    # Verify current password
    if not authenticate_user(target_username, request.current_password):
        raise HTTPException(
            status_code=401,
            detail="Current password is incorrect"
        )
    
    # Validate new password
    if len(request.new_password) < 6:
        raise HTTPException(
            status_code=400,
            detail="New password must be at least 6 characters long"
        )
    
    # Update password
    if update_user_password(target_username, request.new_password):
        # Invalidate all sessions for this user (force re-login)
        tokens_to_delete = [token for token, username in active_sessions.items() if username == target_username]
        for token in tokens_to_delete:
            delete_session(token)
        
        return {"message": f"Password changed successfully for user '{target_username}'. Please login again."}
    else:
        raise HTTPException(
            status_code=500,
            detail="Failed to update password"
        )


# Admin dashboard endpoints
@app.get("/api/admin/videos")
async def get_all_videos_endpoint(user: str = Depends(authenticate_api_request)):
    """Get all videos with their status. Supports Bearer token or API key authentication."""
    return get_all_videos()


@app.get("/api/admin/stats")
async def get_stats_endpoint(user: str = Depends(authenticate_api_request)):
    """Get statistics about videos. Supports Bearer token or API key authentication."""
    return get_stats()


# n8n Integration Endpoint for Channel Processing
class ChannelProcessRequest(BaseModel):
    """Request model for processing a YouTube channel (for n8n integration)."""
    channel_url: str = Field(..., description="YouTube channel URL")
    max_results: Optional[int] = Field(None, description="Maximum number of videos to process")
    deepgram_api_key: Optional[str] = Field(None, description="Deepgram API key (optional if set via env var)")


class ChannelProcessResponse(BaseModel):
    """Response model for channel processing."""
    channel_url: str
    channel_name: Optional[str] = None
    total_videos: int
    processed_videos: int
    success_count: int
    failed_count: int
    message: str
    video_results: List[dict]


@app.post("/api/channel/process", response_model=ChannelProcessResponse)
async def process_channel_videos(
    request: ChannelProcessRequest,
    user: str = Depends(authenticate_api_request)
):
    """
    Process a YouTube channel: Get video IDs, transcribe all videos, and save to DB.
    
    This endpoint is designed for n8n workflow integration:
    1. Gets video IDs from channel URL
    2. Transcribes all videos using existing /transcribe logic
    3. Saves results to database
    
    Supports various YouTube channel URL formats:
    - https://www.youtube.com/@channelname
    - https://www.youtube.com/channel/CHANNEL_ID
    - https://www.youtube.com/c/channelname
    - https://www.youtube.com/user/username
    """
    try:
        # Step 1: Get video IDs from channel (with pagination, excluding shorts)
        channel_url = normalize_channel_url(request.channel_url)
        max_results = request.max_results
        
        # Extract all videos (excluding shorts)
        videos_data, channel_name = extract_all_channel_videos(
            channel_url,
            max_results=max_results,
            exclude_shorts=True
        )
        
        videos_info = [
            {
                'video_id': video['video_id'],
                'video_url': video['video_url'],
                'title': video['title']
            }
            for video in videos_data
        ]
        
        if not videos_info:
            raise HTTPException(
                status_code=404,
                detail=f"No full-length videos found for channel URL: {channel_url} (shorts are excluded)"
            )
        
        # Step 2: Transcribe all videos
        api_key = request.deepgram_api_key or os.getenv("DEEPGRAM_API_KEY")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail="Deepgram API key is required. Provide it in the request or set DEEPGRAM_API_KEY environment variable."
            )
        
        # Create video request for transcription
        video_list = [(v['video_id'], v['video_url']) for v in videos_info]
        temp_dir = tempfile.mkdtemp(prefix="youtube_audio_")
        
        success_count = 0
        failed_count = 0
        video_results = []
        
        for video_id, video_url in video_list:
            audio_file_path = None
            transcript = None
            error_msg = None
            status = "failed"
            
            try:
                # Check database for existing record
                db_record = get_video_record(video_id)
                
                if db_record and db_record['status'] == 'success' and db_record['transcript']:
                    # Use cached transcript
                    transcript = db_record['transcript']
                    status = "success"
                    success_count += 1
                elif db_record and db_record['status'] == 'failed':
                    # Skip failed videos
                    error_msg = db_record.get('error_message', 'Previous attempt failed')
                    failed_count += 1
                else:
                    # Process video
                    if not db_record:
                        create_video_record(video_id, video_url, "processing")
                    
                    # Download audio
                    if db_record and db_record.get('audio_file_path') and os.path.exists(db_record['audio_file_path']):
                        audio_file_path = db_record['audio_file_path']
                    else:
                        audio_file_path = download_audio(video_id, temp_dir)
                        update_video_record(video_id, audio_file_path=audio_file_path)
                    
                    # Transcribe
                    transcript = transcribe_audio(audio_file_path, api_key)
                    update_video_record(video_id, status="success", transcript=transcript)
                    
                    # Delete audio file
                    if audio_file_path and os.path.exists(audio_file_path):
                        try:
                            os.remove(audio_file_path)
                            delete_audio_file_path(video_id)
                        except Exception as e:
                            print(f"Warning: Could not delete audio file {audio_file_path}: {e}")
                    
                    status = "success"
                    success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                status = "failed"
                failed_count += 1
                
                # Update database with failure
                db_record = get_video_record(video_id)
                if db_record and db_record['status'] != 'failed':
                    update_video_record(video_id, status="failed", error_message=error_msg)
                elif not db_record:
                    create_video_record(video_id, video_url, "failed")
                    update_video_record(video_id, error_message=error_msg)
            
            # Find video title
            video_title = next((v['title'] for v in videos_info if v['video_id'] == video_id), 'Unknown Title')
            
            video_results.append({
                'video_id': video_id,
                'video_url': video_url,
                'title': video_title,
                'status': status,
                'transcript': transcript if status == 'success' else None,
                'error': error_msg if status == 'failed' else None
            })
        
        # Clean up temp directory
        try:
            if os.path.exists(temp_dir) and not os.listdir(temp_dir):
                shutil.rmtree(temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")
        
        message = f"Processed {len(videos_info)} videos. {success_count} successful, {failed_count} failed."
        
        return ChannelProcessResponse(
            channel_url=channel_url,
            channel_name=channel_name,
            total_videos=len(videos_info),
            processed_videos=len(video_results),
            success_count=success_count,
            failed_count=failed_count,
            message=message,
            video_results=video_results
        )
        
    except yt_dlp.utils.DownloadError as e:
        error_msg = str(e)
        if "Private video" in error_msg or "Video unavailable" in error_msg:
            raise HTTPException(
                status_code=404,
                detail=f"Channel or videos not accessible: {error_msg}"
            )
        raise HTTPException(
            status_code=400,
            detail=f"Failed to extract videos from channel: {error_msg}"
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing channel: {str(e)}"
        )


# Admin dashboard GUI
@app.get("/", response_class=HTMLResponse)
async def admin_dashboard():
    """Admin dashboard page."""
    return FileResponse("static/admin.html")


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "healthy"}


# User Management Endpoints
class CreateUserRequest(BaseModel):
    """Request model for creating a user."""
    username: str = Field(..., min_length=3, description="Username (minimum 3 characters)")
    password: str = Field(..., min_length=6, description="Password (minimum 6 characters)")


class DeleteUserRequest(BaseModel):
    """Request model for deleting a user."""
    username: str


class UserInfo(BaseModel):
    """User information model."""
    username: str
    created_at: Optional[str] = None


@app.get("/api/admin/users", response_model=List[UserInfo])
async def list_users(user: str = Depends(authenticate_api_request)):
    """List all admin users. Requires authentication."""
    from database import get_db_connection, DB_TYPE
    
    try:
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                from psycopg2.extras import RealDictCursor
                cursor = conn.cursor(cursor_factory=RealDictCursor)
                cursor.execute("SELECT username, created_at FROM admin_users ORDER BY created_at")
                rows = cursor.fetchall()
                cursor.close()
                users = [{"username": row['username'], "created_at": str(row.get('created_at', ''))} for row in rows]
            else:  # SQLite
                cursor = conn.execute("SELECT username, created_at FROM admin_users ORDER BY created_at")
                rows = cursor.fetchall()
                users = [{"username": row['username'], "created_at": row['created_at']} for row in rows]
        
        return users
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to list users: {str(e)}"
        )


@app.post("/api/admin/users", response_model=UserInfo)
async def create_user(request: CreateUserRequest, user: str = Depends(authenticate_api_request)):
    """Create a new admin user. Requires authentication."""
    from auth import hash_password
    from database import get_db_connection, DB_TYPE
    
    try:
        password_hash = hash_password(request.password)
        
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                try:
                    cursor.execute("""
                        INSERT INTO admin_users (username, password_hash)
                        VALUES (%s, %s)
                        ON CONFLICT (username) DO UPDATE 
                        SET password_hash = EXCLUDED.password_hash
                    """, (request.username, password_hash))
                    cursor.close()
                except Exception as e:
                    cursor.close()
                    raise e
            else:  # SQLite
                conn.execute("""
                    INSERT OR REPLACE INTO admin_users (username, password_hash)
                    VALUES (?, ?)
                """, (request.username, password_hash))
        
        return {
            "username": request.username,
            "created_at": None
        }
    except Exception as e:
        error_msg = str(e)
        if "UNIQUE constraint" in error_msg or "duplicate key" in error_msg.lower():
            raise HTTPException(
                status_code=400,
                detail=f"Username '{request.username}' already exists"
            )
        raise HTTPException(
            status_code=500,
            detail=f"Failed to create user: {str(e)}"
        )


@app.delete("/api/admin/users/{username}")
async def delete_user(username: str, user: str = Depends(authenticate_api_request)):
    """Delete an admin user. Requires authentication. Cannot delete yourself."""
    from database import get_db_connection, DB_TYPE
    
    # Prevent deleting yourself
    if user != "api_user" and username == user:
        raise HTTPException(
            status_code=400,
            detail="You cannot delete your own account"
        )
    
    try:
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                cursor.execute("DELETE FROM admin_users WHERE username = %s", (username,))
                deleted_count = cursor.rowcount
                cursor.close()
            else:  # SQLite
                cursor = conn.execute("DELETE FROM admin_users WHERE username = ?", (username,))
                deleted_count = cursor.rowcount
        
        if deleted_count == 0:
            raise HTTPException(
                status_code=404,
                detail=f"User '{username}' not found"
            )
        
        return {"message": f"User '{username}' deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete user: {str(e)}"
        )


# Settings Management Endpoints
class SettingRequest(BaseModel):
    """Request model for updating a setting."""
    value: str


@app.get("/api/admin/settings/{setting_key}")
async def get_setting_endpoint(setting_key: str, user: str = Depends(authenticate_api_request)):
    """Get a setting value. Requires authentication."""
    value = get_setting(setting_key)
    return {"setting_key": setting_key, "value": value}


@app.post("/api/admin/settings/{setting_key}")
async def set_setting_endpoint(
    setting_key: str,
    request: SettingRequest,
    user: str = Depends(authenticate_api_request)
):
    """Set a setting value. Requires authentication."""
    if set_setting(setting_key, request.value):
        return {"message": f"Setting '{setting_key}' updated successfully", "value": request.value}
    else:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update setting '{setting_key}'"
        )
