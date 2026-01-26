# Configuration Guide

## Environment Variables

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

## Getting YouTube Cookies

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

## Email Configuration (Optional)

If you want to send email notifications:

```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_USE_TLS=true
```

**Note:** For Gmail, you'll need to use an [App Password](https://support.google.com/accounts/answer/185833) instead of your regular password.

## Configuration Tips

- **API Keys**: Can be provided in `.env` file or in request body (for testing)
- **Cookies**: Essential for avoiding YouTube bot detection
- **Rate Limiting**: Increase `YOUTUBE_SLEEP_INTERVAL` if you encounter rate limits
- **Database**: SQLite is fine for development, PostgreSQL recommended for production

## Related Documentation

- [Database Setup](database.md) - Detailed database configuration
- [Troubleshooting](troubleshooting.md) - Common configuration issues
