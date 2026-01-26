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

# Rate Limiting: Delay between YouTube requests (seconds)
YOUTUBE_SLEEP_INTERVAL=2.0

# Proxy Configuration (Optional)
# Proxy URL for yt-dlp requests (useful for Bright Data, etc.)
# Format: http://USERNAME:PASSWORD@proxy.example.com:PORT
# Example: http://brd-customer-USERNAME:PASSWORD@brd.superproxy.io:33335
YTDLP_PROXY=

# ============================================
# Server Configuration
# ============================================

# Server Port (default: 8001)
PORT=8001
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

## Proxy Configuration

If you're using a proxy service (like Bright Data), you can configure it in two ways:

### 1. Environment Variable (Recommended for Docker)

Add to your `.env` file:
```bash
YTDLP_PROXY=http://USERNAME:PASSWORD@brd.superproxy.io:33335
```

### 2. Dashboard Settings (Recommended for UI)

1. Go to **Settings** tab in the admin dashboard
2. Scroll to **Proxy Configuration** section
3. Enter your proxy URL
4. Click **Save Proxy**
5. Optionally click **Test Proxy** to verify it works

**Proxy Format Examples:**
- `http://username:password@proxy.example.com:8080`
- `https://username:password@proxy.example.com:8080`
- `socks5://username:password@proxy.example.com:1080`

**Note:** For Bright Data or similar services that require certificates:
1. Place the certificate file in `certs/brightdata-33335.crt`
2. The Dockerfile will automatically install it
3. Or mount it in docker-compose.yml

## Configuration Tips

- **API Keys**: Can be provided in `.env` file or in request body (for testing)
- **Proxy**: Useful for bypassing geo-restrictions or using proxy services
- **Rate Limiting**: Increase `YOUTUBE_SLEEP_INTERVAL` if you encounter rate limits
- **Database**: SQLite is fine for development, PostgreSQL recommended for production

## Related Documentation

- [Database Setup](database.md) - Detailed database configuration
- [Troubleshooting](troubleshooting.md) - Common configuration issues
