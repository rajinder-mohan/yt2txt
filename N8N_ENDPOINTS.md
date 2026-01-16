# n8n Integration Guide - API Endpoints & Payloads

## Default Admin Credentials

**Username:** `admin`  
**Password:** `admin`

> ⚠️ **Note:** These are the default credentials. Change them in production by updating the `.env` file.

---

## Base URL

Replace `YOUR_SERVER_URL` with your actual server URL:
- Local: `http://localhost:8001`
- Production: `https://your-domain.com`

---

## Authentication Methods

The API supports **two authentication methods**:

### Method 1: Basic Auth (Recommended for n8n) ⭐

**Simplest and most suitable for automation!**

Use Basic Authentication with your username and password.

**n8n Configuration:**
- Authentication Type: **Basic Auth**
- Username: `admin` (or your username)
- Password: `admin` (or your password)

**No login required!** Just use Basic Auth in each request.

**Example with cURL:**
```bash
curl -u "username:password" "https://your-server.com/api/videos"
```

---

### Method 2: Bearer Token Authentication (Session-based)

**Endpoint:** `POST /api/login`

**Headers:**
```
Content-Type: application/json
```

**Payload:**
```json
{
  "username": "admin",
  "password": "admin"
}
```

**Response:**
```json
{
  "token": "your-auth-token-here",
  "username": "admin"
}
```

**n8n Configuration:**
- Method: `POST`
- URL: `{{ $env.SERVER_URL }}/api/login`
- Authentication: None
- Body Content Type: JSON
- Body: Use the JSON payload above

**Save the token** from the response to use in subsequent requests.

Then use `Authorization: Bearer <token>` header in subsequent requests.

---

## Endpoint 1: Process Channel (Complete Workflow) ⭐ RECOMMENDED

This endpoint does everything in one call: gets video IDs, transcribes all videos, and saves to DB.

**Endpoint:** `POST /api/channel/process`

**Headers (Choose ONE authentication method):**

**Option A: API Key (Recommended)**
```
Content-Type: application/json
Authorization: Basic base64(username:password)
```

**Option B: Bearer Token**
```
Content-Type: application/json
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Payload:**
```json
{
  "channel_url": "https://www.youtube.com/@channelname",
  "max_results": 50,
  "deepgram_api_key": "your-deepgram-api-key"
}
```

**Payload Fields:**
- `channel_url` (required): YouTube channel URL
  - Examples:
    - `https://www.youtube.com/@channelname`
    - `https://www.youtube.com/channel/CHANNEL_ID`
    - `https://www.youtube.com/c/channelname`
    - `https://www.youtube.com/user/username`
- `max_results` (optional): Maximum number of videos to process
- `deepgram_api_key` (optional): Deepgram API key (if not set in env)

**Response:**
```json
{
  "channel_url": "https://www.youtube.com/@channelname",
  "channel_name": "Channel Name",
  "total_videos": 50,
  "processed_videos": 50,
  "success_count": 45,
  "failed_count": 5,
  "message": "Processed 50 videos. 45 successful, 5 failed.",
  "video_results": [
    {
      "video_id": "dQw4w9WgXcQ",
      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "title": "Video Title",
      "status": "success",
      "transcript": "Full transcript text...",
      "error": null
    },
    {
      "video_id": "another_video_id",
      "video_url": "https://www.youtube.com/watch?v=another_video_id",
      "title": "Another Video",
      "status": "failed",
      "transcript": null,
      "error": "Error message here"
    }
  ]
}
```

**n8n Configuration (API Key Method - Recommended):**
- Method: `POST`
- URL: `{{ $env.SERVER_URL }}/api/channel/process`
- Authentication: **Header Auth** or **Generic Credential Type**
  - Authentication Type: **Basic Auth**
  - Username: `{{ $env.API_USERNAME }}` (set API_USERNAME in n8n environment variables)
  - Password: `{{ $env.API_PASSWORD }}` (set API_PASSWORD in n8n environment variables)
- Body Content Type: JSON
- Body: Use the JSON payload above

**n8n Configuration (Bearer Token Method):**
- Method: `POST`
- URL: `{{ $env.SERVER_URL }}/api/channel/process`
- Authentication: **Generic Credential Type**
  - Name: `Authorization`
  - Value: `Bearer {{ $json.token }}` (use token from login step)
- Body Content Type: JSON
- Body: Use the JSON payload above

