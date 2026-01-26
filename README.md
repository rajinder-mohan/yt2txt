# YouTube Audio Transcription & AI Content Generation Service

A comprehensive FastAPI service for downloading YouTube videos, transcribing audio, managing AI prompts, and generating content using OpenAI GPT models. Features a full admin dashboard, bulk operations, and robust database storage.

## 🚀 Features

### Core Functionality
- **Video Transcription**: Download audio from YouTube videos and transcribe using Deepgram API
- **Channel Processing**: Extract all videos from YouTube channels with automatic pagination
- **Metadata Extraction**: Capture complete video metadata (title, channel, duration, views, upload date, etc.)
- **Smart Caching**: Avoids re-processing already transcribed videos
- **Rate Limiting Protection**: Handles YouTube bot detection and rate limits gracefully

### AI Integration
- **OpenAI GPT Integration**: Generate content using GPT-3.5, GPT-4, and other models
- **Prompt Management**: Store and reuse AI prompts with variable templates
- **Bulk Content Generation**: Generate AI content for multiple videos simultaneously
- **Content Storage**: Store multiple AI-generated content items per video (1 → many relationship)

### Admin Dashboard
- **Web-based UI**: Complete admin dashboard for all operations
- **Video Management**: View, search, and filter all videos
- **Transcript Viewing**: Browse and view transcripts with full-text search
- **Bulk Operations**: Select multiple videos and perform batch operations
- **Prompt Management**: Create, edit, and manage AI prompts
- **User Management**: Create and manage admin users
- **Settings Configuration**: Configure cookies, webhooks, and more

### Database & Storage
- **Dual Database Support**: SQLite (default) or PostgreSQL
- **Unlimited Text Storage**: All large fields (transcripts, prompts, content) use TEXT type
- **Metadata Storage**: Complete video metadata stored in structured and JSON format
- **Content Relationships**: One video can have many generated content items

