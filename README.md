# YouTube Audio Transcription Microservice

A FastAPI microservice that downloads audio from YouTube videos and transcribes them using Deepgram's speech-to-text API. Features intelligent caching and tracking to avoid redundant downloads and transcriptions.

## Features

- Download audio from YouTube videos using video IDs or URLs
- Transcribe audio using Deepgram API
- Support for multiple video IDs/URLs in a single request
- **Database tracking** - Tracks all processed videos with status
- **Smart caching** - Returns cached transcripts without re-processing
- **Failed status tracking** - Prevents re-downloading failed videos
- **Selective cleanup** - Audio files only deleted after successful transcription
- **Admin Dashboard** - Web-based GUI for tracking and monitoring all videos
- **Authentication** - Secure admin login system
- Error handling for individual video processing
- RESTful API with automatic documentation
- **Dockerized** - Easy deployment with Docker

## Prerequisites

- Python 3.8+
- FFmpeg (required for audio conversion)
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg
  
  # macOS
  brew install ffmpeg
  ```

## Installation

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

2. Set up environment variables:
   ```bash
   # Copy the example file
   cp .env.example .env
   
   # Edit .env and add your Deepgram API key
   # Optionally customize admin credentials
   ```

## Running the Service

### Option 1: Docker (Recommended)

1. Build and run with Docker Compose:
   ```bash
   docker-compose up -d
   ```

2. Or build and run manually:
   ```bash
   docker build -t youtube-transcription .
   docker run -d -p 8001:8001 -e DEEPGRAM_API_KEY=your-api-key youtube-transcription
   ```

The service will be available at:
- **Admin Dashboard**: http://localhost:8001
- **API**: http://localhost:8001
- **Interactive Docs**: http://localhost:8001/docs
- **Health check**: http://localhost:8001/health

**Default Admin Credentials:**
- Username: Set via `ADMIN_USERNAME` in `.env` (default: `admin`)
- Password: Set via `ADMIN_PASSWORD` in `.env` (default: `admin`)

⚠️ **Important**: Change the default admin password in production by updating `.env` file!

### Option 2: Local Development

Start the FastAPI server:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

The API will be available at:
- **Admin Dashboard**: http://localhost:8001
- **API**: http://localhost:8001
- **Interactive Docs**: http://localhost:8001/docs
- **Health check**: http://localhost:8001/health

## Database

The service uses SQLite to track all processed videos. The database file `youtube_transcriptions.db` is automatically created on first run.

**Database Schema:**
- `video_id` - Unique YouTube video ID
- `video_url` - Original URL if provided
- `status` - Processing status: `processing`, `success`, or `failed`
- `transcript` - Transcribed text (stored for successful transcriptions)
- `audio_file_path` - Path to audio file (kept for failed attempts)
- `error_message` - Error details for failed attempts
- `created_at` / `updated_at` - Timestamps

## API Usage

### Transcribe Videos

**Endpoint:** `POST /transcribe`

**Request Body:**
```json
{
  "videos": [
    "dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=VIDEO_ID_2",
    "https://youtu.be/VIDEO_ID_3"
  ],
  "deepgram_api_key": "your-api-key"  // Optional if set as env var
}
```

**Alternative formats (also supported):**
```json
{
  "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "video_urls": ["https://www.youtube.com/watch?v=VIDEO_ID_3"],
  "deepgram_api_key": "your-api-key"
}
```

**Note:** 
- The `videos` field is recommended as it accepts both video IDs and URLs in a single field
- You can also use `video_ids` or `video_urls` separately
- The service automatically extracts video IDs from any YouTube URL format:
  - `https://www.youtube.com/watch?v=VIDEO_ID`
  - `https://youtu.be/VIDEO_ID`
  - `https://www.youtube.com/embed/VIDEO_ID`
  - `https://m.youtube.com/watch?v=VIDEO_ID`
  - Or just the video ID: `VIDEO_ID`

**Response:**
```json
{
  "success": [
    {
      "video_id": "VIDEO_ID_1",
      "video_url": "https://www.youtube.com/watch?v=VIDEO_ID_1",
      "transcript": "Full transcript text here...",
      "status": "success",
      "from_cache": false
    }
  ],
  "errors": [
    {
      "video_id": "VIDEO_ID_2",
      "video_url": "https://www.youtube.com/watch?v=VIDEO_ID_2",
      "error": "Error message",
      "status": "error"
    }
  ]
}
```

**Response Fields:**
- `from_cache`: `true` if transcript was retrieved from database (no re-processing)
- `from_cache`: `false` if video was newly processed

### Get Video Status

**Endpoint:** `GET /video/{video_id}`

Get the status and transcript of a specific video.

**Response:**
```json
{
  "video_id": "VIDEO_ID",
  "video_url": "https://www.youtube.com/watch?v=VIDEO_ID",
  "status": "success",
  "transcript": "Full transcript...",
  "error_message": null,
  "created_at": "2024-01-01 12:00:00",
  "updated_at": "2024-01-01 12:05:00"
}
```

