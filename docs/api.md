# API Documentation

## Interactive API Docs

Once the service is running, access the interactive API documentation:

- **Swagger UI**: http://localhost:8001/docs
- **ReDoc**: http://localhost:8001/redoc

All endpoints include detailed descriptions, parameters, request/response examples, and use cases.

## Authentication

All API endpoints require authentication. See [Usage Guide - Authentication](usage.md#authentication) for details.

## Main Endpoints

### Video Operations

#### `POST /transcribe`
Transcribe YouTube videos using Deepgram API.

**Request:**
```json
{
  "videos": ["dQw4w9WgXcQ", "https://www.youtube.com/watch?v=VIDEO_ID"],
  "deepgram_api_key": "your-key"
}
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

#### `GET /video/{video_id}`
Get video information and transcript by video ID or URL.

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "status": "processed",
  "transcript": "Full transcript...",
  "title": "Video Title",
  "channel_name": "Channel Name",
  "duration": 180,
  "view_count": 1000000,
  "upload_date": "2024-01-01",
  "metadata": {...}
}
```

#### `POST /channel/videos`
Extract videos from YouTube channel.

**Request:**
```json
{
  "channel_url": "https://www.youtube.com/@channelname",
  "max_results": 50
}
```

#### `GET /channel/videos`
Extract videos from channel (GET method with query parameters).

### Video Management

#### `GET /api/videos`
Get videos with advanced filtering.

**Query Parameters:**
- `status`: Filter by status (pending, processing, processed, failed, rate_limited)
- `channel`: Filter by exact channel name
- `search`: Search in video_id, title, or channel_name
- `date_from`: Filter from date (YYYY-MM-DD)
- `date_to`: Filter to date (YYYY-MM-DD)
- `limit`: Maximum results
- `offset`: Pagination offset

#### `GET /api/admin/videos`
Get all videos (admin endpoint, no filters).

#### `GET /api/admin/stats`
Get video statistics.

**Response:**
```json
{
  "total": 100,
  "success": 80,
  "failed": 10,
  "processing": 5,
  "pending": 5,
  "rate_limited": 0
}
```

#### `POST /api/channel/process`
Process entire channel: extract videos and transcribe automatically.

### Transcripts

#### `GET /api/transcripts`
Get transcripts with filtering (only processed videos).

**Query Parameters:** Same as `/api/videos`

### AI Processing

#### `POST /api/ai/process`
Process prompt with OpenAI GPT models.

**Request:**
```json
{
  "prompt": "Summarize: {transcript}",
  "prompt_variables": {
    "transcript": "Video transcript..."
  },
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000,
  "openai_api_key": "your-key"
}
```

**Response:**
```json
{
  "response": "Generated content...",
  "usage": {
    "prompt_tokens": 100,
    "completion_tokens": 200,
    "total_tokens": 300
  },
  "error": null
}
```

### Prompt Management

#### `GET /api/prompts`
List all prompts, optionally filtered by operation_type.

#### `GET /api/prompts/{id}`
Get prompt by ID.

#### `POST /api/prompts`
Create new prompt.

**Request:**
```json
{
  "name": "Summarize Video",
  "description": "Summarizes video transcripts",
  "system_prompt": "You are a helpful assistant.",
  "user_prompt_template": "Summarize: {transcript}",
  "operation_type": "summarize"
}
```

#### `PUT /api/prompts/{id}`
Update existing prompt.

#### `DELETE /api/prompts/{id}`
Delete prompt.

### Bulk Operations

#### `POST /api/bulk/transcribe`
Bulk transcribe multiple videos.

**Request:**
```json
{
  "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "deepgram_api_key": "your-key"
}
```

#### `POST /api/bulk/generate-content`
Bulk generate AI content for multiple videos.

**Request:**
```json
{
  "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "prompt_id": 1,
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000
}
```

#### `POST /api/bulk/get-data`
Bulk get data for multiple videos.

**Request:**
```json
["VIDEO_ID_1", "VIDEO_ID_2", "VIDEO_ID_3"]
```

### Generated Content

#### `GET /api/videos/{video_id}/generated-content`
Get all generated content for a specific video.

#### `GET /api/generated-content/{id}`
Get generated content by ID.

#### `GET /api/generated-content`
List all generated content with pagination.

#### `DELETE /api/generated-content/{id}`
Delete generated content.

### User Management

#### `GET /api/admin/users`
List all admin users.

#### `POST /api/admin/users`
Create new admin user.

**Request:**
```json
{
  "username": "newuser",
  "password": "securepassword"
}
```

#### `DELETE /api/admin/users/{username}`
Delete admin user.

### Settings

#### `GET /api/admin/settings/{key}`
Get setting value.

#### `POST /api/admin/settings/{key}`
Set setting value.

**Request:**
```json
{
  "value": "setting_value"
}
```

#### `GET /api/admin/cookies`
Get YouTube cookies.

#### `POST /api/admin/cookies`
Set YouTube cookies.

**Request:**
```json
{
  "cookies": "name1=value1; name2=value2; ..."
}
```

#### `DELETE /api/admin/cookies`
Delete YouTube cookies.

### Utilities

#### `POST /api/extract-video-ids`
Extract video IDs from HTML content.

**Request:**
```json
{
  "html": "<html>...YouTube page HTML...</html>"
}
```

**Response:**
```json
{
  "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "count": 2
}
```

#### `GET /health`
Health check endpoint.

**Response:**
```json
{
  "status": "healthy"
}
```

### Authentication

#### `POST /api/login`
Admin login.

**Request:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "token": "bearer_token_here",
  "username": "admin"
}
```

#### `POST /api/logout`
Logout (invalidate session token).

#### `POST /api/change-password`
Change password for authenticated user.

**Request:**
```json
{
  "current_password": "oldpassword",
  "new_password": "newpassword"
}
```

## Response Codes

- `200` - Success
- `201` - Created
- `400` - Bad Request (invalid parameters)
- `401` - Unauthorized (authentication required)
- `404` - Not Found
- `500` - Internal Server Error

## Rate Limiting

The service includes built-in rate limiting protection for YouTube requests:
- Configurable delay between requests (`YOUTUBE_SLEEP_INTERVAL`)
- Automatic detection of rate limit errors
- Videos marked as `rate_limited` for retry later

## Related Documentation

- [Usage Guide](usage.md) - API usage examples
- [Interactive Docs](http://localhost:8001/docs) - Full interactive documentation