### API Features
- **RESTful API**: Complete REST API with automatic Swagger documentation
- **Authentication**: Basic Auth and Bearer token support
- **Advanced Filtering**: Filter videos by status, channel, date range, search terms
- **Pagination**: Support for large datasets
- **Bulk Endpoints**: Process multiple videos in single requests

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [API Documentation](#api-documentation)
- [Database Setup](#database-setup)
- [Environment Variables](#environment-variables)
- [Features Guide](#features-guide)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)

## 🔧 Prerequisites

- **Python 3.8+** (or Docker)
- **FFmpeg** (for audio conversion)
  ```bash
  # Ubuntu/Debian
  sudo apt-get install ffmpeg
  
  # macOS
  brew install ffmpeg
  
  # Windows
  # Download from https://ffmpeg.org/download.html
  ```

- **API Keys** (required):
  - **Deepgram API Key**: Get from [Deepgram Console](https://console.deepgram.com/)
  - **OpenAI API Key** (optional, for AI features): Get from [OpenAI Platform](https://platform.openai.com/)

- **PostgreSQL** (optional, if not using SQLite):
  - PostgreSQL 12+ installed and running

## 📦 Installation

### Option 1: Docker (Recommended)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/youtube-script.git
   cd youtube-script
   ```

2. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and add your API keys
   ```

3. **Build and run:**
   ```bash
   docker-compose up -d
   ```

4. **Access the service:**
   - Admin Dashboard: http://localhost:8001
   - API Docs: http://localhost:8001/docs
   - Health Check: http://localhost:8001/health

### Option 2: Local Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/youtube-script.git
   cd youtube-script
   ```

2. **Create virtual environment (recommended):**
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   cp .env.example .env
   # Edit .env and configure your settings
   ```

5. **Run the service:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8001
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file in the project root with the following variables:

```bash
# ============================================
# Required API Keys
# ============================================

# Deepgram API Key (Required for transcription)
DEEPGRAM_API_KEY=your-deepgram-api-key-here

# OpenAI API Key (Required for AI content generation)
OPENAI_API_KEY=your-openai-api-key-here

# ============================================
# Database Configuration
# ============================================

# Database Type: 'sqlite' (default) or 'postgres'
DB_TYPE=sqlite

# SQLite Configuration (if DB_TYPE=sqlite)
SQLITE_PATH=youtube_transcriptions.db

# PostgreSQL Configuration (if DB_TYPE=postgres)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=youtube_transcriptions
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres

# ============================================
# YouTube Configuration
# ============================================

# YouTube Cookies (Optional but Recommended)
# Helps bypass bot detection. Get cookies from browser and paste here.
# Format: "name1=value1; name2=value2; ..."
# See "Getting YouTube Cookies" section below
YOUTUBE_COOKIES=

# Alternative: Path to cookies file (Netscape format)
# YOUTUBE_COOKIES_FILE=/path/to/cookies.txt

# Alternative: Extract cookies from browser
# YOUTUBE_COOKIES_BROWSER=chrome

# Rate Limiting: Delay between YouTube requests (seconds)
YOUTUBE_SLEEP_INTERVAL=2.0

# ============================================
# Server Configuration
# ============================================

# Server Port (default: 8001)
PORT=8001
```

### Getting YouTube Cookies

YouTube cookies are **highly recommended** to avoid bot detection errors. Here's how to get them:

1. **Open YouTube in your browser** (logged in)
2. **Open Developer Tools** (F12 or Right-click → Inspect)
3. **Go to Network tab**
4. **Visit any YouTube page** (e.g., https://www.youtube.com/@channelname)
5. **Find a request to `youtube.com`** in the network list
6. **Click on the request** → Go to **Headers** tab
7. **Scroll down** to find the **`cookie:`** header
8. **Copy the entire cookie value** (everything after "cookie: ")
9. **Paste it in `.env`** as `YOUTUBE_COOKIES=...`

**Example:**
```
YOUTUBE_COOKIES="VISITOR_INFO1_LIVE=abc123; YSC=xyz789; PREF=..."
```

## 🗄️ Database Setup

### SQLite (Default)

SQLite is used by default and requires no setup. The database file is created automatically at `youtube_transcriptions.db`.

**Advantages:**
- No installation required
- Perfect for development and small deployments
- Single file database

### PostgreSQL (Production)

For production or multi-user environments, use PostgreSQL:

1. **Install PostgreSQL:**
   ```bash
   # Ubuntu/Debian
   sudo apt-get install postgresql postgresql-contrib
   
   # macOS
   brew install postgresql
   ```

2. **Create database:**
   ```bash
   sudo -u postgres psql
   CREATE DATABASE youtube_transcriptions;
   CREATE USER your_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE youtube_transcriptions TO your_user;
   \q
   ```

3. **Update `.env`:**
   ```bash
   DB_TYPE=postgres
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=youtube_transcriptions
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   ```

4. **Install PostgreSQL driver:**
   ```bash
   pip install psycopg2-binary
   ```

The database schema is created automatically on first run.

## 🎯 Usage

### Admin Dashboard

1. **Access the dashboard:**
   - Navigate to http://localhost:8001
   - Login with admin credentials (create first user via API or dashboard)

2. **Features:**
   - **Videos Tab**: View all videos, filter by status/channel, bulk operations
   - **Transcripts Tab**: Browse processed videos with transcripts
   - **Process Channel Tab**: Extract videos from YouTube channels
   - **AI Processing Tab**: Generate content using OpenAI GPT
   - **Prompts Tab**: Manage AI prompt templates
   - **User Management Tab**: Create and manage admin users
   - **Settings Tab**: Configure cookies, webhooks, and settings

### API Usage

#### 1. Transcribe Videos

**Endpoint:** `POST /transcribe`

```bash
curl -X POST "http://localhost:8001/transcribe" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <base64(username:password)>" \
  -d '{
    "videos": [
      "dQw4w9WgXcQ",
      "https://www.youtube.com/watch?v=VIDEO_ID_2"
    ],
    "deepgram_api_key": "your-key"  # Optional if set in .env
  }'
```

**Response:**
```json
{
  "success": [
    {
      "video_id": "dQw4w9WgXcQ",
      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "transcript": "Full transcript text...",
      "status": "success",
      "from_cache": false
    }
  ],
  "errors": []
}
```

#### 2. Get Videos with Filters

**Endpoint:** `GET /api/videos`

```bash
curl -X GET "http://localhost:8001/api/videos?status=processed&channel=ChannelName&limit=10" \
  -H "Authorization: Basic <base64(username:password)>"
```

**Query Parameters:**
- `status`: Filter by status (pending, processing, processed, failed, rate_limited)
- `channel`: Filter by exact channel name
- `search`: Search in video_id, title, or channel_name
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `limit`: Maximum results
- `offset`: Pagination offset

#### 3. Extract Channel Videos

**Endpoint:** `POST /channel/videos`

```bash
curl -X POST "http://localhost:8001/channel/videos" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <base64(username:password)>" \
  -d '{
    "channel_url": "https://www.youtube.com/@channelname",
    "max_results": 50
  }'
```

#### 4. Generate AI Content

**Endpoint:** `POST /api/ai/process`

```bash
curl -X POST "http://localhost:8001/api/ai/process" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <base64(username:password)>" \
  -d '{
    "prompt": "Summarize the following transcript: {transcript}",
    "prompt_variables": {
      "transcript": "Video transcript here..."
    },
    "model": "gpt-3.5-turbo",
    "temperature": 0.7,
    "max_tokens": 1000
  }'
```

#### 5. Bulk Operations

**Bulk Transcribe:**
```bash
curl -X POST "http://localhost:8001/api/bulk/transcribe" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <base64(username:password)>" \
  -d '{
    "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2", "VIDEO_ID_3"]
  }'
```

**Bulk Generate Content:**
```bash
curl -X POST "http://localhost:8001/api/bulk/generate-content" \
  -H "Content-Type: application/json" \
  -H "Authorization: Basic <base64(username:password)>" \
  -d '{
    "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2"],
    "prompt_id": 1,
    "model": "gpt-3.5-turbo"
  }'
```

### Python Example

```python
import requests
from requests.auth import HTTPBasicAuth

# Base URL
BASE_URL = "http://localhost:8001"

# Authentication
auth = HTTPBasicAuth("admin", "admin")

# 1. Transcribe a video
response = requests.post(
    f"{BASE_URL}/transcribe",
    json={
        "videos": ["dQw4w9WgXcQ"],
        "deepgram_api_key": "your-key"
    },
    auth=auth
)
result = response.json()
print(f"Transcript: {result['success'][0]['transcript']}")

# 2. Get videos with filters
response = requests.get(
    f"{BASE_URL}/api/videos",
    params={"status": "processed", "limit": 10},
    auth=auth
)
videos = response.json()
print(f"Found {videos['total']} videos")

# 3. Generate AI content
response = requests.post(
    f"{BASE_URL}/api/ai/process",
    json={
        "prompt": "Summarize: {transcript}",
        "prompt_variables": {"transcript": "Video transcript..."},
        "model": "gpt-3.5-turbo"
    },
    auth=auth
)
content = response.json()
print(f"Generated: {content['response']}")
```

## 📚 API Documentation

### Interactive API Docs

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

All endpoints include detailed descriptions, parameters, request/response examples, and use cases.

### Main Endpoints

#### Video Operations
- `POST /transcribe` - Transcribe YouTube videos
- `GET /video/{video_id}` - Get video information and transcript
- `POST /channel/videos` - Extract videos from YouTube channel
- `GET /channel/videos` - Extract videos (GET method)

#### Video Management
- `GET /api/videos` - Get videos with advanced filtering
- `GET /api/admin/videos` - Get all videos (admin)
- `GET /api/admin/stats` - Get video statistics
- `POST /api/channel/process` - Process entire channel

#### Transcripts
- `GET /api/transcripts` - Get transcripts with filtering

#### AI Processing
- `POST /api/ai/process` - Process prompt with OpenAI GPT

#### Prompt Management
- `GET /api/prompts` - List all prompts
- `GET /api/prompts/{id}` - Get prompt by ID
- `POST /api/prompts` - Create new prompt
- `PUT /api/prompts/{id}` - Update prompt
- `DELETE /api/prompts/{id}` - Delete prompt

#### Bulk Operations
- `POST /api/bulk/transcribe` - Bulk transcribe videos
- `POST /api/bulk/generate-content` - Bulk generate AI content
- `POST /api/bulk/get-data` - Bulk get video data

#### Generated Content
- `GET /api/videos/{video_id}/generated-content` - Get all content for video
- `GET /api/generated-content/{id}` - Get content by ID
- `GET /api/generated-content` - List all generated content
- `DELETE /api/generated-content/{id}` - Delete generated content

#### User Management
- `GET /api/admin/users` - List all users
- `POST /api/admin/users` - Create user
- `DELETE /api/admin/users/{username}` - Delete user

#### Settings
- `GET /api/admin/settings/{key}` - Get setting
- `POST /api/admin/settings/{key}` - Set setting
- `GET /api/admin/cookies` - Get YouTube cookies
- `POST /api/admin/cookies` - Set YouTube cookies
- `DELETE /api/admin/cookies` - Delete cookies

#### Utilities
- `POST /api/extract-video-ids` - Extract video IDs from HTML
- `GET /health` - Health check

#### Authentication
- `POST /api/login` - Admin login
- `POST /api/logout` - Logout
- `POST /api/change-password` - Change password

## 🔐 Authentication

All API endpoints require authentication. Two methods are supported:

### 1. Basic Authentication (Recommended for API)

```bash
curl -X GET "http://localhost:8001/api/videos" \
  -u "username:password"
```

Or in Python:
```python
import requests
requests.get("http://localhost:8001/api/videos", auth=("username", "password"))
```

### 2. Bearer Token (For Dashboard Sessions)

1. **Login to get token:**
   ```bash
   curl -X POST "http://localhost:8001/api/login" \
     -H "Content-Type: application/json" \
     -d '{"username": "admin", "password": "admin"}'
   ```

2. **Use token in requests:**
   ```bash
   curl -X GET "http://localhost:8001/api/videos" \
     -H "Authorization: Bearer <token>"
   ```

## 🎨 Features Guide

### Bulk Video Operations

1. **Select Videos:**
   - Go to Videos tab
   - Check boxes next to videos you want to process
   - Use "Select All" checkbox for all videos

2. **Perform Actions:**
   - **Get Data**: Retrieve metadata for selected videos
   - **Transcribe**: Transcribe selected videos
   - **Generate Content**: Generate AI content for selected videos

### Prompt Management

1. **Create Prompt:**
   - Go to Prompts tab
   - Click "Create New Prompt"
   - Fill in:
     - Name (required)
     - Description (optional)
     - System Prompt (AI instructions)
     - User Prompt Template (with {variables})
     - Operation Type (category)

2. **Use Variables:**
   - In user prompt template, use `{variable_name}`
   - Available variables: `{video_id}`, `{video_title}`, `{channel_name}`, `{transcript}`, `{duration}`, `{view_count}`
   - Variables are automatically replaced when using the prompt

3. **Example Prompt:**
   ```
   System Prompt: "You are a helpful assistant that summarizes video content."
   
   User Template: "Summarize this video transcript:\n\nTitle: {video_title}\nChannel: {channel_name}\nTranscript: {transcript}"
   ```

### AI Content Generation

1. **Using Saved Prompt:**
   - Go to AI Processing tab
   - Select a saved prompt from dropdown
   - Click "Process with AI"

2. **Using Custom Prompt:**
   - Enter custom prompt in text area
   - Optionally save it for later use
   - Click "Process with AI"

3. **View Generated Content:**
   - Go to Videos tab
   - Click "View Content" button for any video
   - See all generated content items for that video
   - Delete individual content items if needed

### Channel Processing

1. **Extract Videos:**
   - Go to Process Channel tab
   - Enter YouTube channel URL
   - Click "Submit Channel"
   - Videos are stored with "pending" status

2. **Process Extracted Videos:**
   - Use bulk operations to transcribe pending videos
   - Or use `/api/channel/process` endpoint for automatic processing

3. **HTML Extraction (Alternative):**
   - If channel API doesn't work, use HTML extraction
   - Paste HTML from YouTube page
   - Extract video IDs
   - Process extracted videos

## 🗃️ Database Schema

### Tables

#### `video_transcriptions`
Stores video information and transcripts.

**Fields:**
- `id` - Primary key
- `video_id` - YouTube video ID (unique)
- `video_url` - Original URL
- `status` - Processing status (pending, processing, processed, failed, rate_limited)
- `transcript` - Full transcript text (TEXT, unlimited size)
- `title` - Video title
- `duration` - Video duration in seconds
- `view_count` - Number of views
- `upload_date` - Upload date
- `channel_name` - Channel/author name
- `channel_id` - Channel ID
- `metadata` - Complete metadata as JSON
- `error_message` - Error details if failed
- `created_at` / `updated_at` - Timestamps

#### `prompts`
Stores AI prompt templates.

**Fields:**
- `id` - Primary key
- `name` - Prompt name
- `description` - Description
- `system_prompt` - System prompt (TEXT, unlimited)
- `user_prompt_template` - User template with variables (TEXT, unlimited)
- `operation_type` - Category (e.g., 'summarize', 'extract_keywords')
- `created_at` / `updated_at` - Timestamps

#### `generated_content`
Stores AI-generated content (1 video → many content items).

**Fields:**
- `id` - Primary key
- `video_id` - Foreign key to video_transcriptions
- `prompt_id` - Foreign key to prompts (optional)
- `prompt_text` - Prompt used (TEXT, unlimited)
- `model` - OpenAI model used
- `temperature` - Temperature setting
- `max_tokens` - Max tokens setting
- `generated_text` - Generated content (TEXT, unlimited)
- `usage_info` - Token usage statistics (JSON)
- `created_at` - Timestamp

#### `admin_users`
Stores admin user accounts.

**Fields:**
- `id` - Primary key
- `username` - Username (unique)
- `password_hash` - Hashed password
- `created_at` - Timestamp

#### `settings`
Stores key-value settings.

**Fields:**
- `id` - Primary key
- `setting_key` - Setting name (unique)
- `setting_value` - Setting value (TEXT)
- `updated_at` - Timestamp

## 🐛 Troubleshooting

### Common Issues

#### 1. "Sign in to confirm you're not a bot" Error

**Problem:** YouTube is blocking requests.

**Solution:**
- Configure YouTube cookies (see "Getting YouTube Cookies" section)
- Add cookies to `.env` file or via admin dashboard
- Ensure cookies are from a logged-in YouTube session

#### 2. Rate Limiting Errors

**Problem:** "The current session has been rate-limited by YouTube"

**Solution:**
- Increase `YOUTUBE_SLEEP_INTERVAL` in `.env` (default: 2 seconds)
- Wait before retrying (rate limits typically last 1 hour)
- Use cookies to reduce rate limiting
- Videos marked as `rate_limited` will be retried on next run

#### 3. Database Connection Errors (PostgreSQL)

**Problem:** Cannot connect to PostgreSQL

**Solution:**
- Verify PostgreSQL is running: `sudo systemctl status postgresql`
- Check connection settings in `.env`
- Ensure database and user exist
- For Docker, use `network_mode: host` in docker-compose.yml

#### 4. FFmpeg Not Found

**Problem:** "ffmpeg: command not found"

**Solution:**
- Install FFmpeg (see Prerequisites)
- For Docker, FFmpeg is included in the image
- Verify installation: `ffmpeg -version`

#### 5. API Key Errors

**Problem:** "API key is required"

**Solution:**
- Set `DEEPGRAM_API_KEY` in `.env` file
- Or provide API key in request body
- For OpenAI features, set `OPENAI_API_KEY` in `.env`

#### 6. Port Already in Use

**Problem:** "Address already in use"

**Solution:**
- Change port in `.env`: `PORT=8002`
- Or stop the service using port 8001
- Update docker-compose.yml if using Docker

## 📝 Development

### Project Structure

```
youtube-script/
├── main.py                 # FastAPI application and endpoints
├── database.py             # Database operations and schema
├── auth.py                 # Authentication and session management
├── download_audio.py       # Audio download utilities (if separate)
├── email_service.py        # Email sending functionality
├── requirements.txt        # Python dependencies
├── Dockerfile              # Docker image definition
├── docker-compose.yml      # Docker Compose configuration
├── static/                 # Frontend files
│   ├── admin.html         # Admin dashboard HTML
│   ├── admin.js           # Frontend JavaScript
│   └── admin.css          # Styles
└── README.md              # This file
```

### Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio httpx

# Run tests (if available)
pytest
```

### Code Style

The project follows PEP 8 Python style guidelines. Consider using:
- `black` for code formatting
- `flake8` for linting
- `mypy` for type checking

## 🤝 Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the repository**
2. **Create a feature branch:** `git checkout -b feature/amazing-feature`
3. **Make your changes**
4. **Test thoroughly**
5. **Commit your changes:** `git commit -m 'Add amazing feature'`
6. **Push to the branch:** `git push origin feature/amazing-feature`
7. **Open a Pull Request**

### Development Setup

1. Clone your fork
2. Create virtual environment
3. Install dependencies: `pip install -r requirements.txt`
4. Create `.env` file with your API keys
5. Run locally: `uvicorn main:app --reload`

## 📄 License

This project is open source. Please check the LICENSE file for details.

## 🆘 Support

- **Issues**: Report bugs or request features on GitHub Issues
- **Documentation**: Check `/docs` endpoint for interactive API documentation
- **Email**: [Your email if applicable]

## 🙏 Acknowledgments

- [FastAPI](https://fastapi.tiangolo.com/) - Modern web framework
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - YouTube video downloader
- [Deepgram](https://www.deepgram.com/) - Speech-to-text API
- [OpenAI](https://openai.com/) - GPT models for content generation

## 📊 Status

- ✅ Video transcription
- ✅ Channel processing
- ✅ AI content generation
- ✅ Prompt management
- ✅ Bulk operations
- ✅ Admin dashboard
- ✅ Database storage
- ✅ API documentation

---

**Made with ❤️ for the open source community**