### Example with cURL

**Using videos field (recommended - accepts both IDs and URLs):**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "Content-Type: application/json" \
  -d '{
    "videos": [
      "dQw4w9WgXcQ",
      "https://www.youtube.com/watch?v=VIDEO_ID_2",
      "https://youtu.be/VIDEO_ID_3"
    ],
    "deepgram_api_key": "your-api-key"
  }'
```

**Using video_ids (also accepts URLs):**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "Content-Type: application/json" \
  -d '{
    "video_ids": ["dQw4w9WgXcQ"],
    "deepgram_api_key": "your-api-key"
  }'
```

**Using video_urls:**
```bash
curl -X POST "http://localhost:8000/transcribe" \
  -H "Content-Type: application/json" \
  -d '{
    "video_urls": ["https://www.youtube.com/watch?v=dQw4w9WgXcQ"],
    "deepgram_api_key": "your-api-key"
  }'
```

**Get video status:**
```bash
curl "http://localhost:8000/video/dQw4w9WgXcQ"
```

### Example with Python

```python
import requests

url = "http://localhost:8000/transcribe"

# Using videos field (recommended - accepts both IDs and URLs)
payload = {
    "videos": [
        "dQw4w9WgXcQ",
        "https://www.youtube.com/watch?v=VIDEO_ID_2",
        "https://youtu.be/VIDEO_ID_3"
    ],
    "deepgram_api_key": "your-api-key"
}

# Or using separate fields
payload = {
    "video_ids": ["dQw4w9WgXcQ"],
    "video_urls": ["https://www.youtube.com/watch?v=VIDEO_ID_2"],
    "deepgram_api_key": "your-api-key"
}

response = requests.post(url, json=payload)
result = response.json()

# Check cached vs new transcripts
for item in result["success"]:
    if item["from_cache"]:
        print(f"Video {item['video_id']} - Retrieved from cache")
    else:
        print(f"Video {item['video_id']} - Newly processed")
```

## Behavior

### Successful Processing
1. Video is checked in database
2. If transcript exists → Return cached transcript (no download/transcription)
3. If not found → Download audio → Transcribe → Store in database → **Delete audio file**
4. Return transcript

### Failed Processing
1. Video is checked in database
2. If status is `failed` → Return error (no re-download)
3. If processing fails → Store failure status → **Keep audio file** for potential retry
4. Return error

### Status Tracking
- **`processing`**: Video is being processed
- **`success`**: Transcript successfully generated and stored
- **`failed`**: Processing failed (audio file may be retained)

## Admin Dashboard

Access the admin dashboard at `http://localhost:8001` (or your configured port).

**Features:**
- View all processed videos with their status
- Search and filter videos
- View full transcripts
- Monitor statistics (total, success, failed, processing)
- Real-time updates (auto-refreshes every 30 seconds)

**Login:**
- Default username: `admin`
- Default password: `admin`

## Environment Variables

The service uses a `.env` file for configuration. Create a `.env` file in the project root:

```bash
# Copy the example file
cp .env.example .env

# Edit .env and configure your settings
```

**Example `.env` file:**
```bash
# Deepgram API Key
DEEPGRAM_API_KEY=your-deepgram-api-key-here

# Default Admin User Credentials
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin
```

**Environment Variables:**
- `DEEPGRAM_API_KEY`: Deepgram API key (required) - Get from https://console.deepgram.com/
- `ADMIN_USERNAME`: Default admin username (default: `admin`)
- `ADMIN_PASSWORD`: Default admin password (default: `admin`)

**Database Configuration:**
- `DB_TYPE`: Database type - `sqlite` (default) or `postgres`

**For SQLite (default):**
- `SQLITE_PATH`: Path to SQLite database file (default: `youtube_transcriptions.db`)

**For PostgreSQL:**
- `POSTGRES_HOST`: PostgreSQL host (default: `localhost`)
- `POSTGRES_PORT`: PostgreSQL port (default: `5432`)
- `POSTGRES_DB`: Database name (default: `youtube_transcriptions`)
- `POSTGRES_USER`: PostgreSQL username (default: `postgres`)
- `POSTGRES_PASSWORD`: PostgreSQL password (default: `postgres`)

**Note:** 
- The `.env` file is automatically loaded when the application starts
- For Docker, the `.env` file is automatically loaded via `docker-compose.yml`
- You can still provide the API key in the request body as an alternative
- **Important**: Change the default admin password in production!
- The default admin user is created automatically on first run using these credentials
- The database type is determined by `DB_TYPE` environment variable

## Notes

- Audio files are **only deleted after successful transcription**
- Failed attempts keep audio files for potential retry
- Transcripts are cached in database to avoid re-processing
- Failed videos are tracked to prevent unnecessary re-downloads
- The service uses Deepgram's `nova-2` model with smart formatting enabled
- Currently configured for English language transcription (can be modified in code)
- Database file (`youtube_transcriptions.db`) is created automatically
