# Troubleshooting Guide

## Common Issues and Solutions

### 1. "Sign in to confirm you're not a bot" Error

**Problem:** YouTube is blocking requests with bot detection.

**Solution:**
1. Configure YouTube cookies (see [Configuration Guide](configuration.md#getting-youtube-cookies))
2. Add cookies to `.env` file or via admin dashboard
3. Ensure cookies are from a logged-in YouTube session
4. Cookies should be recent (not expired)

**Prevention:**
- Always configure cookies before processing videos
- Update cookies if they expire
- Use cookies from a browser where you're logged into YouTube

### 2. Rate Limiting Errors

**Problem:** "The current session has been rate-limited by YouTube"

**Symptoms:**
- Videos marked as `rate_limited` status
- Error messages mentioning rate limits
- Processing stops after encountering rate limit

**Solution:**
1. **Increase delay between requests:**
   ```bash
   # In .env file
   YOUTUBE_SLEEP_INTERVAL=5.0  # Increase from default 2.0
   ```

2. **Wait before retrying:**
   - Rate limits typically last 1 hour
   - Wait before processing more videos

3. **Use cookies:**
   - Cookies significantly reduce rate limiting
   - See [Configuration Guide](configuration.md#getting-youtube-cookies)

4. **Resume processing:**
   - Videos marked as `rate_limited` will be retried on next run
   - Processing automatically skips already processed videos

**Prevention:**
- Always use cookies
- Increase `YOUTUBE_SLEEP_INTERVAL` for large batches
- Process videos in smaller batches

### 3. Database Connection Errors (PostgreSQL)

**Problem:** Cannot connect to PostgreSQL database.

**Symptoms:**
- Error: "could not connect to server"
- Error: "authentication failed"
- Error: "database does not exist"

**Solution:**

1. **Verify PostgreSQL is running:**
   ```bash
   # Linux
   sudo systemctl status postgresql
   
   # macOS
   brew services list
   
   # Start if not running
   sudo systemctl start postgresql  # Linux
   brew services start postgresql   # macOS
   ```

2. **Check connection settings in `.env`:**
   ```bash
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   POSTGRES_DB=youtube_transcriptions
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   ```

3. **Verify database exists:**
   ```bash
   sudo -u postgres psql -l
   ```

4. **Test connection:**
   ```bash
   psql -h localhost -U your_user -d youtube_transcriptions
   ```

5. **For Docker:**
   - Use `network_mode: host` in docker-compose.yml
   - Or use service name as host (e.g., `POSTGRES_HOST=postgres`)

### 4. FFmpeg Not Found

**Problem:** "ffmpeg: command not found"

**Solution:**

**Linux (Ubuntu/Debian):**
```bash
sudo apt-get update
sudo apt-get install ffmpeg
```

**macOS:**
```bash
brew install ffmpeg
```

**Windows:**
1. Download from https://ffmpeg.org/download.html
2. Add to PATH environment variable

**Docker:**
- FFmpeg is included in the Docker image
- No additional setup needed

**Verify installation:**
```bash
ffmpeg -version
```

### 5. API Key Errors

**Problem:** "API key is required" or "Invalid API key"

**Solution:**

1. **Deepgram API Key:**
   - Set `DEEPGRAM_API_KEY` in `.env` file
   - Or provide in request body: `"deepgram_api_key": "your-key"`
   - Get key from: https://console.deepgram.com/

2. **OpenAI API Key:**
   - Set `OPENAI_API_KEY` in `.env` file
   - Or provide in request body: `"openai_api_key": "your-key"`
   - Get key from: https://platform.openai.com/api-keys

3. **Verify keys are correct:**
   - Check for extra spaces or quotes
   - Ensure keys are not expired
   - Verify keys have necessary permissions

### 6. Port Already in Use

**Problem:** "Address already in use" or "Port 8001 is already in use"

**Solution:**

1. **Change port:**
   ```bash
   # In .env file
   PORT=8002
   ```

2. **Or stop service using port:**
   ```bash
   # Find process using port
   lsof -i :8001  # macOS/Linux
   netstat -ano | findstr :8001  # Windows
   
   # Kill process
   kill -9 <PID>  # macOS/Linux
   taskkill /PID <PID> /F  # Windows
   ```

3. **For Docker:**
   - Update port mapping in docker-compose.yml:
     ```yaml
     ports:
       - "8002:8001"
     ```

### 7. Module Not Found Errors

**Problem:** "ModuleNotFoundError: No module named 'X'"

**Solution:**

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Verify virtual environment:**
   ```bash
   # Activate virtual environment
   source venv/bin/activate  # macOS/Linux
   venv\Scripts\activate     # Windows
   ```

3. **For Docker:**
   - Rebuild image: `docker-compose build`

### 8. Database Schema Errors

**Problem:** "Table does not exist" or schema errors

**Solution:**

1. **Delete database file (SQLite):**
   ```bash
   rm youtube_transcriptions.db
   # Restart service - schema will be recreated
   ```

2. **Recreate schema (PostgreSQL):**
   ```sql
   DROP DATABASE youtube_transcriptions;
   CREATE DATABASE youtube_transcriptions;
   # Restart service - schema will be recreated
   ```

3. **Check database permissions:**
   - Ensure user has CREATE TABLE permissions
   - Verify database connection

### 9. Cookie Format Errors

**Problem:** "Invalid cookie format"

**Solution:**

1. **Correct format:**
   ```
   name1=value1; name2=value2; name3=value3
   ```

2. **Common mistakes:**
   - Missing semicolons between cookies
   - Extra quotes around entire string
   - Missing `=` signs

3. **Get fresh cookies:**
   - Follow instructions in [Configuration Guide](configuration.md#getting-youtube-cookies)
   - Ensure cookies are from logged-in session

### 10. Video Not Found Errors

**Problem:** "Video unavailable" or "Video not found"

**Solution:**

1. **Verify video exists:**
   - Check video ID is correct
   - Ensure video is not private or deleted
   - Test video URL in browser

2. **Check video status:**
   - Video might be age-restricted
   - Video might be region-locked
   - Video might require login

3. **Use cookies:**
   - Some videos require authentication
   - Configure cookies to access restricted content

### 11. Slow Processing

**Problem:** Videos processing very slowly

**Solution:**

1. **Check rate limiting:**
   - Increase `YOUTUBE_SLEEP_INTERVAL` if hitting rate limits
   - Process videos in smaller batches

2. **Check network:**
   - Slow internet connection affects download speed
   - Check bandwidth usage

3. **Check API limits:**
   - Deepgram API has rate limits
   - OpenAI API has rate limits
   - Check API usage in respective dashboards

4. **Database performance:**
   - Use PostgreSQL for better performance with large datasets
   - Add database indexes if needed

### 12. Docker Issues

**Problem:** Docker container won't start or crashes

**Solution:**

1. **Check logs:**
   ```bash
   docker-compose logs youtube-transcription
   ```

2. **Rebuild container:**
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Check environment variables:**
   - Ensure `.env` file exists
   - Verify all required variables are set

4. **Check port conflicts:**
   - Ensure port 8001 is not in use
   - Change port if needed

## Getting Help

If you encounter issues not covered here:

1. **Check logs:**
   - Application logs in console
   - Docker logs: `docker-compose logs`
   - Database logs (if applicable)

2. **Verify configuration:**
   - Check `.env` file settings
   - Verify API keys are correct
   - Ensure database is accessible

3. **Check documentation:**
   - [Installation Guide](installation.md)
   - [Configuration Guide](configuration.md)
   - [API Documentation](api.md)

4. **Report issues:**
   - Create GitHub issue with:
     - Error message
     - Steps to reproduce
     - Configuration details (without sensitive data)
     - Logs (if available)

## Related Documentation

- [Installation Guide](installation.md) - Setup instructions
- [Configuration Guide](configuration.md) - Environment setup
- [Database Setup](database.md) - Database configuration
