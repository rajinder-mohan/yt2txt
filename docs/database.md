# Database Setup Guide

## Database Options

The service supports two database backends:

- **SQLite** (default) - Perfect for development and small deployments
- **PostgreSQL** - Recommended for production and multi-user environments

## SQLite (Default)

SQLite is used by default and requires no setup. The database file is created automatically at `youtube_transcriptions.db`.

### Advantages
- No installation required
- Perfect for development and small deployments
- Single file database
- Easy backup (just copy the file)

### Configuration

In your `.env` file:
```bash
DB_TYPE=sqlite
SQLITE_PATH=youtube_transcriptions.db
```

The database schema is created automatically on first run.

## PostgreSQL (Production)

For production or multi-user environments, use PostgreSQL.

### Installation

**Ubuntu/Debian:**
```bash
sudo apt-get update
sudo apt-get install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

**macOS:**
```bash
brew install postgresql
brew services start postgresql
```

**Windows:**
Download and install from [PostgreSQL Downloads](https://www.postgresql.org/download/windows/)

### Database Setup

1. **Create database and user:**
   ```bash
   sudo -u postgres psql
   ```

2. **In PostgreSQL prompt:**
   ```sql
   CREATE DATABASE youtube_transcriptions;
   CREATE USER your_user WITH PASSWORD 'your_password';
   GRANT ALL PRIVILEGES ON DATABASE youtube_transcriptions TO your_user;
   \q
   ```

3. **Update `.env` file:**
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

### Docker PostgreSQL Setup

If using Docker, you can add PostgreSQL to your `docker-compose.yml`:

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_DB: youtube_transcriptions
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  youtube-transcription:
    # ... your existing config
    environment:
      DB_TYPE: postgres
      POSTGRES_HOST: postgres
      POSTGRES_PORT: 5432
      # ... other env vars

volumes:
  postgres_data:
```

## Database Schema

The following tables are created automatically:

### `video_transcriptions`
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

### `prompts`
Stores AI prompt templates.

**Fields:**
- `id` - Primary key
- `name` - Prompt name
- `description` - Description
- `system_prompt` - System prompt (TEXT, unlimited)
- `user_prompt_template` - User template with variables (TEXT, unlimited)
- `operation_type` - Category (e.g., 'summarize', 'extract_keywords')
- `created_at` / `updated_at` - Timestamps

### `generated_content`
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

### `admin_users`
Stores admin user accounts.

**Fields:**
- `id` - Primary key
- `username` - Username (unique)
- `password_hash` - Hashed password
- `created_at` - Timestamp

### `settings`
Stores key-value settings.

**Fields:**
- `id` - Primary key
- `setting_key` - Setting name (unique)
- `setting_value` - Setting value (TEXT)
- `updated_at` - Timestamp

## Large Text Storage

All large text fields (transcripts, prompts, generated content) use `TEXT` type which supports:
- **PostgreSQL**: Up to ~1GB per field
- **SQLite**: Up to maximum database size (default 140TB)

This ensures unlimited storage for transcripts, prompts, and AI-generated content.

## Backup and Migration

### SQLite Backup
```bash
# Simple file copy
cp youtube_transcriptions.db youtube_transcriptions.db.backup
```

### PostgreSQL Backup
```bash
# Backup
pg_dump -U your_user youtube_transcriptions > backup.sql

# Restore
psql -U your_user youtube_transcriptions < backup.sql
```

### Migration from SQLite to PostgreSQL

1. Export data from SQLite
2. Create PostgreSQL database
3. Import data into PostgreSQL
4. Update `.env` to use PostgreSQL

## Related Documentation

- [Configuration Guide](configuration.md) - Environment variables
- [Troubleshooting](troubleshooting.md) - Database connection issues
