# Usage Guide

## Admin Dashboard

### Accessing the Dashboard

1. **Start the service** (see [Installation Guide](installation.md))
2. **Navigate to:** http://localhost:8001
3. **Login** with admin credentials (create first user via API or dashboard)

### Dashboard Features

#### Videos Tab
- **View all videos** with complete metadata
- **Filter by status** (pending, processing, processed, failed, rate_limited)
- **Filter by channel** using dropdown
- **Search** videos by ID, title, or channel name
- **Bulk operations**: Select multiple videos and perform batch actions
- **View transcripts**: Click on transcript preview to see full text
- **View generated content**: Click "View Content" to see AI-generated content

#### Transcripts Tab
- Browse all processed videos with transcripts
- Filter and search transcripts
- View full transcript text

#### Process Channel Tab
- **Extract videos** from YouTube channels
- Enter channel URL (supports various formats)
- Videos are stored with "pending" status
- Use bulk operations to transcribe extracted videos

#### AI Processing Tab
- **Generate content** using OpenAI GPT models
- **Select saved prompts** from dropdown
- **Use custom prompts** or create new ones
- **View generated content** with usage statistics

#### Prompts Tab
- **Create prompts** with system and user templates
- **Edit existing prompts**
- **Delete prompts**
- **Use variables** in templates (e.g., `{video_title}`, `{transcript}`)

#### User Management Tab
- **Create admin users**
- **Delete users**
- **Manage user accounts**

#### Settings Tab
- **Configure YouTube cookies** (essential for avoiding bot detection)
- **Set n8n webhook URL** (if using n8n integration)
- **Manage system settings**

## API Usage

### Authentication

All API endpoints require authentication. Two methods are supported:

#### 1. Basic Authentication (Recommended for API)

```bash
curl -X GET "http://localhost:8001/api/videos" \
  -u "username:password"
```

Or in Python:
```python
import requests
requests.get("http://localhost:8001/api/videos", auth=("username", "password"))
```

#### 2. Bearer Token (For Dashboard Sessions)

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

### Common API Operations

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
    "deepgram_api_key": "your-key"
  }'
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

## Python Examples

### Basic Usage

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

## Feature Guides

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

## Related Documentation

- [API Documentation](api.md) - Complete API reference
- [Installation Guide](installation.md) - Setup instructions
- [Configuration Guide](configuration.md) - Environment setup