---

## Endpoint 2: Get Video IDs from Channel (Step 1 - Get IDs Only)

Use this if you want to get video IDs first, then process them separately.

**Endpoint:** `POST /channel/videos`

**Headers:**
```
Content-Type: application/json
```

**Payload:**
```json
{
  "channel_url": "https://www.youtube.com/@channelname",
  "max_results": 50
}
```

**Response:**
```json
{
  "channel_url": "https://www.youtube.com/@channelname",
  "channel_name": "Channel Name",
  "total_videos": 50,
  "videos": [
    {
      "video_id": "dQw4w9WgXcQ",
      "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
      "title": "Video Title",
      "duration": 180,
      "view_count": 1000000,
      "upload_date": "2024-01-15"
    }
  ]
}
```

**n8n Configuration:**
- Method: `POST`
- URL: `{{ $env.SERVER_URL }}/channel/videos`
- Authentication: None
- Body Content Type: JSON
- Body: Use the JSON payload above

**Alternative GET Method:**
- Method: `GET`
- URL: `{{ $env.SERVER_URL }}/channel/videos?channel_url=https://www.youtube.com/@channelname&max_results=50`

---

## Endpoint 3: Transcribe Videos (Step 2 - Process Videos)

Use this after getting video IDs from Endpoint 2, or to transcribe individual videos.

**Endpoint:** `POST /transcribe`

**Headers:**
```
Content-Type: application/json
```

**Payload:**
```json
{
  "videos": [
    "dQw4w9WgXcQ",
    "https://www.youtube.com/watch?v=VIDEO_ID_2",
    "https://youtu.be/VIDEO_ID_3"
  ],
  "deepgram_api_key": "your-deepgram-api-key"
}
```

**Alternative Payload Formats:**
```json
{
  "video_ids": ["VIDEO_ID_1", "VIDEO_ID_2"],
  "deepgram_api_key": "your-deepgram-api-key"
}
```

```json
{
  "video_urls": [
    "https://www.youtube.com/watch?v=VIDEO_ID_1",
    "https://youtu.be/VIDEO_ID_2"
  ],
  "deepgram_api_key": "your-deepgram-api-key"
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
  "errors": [
    {
      "video_id": "failed_video_id",
      "video_url": "https://www.youtube.com/watch?v=failed_video_id",
      "error": "Error message",
      "status": "error"
    }
  ]
}
```

**n8n Configuration:**
- Method: `POST`
- URL: `{{ $env.SERVER_URL }}/transcribe`
- Authentication: None
- Body Content Type: JSON
- Body: Use the JSON payload above

---

## Endpoint 4: Get Video Status

Get the status and transcript of a specific video.

**Endpoint:** `GET /video/{video_id}`

**Headers:**
```
(none required)
```

**URL Examples:**
- `GET /video/dQw4w9WgXcQ`
- `GET /video/https://www.youtube.com/watch?v=dQw4w9WgXcQ`

**Response:**
```json
{
  "video_id": "dQw4w9WgXcQ",
  "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
  "status": "success",
  "transcript": "Full transcript text...",
  "error_message": null,
  "created_at": "2024-01-15T10:00:00",
  "updated_at": "2024-01-15T10:05:00"
}
```

**n8n Configuration:**
- Method: `GET`
- URL: `{{ $env.SERVER_URL }}/video/{{ $json.video_id }}`
- Authentication: None

---

## Endpoint 5: Change Password

Change the password for the authenticated user.

**Endpoint:** `POST /api/change-password`

**Headers (Choose ONE authentication method):**

**Option A: API Key (Recommended)**
```
Content-Type: application/json
Authorization: Basic base64(username:password)
```

**Option B: Bearer Token**
```
Content-Type: application/json
Authorization: Bearer YOUR_AUTH_TOKEN
```

**Payload (Bearer Token Method):**
```json
{
  "current_password": "old-password",
  "new_password": "new-secure-password"
}
```

**Payload (API Key Method - username required):**
```json
{
  "username": "admin",
  "current_password": "old-password",
  "new_password": "new-secure-password"
}
```

**Payload Fields:**
- `current_password` (required): Current password for verification
- `new_password` (required): New password (minimum 6 characters)
- `username` (optional): Required when using API key authentication, optional when using Bearer token

**Response:**
```json
{
  "message": "Password changed successfully. Please login again."
}
```

**n8n Configuration:**
- Method: `POST`
- URL: `{{ $env.SERVER_URL }}/api/change-password`
- Authentication: Basic Auth (username:password) or Bearer Token
- Body Content Type: JSON
- Body: Use the JSON payload above

**Note:** After password change, all sessions are invalidated and user must login again.

---

## Endpoint 6: Health Check

Check if the service is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy"
}
```

**n8n Configuration:**
- Method: `GET`
- URL: `{{ $env.SERVER_URL }}/health`
- Authentication: None

---

## Complete n8n Workflow Examples

### Workflow 1: Simple - Process Channel (One Step) - API Key Method ⭐

1. **Webhook** (or Manual Trigger)
   - Receives channel URL

2. **HTTP Request Node**
   - `POST /api/channel/process` with channel URL
   - Use **Basic Auth** with username and password
   - No login required!

3. **Done!** Results are saved to DB

### Workflow 1b: Simple - Process Channel (Bearer Token Method)

1. **Webhook** (or Manual Trigger)
   - Receives channel URL

2. **HTTP Request Node**
   - First call: `POST /api/login` to get token
   - Second call: `POST /api/channel/process` with channel URL
   - Uses token from first call in Authorization header

3. **Done!** Results are saved to DB

### Workflow 2: Step-by-Step (More Control)

1. **Webhook** (or Manual Trigger)
   - Receives channel URL

2. **HTTP Request Node**
   - `POST /channel/videos`
   - Gets list of video IDs

3. **Split In Batches Node**
   - Process videos in batches (optional)

4. **HTTP Request Node** (Loop)
   - `POST /transcribe`
   - Transcribe each video

5. **Optional: Add Email Node** (if you want email notifications)
   - Send custom email with results using n8n's email node

---

## n8n Environment Variables Setup

In n8n, set these environment variables:

```
SERVER_URL=http://localhost:8001
# or
SERVER_URL=https://your-production-domain.com

API_USERNAME=your-username
API_PASSWORD=your-password
DEEPGRAM_API_KEY=your-deepgram-api-key
```

Then use in nodes: `{{ $env.SERVER_URL }}` with Basic Auth using `{{ $env.API_USERNAME }}` and `{{ $env.API_PASSWORD }}`

**Important:** Use Basic Auth with your admin username and password for all API requests!

---

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid input)
- `401`: Unauthorized (invalid/missing auth token)
- `404`: Not Found (video/channel not found)
- `500`: Internal Server Error

Error responses follow this format:
```json
{
  "detail": "Error message here"
}
```

---

## Tips for n8n

1. **Store Auth Token**: After login, store the token in a variable or use it immediately in the next node
2. **Error Handling**: Add error handling nodes after HTTP requests
3. **Rate Limiting**: If processing many videos, add delays between requests
4. **Batch Processing**: Use "Split In Batches" node to process videos in smaller groups
5. **Webhook Response**: Return the processing results to the webhook caller

---

## Example n8n Workflow JSON

You can import this into n8n:

```json
{
  "name": "YouTube Channel Transcription",
  "nodes": [
    {
      "parameters": {},
      "name": "Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.SERVER_URL }}/api/login",
        "authentication": "none",
        "jsonBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "username",
              "value": "admin"
            },
            {
              "name": "password",
              "value": "admin"
            }
          ]
        }
      },
      "name": "Login",
      "type": "n8n-nodes-base.httpRequest",
      "position": [450, 300]
    },
    {
      "parameters": {
        "method": "POST",
        "url": "={{ $env.SERVER_URL }}/api/channel/process",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "Authorization",
              "value": "=Bearer {{ $json.token }}"
            }
          ]
        },
        "jsonBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "channel_url",
              "value": "={{ $json.channel_url }}"
            },
            {
              "name": "max_results",
              "value": "50"
            }
          ]
        }
      },
      "name": "Process Channel",
      "type": "n8n-nodes-base.httpRequest",
      "position": [650, 300]
    }
  ],
  "connections": {
    "Webhook": {
      "main": [[{"node": "Login", "type": "main", "index": 0}]]
    },
    "Login": {
      "main": [[{"node": "Process Channel", "type": "main", "index": 0}]]
    }
  }
}
```

---

## Support

For issues or questions, check the main README.md file or the API documentation at:
- Swagger UI: `http://YOUR_SERVER_URL/docs`
- ReDoc: `http://YOUR_SERVER_URL/redoc`
