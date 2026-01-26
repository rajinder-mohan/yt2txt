import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database configuration
DB_TYPE = os.getenv("DB_TYPE", "sqlite").lower()

# SQLite configuration
SQLITE_PATH = os.getenv("SQLITE_PATH", "youtube_transcriptions.db")

# PostgreSQL configuration
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "youtube_transcriptions")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "postgres")


def get_db_connection_sqlite():
    """Get SQLite database connection."""
    import sqlite3
    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_db_connection_postgres():
    """Get PostgreSQL database connection."""
    try:
        import psycopg2
        from psycopg2.extras import RealDictCursor
        
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            database=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            connect_timeout=10
        )
        return conn
    except ImportError:
        raise ImportError("psycopg2-binary is required for PostgreSQL support. Install it with: pip install psycopg2-binary")
    except Exception as e:
        error_msg = str(e)
        if "Connection refused" in error_msg or "connection to server" in error_msg.lower():
            raise ConnectionError(
                f"Cannot connect to PostgreSQL at {POSTGRES_HOST}:{POSTGRES_PORT}. "
                f"If running in Docker, use 'network_mode: host' in docker-compose.yml (already configured) "
                f"or set POSTGRES_HOST to your host's IP address. "
                f"Original error: {error_msg}"
            )
        raise


@contextmanager
def get_db_connection():
    """Context manager for database connections (supports both SQLite and PostgreSQL)."""
    if DB_TYPE == "postgres":
        conn = get_db_connection_postgres()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()
    else:  # SQLite (default)
        conn = get_db_connection_sqlite()
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()


def fetch_one(conn, query: str, params: tuple = None) -> Optional[Dict]:
    """Fetch one row from database."""
    if DB_TYPE == "postgres":
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:  # SQLite
        cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None
    finally:
        cursor.close()


def fetch_all(conn, query: str, params: tuple = None) -> list:
    """Fetch all rows from database."""
    if DB_TYPE == "postgres":
        from psycopg2.extras import RealDictCursor
        cursor = conn.cursor(cursor_factory=RealDictCursor)
    else:  # SQLite
        cursor = conn.cursor()
    
    try:
        cursor.execute(query, params)
        rows = cursor.fetchall()
        if rows:
            return [dict(row) for row in rows]
        return []
    finally:
        cursor.close()


def init_database():
    """Initialize the database and create tables if they don't exist."""
    with get_db_connection() as conn:
        # Video transcriptions table
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS video_transcriptions (
                    id SERIAL PRIMARY KEY,
                    video_id VARCHAR(255) NOT NULL UNIQUE,
                    video_url TEXT,
                    status VARCHAR(50) NOT NULL,
                    transcript TEXT,
                    audio_file_path TEXT,
                    error_message TEXT,
                    title TEXT,
                    duration INTEGER,
                    view_count BIGINT,
                    upload_date DATE,
                    channel_name TEXT,
                    channel_id TEXT,
                    metadata JSONB,
                    ignored BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_id ON video_transcriptions(video_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON video_transcriptions(status)
            """)
            
            # Admin users table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id SERIAL PRIMARY KEY,
                    username VARCHAR(255) NOT NULL UNIQUE,
                    password_hash VARCHAR(255) NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Settings table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id SERIAL PRIMARY KEY,
                    setting_key VARCHAR(255) NOT NULL UNIQUE,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Prompts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    system_prompt TEXT,
                    user_prompt_template TEXT,
                    operation_type VARCHAR(100),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompts_operation_type ON prompts(operation_type)
            """)
            
            # Generated content table (1 video -> many content items)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS generated_content (
                    id SERIAL PRIMARY KEY,
                    video_id VARCHAR(255) NOT NULL,
                    prompt_id INTEGER,
                    prompt_text TEXT,
                    model VARCHAR(100),
                    temperature FLOAT,
                    max_tokens INTEGER,
                    generated_text TEXT NOT NULL,
                    usage_info JSONB,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES video_transcriptions(video_id) ON DELETE CASCADE
                )
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_generated_content_video_id ON generated_content(video_id)
            """)
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_generated_content_prompt_id ON generated_content(prompt_id)
            """)
            cursor.close()
        else:  # SQLite
            conn.execute("""
                CREATE TABLE IF NOT EXISTS video_transcriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL UNIQUE,
                    video_url TEXT,
                    status TEXT NOT NULL,
                    transcript TEXT,
                    audio_file_path TEXT,
                    error_message TEXT,
                    title TEXT,
                    duration INTEGER,
                    view_count INTEGER,
                    upload_date TEXT,
                    channel_name TEXT,
                    channel_id TEXT,
                    metadata TEXT,
                    ignored INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_video_id ON video_transcriptions(video_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_status ON video_transcriptions(status)
            """)
            
            # Admin users table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS admin_users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    username TEXT NOT NULL UNIQUE,
                    password_hash TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Settings table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS settings (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    setting_key TEXT NOT NULL UNIQUE,
                    setting_value TEXT,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Prompts table
            conn.execute("""
                CREATE TABLE IF NOT EXISTS prompts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    description TEXT,
                    system_prompt TEXT,
                    user_prompt_template TEXT,
                    operation_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_prompts_operation_type ON prompts(operation_type)
            """)
            
            # Generated content table (1 video -> many content items)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS generated_content (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    video_id TEXT NOT NULL,
                    prompt_id INTEGER,
                    prompt_text TEXT,
                    model TEXT,
                    temperature REAL,
                    max_tokens INTEGER,
                    generated_text TEXT NOT NULL,
                    usage_info TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (video_id) REFERENCES video_transcriptions(video_id) ON DELETE CASCADE
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_generated_content_video_id ON generated_content(video_id)
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_generated_content_prompt_id ON generated_content(prompt_id)
            """)
        
        # Add metadata columns if they don't exist (migration for existing databases)
        _add_metadata_columns(conn)


def _add_metadata_columns(conn):
    """Add metadata columns to existing video_transcriptions table if they don't exist."""
    import json
    metadata_columns = [
        ("title", "TEXT"),
        ("duration", "INTEGER" if DB_TYPE == "postgres" else "INTEGER"),
        ("view_count", "BIGINT" if DB_TYPE == "postgres" else "INTEGER"),
        ("upload_date", "DATE" if DB_TYPE == "postgres" else "TEXT"),
        ("channel_name", "TEXT"),
        ("channel_id", "TEXT"),
        ("metadata", "JSONB" if DB_TYPE == "postgres" else "TEXT"),
        ("ignored", "BOOLEAN" if DB_TYPE == "postgres" else "INTEGER"),
    ]
    
    for column_name, column_type in metadata_columns:
        try:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                # Check if column exists
                cursor.execute("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='video_transcriptions' AND column_name=%s
                """, (column_name,))
                if not cursor.fetchone():
                    cursor.execute(f"ALTER TABLE video_transcriptions ADD COLUMN {column_name} {column_type}")
                    conn.commit()
                cursor.close()
            else:  # SQLite
                # SQLite doesn't support ALTER TABLE ADD COLUMN IF NOT EXISTS easily
                # Try to add column and ignore if it exists
                try:
                    conn.execute(f"ALTER TABLE video_transcriptions ADD COLUMN {column_name} {column_type}")
                    conn.commit()
                except Exception:
                    # Column likely already exists, ignore
                    pass
        except Exception as e:
            # Column might already exist or other error, continue
            print(f"Note: Could not add column {column_name}: {e}")


def get_video_record(video_id: str) -> Optional[Dict]:
    """Get video record from database by video_id."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            return fetch_one(conn, "SELECT * FROM video_transcriptions WHERE video_id = %s", (video_id,))
        else:  # SQLite
            return fetch_one(conn, "SELECT * FROM video_transcriptions WHERE video_id = ?", (video_id,))


def create_video_record(
    video_id: str, 
    video_url: str = None, 
    status: str = "processing",
    title: str = None,
    duration: int = None,
    view_count: int = None,
    upload_date: str = None,
    channel_name: str = None,
    channel_id: str = None,
    metadata: dict = None
):
    """Create a new video record in the database with optional metadata."""
    import json
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            # Convert metadata dict to JSON string for PostgreSQL JSONB
            metadata_json = json.dumps(metadata) if metadata else None
            cursor.execute("""
                INSERT INTO video_transcriptions 
                (video_id, video_url, status, title, duration, view_count, upload_date, channel_name, channel_id, metadata, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s, %s)
                ON CONFLICT (video_id) DO NOTHING
            """, (video_id, video_url, status, title, duration, view_count, upload_date, channel_name, channel_id, metadata_json, datetime.now(), datetime.now()))
            cursor.close()
        else:  # SQLite
            # Convert metadata dict to JSON string for SQLite TEXT
            metadata_json = json.dumps(metadata) if metadata else None
            conn.execute("""
                INSERT OR IGNORE INTO video_transcriptions 
                (video_id, video_url, status, title, duration, view_count, upload_date, channel_name, channel_id, metadata, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (video_id, video_url, status, title, duration, view_count, upload_date, channel_name, channel_id, metadata_json, datetime.now(), datetime.now()))


def update_video_record(
    video_id: str,
    status: str = None,
    transcript: str = None,
    audio_file_path: str = None,
    error_message: str = None,
    video_url: str = None,
    title: str = None,
    duration: int = None,
    view_count: int = None,
    upload_date: str = None,
    channel_name: str = None,
    channel_id: str = None,
    metadata: dict = None
):
    """Update video record in the database with optional metadata."""
    import json
    updates = []
    params = []
    
    if status is not None:
        updates.append("status = %s" if DB_TYPE == "postgres" else "status = ?")
        params.append(status)
    
    if transcript is not None:
        updates.append("transcript = %s" if DB_TYPE == "postgres" else "transcript = ?")
        params.append(transcript)
    
    if audio_file_path is not None:
        updates.append("audio_file_path = %s" if DB_TYPE == "postgres" else "audio_file_path = ?")
        params.append(audio_file_path)
    
    if error_message is not None:
        updates.append("error_message = %s" if DB_TYPE == "postgres" else "error_message = ?")
        params.append(error_message)
    
    if video_url is not None:
        updates.append("video_url = %s" if DB_TYPE == "postgres" else "video_url = ?")
        params.append(video_url)
    
    if title is not None:
        updates.append("title = %s" if DB_TYPE == "postgres" else "title = ?")
        params.append(title)
    
    if duration is not None:
        updates.append("duration = %s" if DB_TYPE == "postgres" else "duration = ?")
        params.append(duration)
    
    if view_count is not None:
        updates.append("view_count = %s" if DB_TYPE == "postgres" else "view_count = ?")
        params.append(view_count)
    
    if upload_date is not None:
        updates.append("upload_date = %s" if DB_TYPE == "postgres" else "upload_date = ?")
        params.append(upload_date)
    
    if channel_name is not None:
        updates.append("channel_name = %s" if DB_TYPE == "postgres" else "channel_name = ?")
        params.append(channel_name)
    
    if channel_id is not None:
        updates.append("channel_id = %s" if DB_TYPE == "postgres" else "channel_id = ?")
        params.append(channel_id)
    
    if metadata is not None:
        metadata_json = json.dumps(metadata) if metadata else None
        if DB_TYPE == "postgres":
            updates.append("metadata = %s::jsonb")
        else:
            updates.append("metadata = ?")
        params.append(metadata_json)
    
    updates.append("updated_at = %s" if DB_TYPE == "postgres" else "updated_at = ?")
    params.append(datetime.now())
    
    if DB_TYPE == "postgres":
        params.append(video_id)
        query = f"UPDATE video_transcriptions SET {', '.join(updates)} WHERE video_id = %s"
    else:  # SQLite
        params.append(video_id)
        query = f"UPDATE video_transcriptions SET {', '.join(updates)} WHERE video_id = ?"
    
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute(query, params)
        cursor.close()


def delete_audio_file_path(video_id: str):
    """Remove audio_file_path from database after successful deletion."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE video_transcriptions SET audio_file_path = NULL, updated_at = %s WHERE video_id = %s",
                (datetime.now(), video_id)
            )
            cursor.close()
        else:  # SQLite
            conn.execute(
                "UPDATE video_transcriptions SET audio_file_path = NULL, updated_at = ? WHERE video_id = ?",
                (datetime.now(), video_id)
            )


def get_all_videos():
    """Get all videos from database (for admin dashboard) with metadata."""
    import json
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            videos = fetch_all(conn, """
                SELECT id, video_id, video_url, status, transcript, error_message, 
                       title, duration, view_count, upload_date, channel_name, channel_id, metadata,
                       ignored, created_at, updated_at
                FROM video_transcriptions
                ORDER BY updated_at DESC
            """)
        else:  # SQLite
            videos = fetch_all(conn, """
                SELECT id, video_id, video_url, status, transcript, error_message, 
                       title, duration, view_count, upload_date, channel_name, channel_id, metadata,
                       ignored, created_at, updated_at
                FROM video_transcriptions
                ORDER BY updated_at DESC
            """)
        
        # Parse JSON metadata for each video
        for video in videos:
            if video.get('metadata'):
                try:
                    if isinstance(video['metadata'], str):
                        video['metadata'] = json.loads(video['metadata'])
                except (json.JSONDecodeError, TypeError):
                    video['metadata'] = None
        
        return videos


def get_stats():
    """Get statistics about videos."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            total = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions")
            processed = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status IN ('success', 'processed')")
            failed = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'failed'")
            processing = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'processing'")
            pending = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'pending'")
            rate_limited = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'rate_limited'")
        else:  # SQLite
            total = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions")
            processed = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status IN ('success', 'processed')")
            failed = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'failed'")
            processing = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'processing'")
            pending = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'pending'")
            rate_limited = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'rate_limited'")
        
        return {
            "total": total['count'] if total else 0,
            "success": processed['count'] if processed else 0,  # Keep 'success' for backward compatibility
            "processed": processed['count'] if processed else 0,
            "failed": failed['count'] if failed else 0,
            "processing": processing['count'] if processing else 0,
            "pending": pending['count'] if pending else 0,
            "rate_limited": rate_limited['count'] if rate_limited else 0
        }


def get_setting(setting_key: str) -> Optional[str]:
    """Get a setting value by key."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            result = fetch_one(conn, "SELECT setting_value FROM settings WHERE setting_key = %s", (setting_key,))
        else:  # SQLite
            result = fetch_one(conn, "SELECT setting_value FROM settings WHERE setting_key = ?", (setting_key,))
        
        return result['setting_value'] if result and result.get('setting_value') else None


def set_setting(setting_key: str, setting_value: str) -> bool:
    """Set a setting value by key."""
    try:
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO settings (setting_key, setting_value, updated_at)
                    VALUES (%s, %s, %s)
                    ON CONFLICT (setting_key) DO UPDATE 
                    SET setting_value = EXCLUDED.setting_value,
                        updated_at = EXCLUDED.updated_at
                """, (setting_key, setting_value, datetime.now()))
                cursor.close()
            else:  # SQLite
                conn.execute("""
                    INSERT OR REPLACE INTO settings (setting_key, setting_value, updated_at)
                    VALUES (?, ?, ?)
                """, (setting_key, setting_value, datetime.now()))
        return True
    except Exception as e:
        print(f"Error setting setting: {e}")
        return False


# Prompt management functions
def get_all_prompts(operation_type: Optional[str] = None) -> list:
    """Get all prompts, optionally filtered by operation_type."""
    with get_db_connection() as conn:
        if operation_type:
            if DB_TYPE == "postgres":
                prompts = fetch_all(conn, "SELECT * FROM prompts WHERE operation_type = %s ORDER BY created_at DESC", (operation_type,))
            else:
                prompts = fetch_all(conn, "SELECT * FROM prompts WHERE operation_type = ? ORDER BY created_at DESC", (operation_type,))
        else:
            prompts = fetch_all(conn, "SELECT * FROM prompts ORDER BY created_at DESC")
        return prompts


def get_prompt(prompt_id: int) -> Optional[Dict]:
    """Get a prompt by ID."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            return fetch_one(conn, "SELECT * FROM prompts WHERE id = %s", (prompt_id,))
        else:
            return fetch_one(conn, "SELECT * FROM prompts WHERE id = ?", (prompt_id,))


def create_prompt(name: str, description: Optional[str] = None, system_prompt: Optional[str] = None, 
                  user_prompt_template: Optional[str] = None, operation_type: Optional[str] = None) -> int:
    """Create a new prompt and return its ID."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO prompts (name, description, system_prompt, user_prompt_template, operation_type, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (name, description, system_prompt, user_prompt_template, operation_type, datetime.now(), datetime.now()))
            prompt_id = cursor.fetchone()[0]
            cursor.close()
        else:  # SQLite
            cursor = conn.execute("""
                INSERT INTO prompts (name, description, system_prompt, user_prompt_template, operation_type, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (name, description, system_prompt, user_prompt_template, operation_type, datetime.now(), datetime.now()))
            prompt_id = cursor.lastrowid
        return prompt_id


def update_prompt(prompt_id: int, name: Optional[str] = None, description: Optional[str] = None,
                  system_prompt: Optional[str] = None, user_prompt_template: Optional[str] = None,
                  operation_type: Optional[str] = None) -> bool:
    """Update a prompt."""
    updates = []
    params = []
    
    if name is not None:
        updates.append("name = %s" if DB_TYPE == "postgres" else "name = ?")
        params.append(name)
    if description is not None:
        updates.append("description = %s" if DB_TYPE == "postgres" else "description = ?")
        params.append(description)
    if system_prompt is not None:
        updates.append("system_prompt = %s" if DB_TYPE == "postgres" else "system_prompt = ?")
        params.append(system_prompt)
    if user_prompt_template is not None:
        updates.append("user_prompt_template = %s" if DB_TYPE == "postgres" else "user_prompt_template = ?")
        params.append(user_prompt_template)
    if operation_type is not None:
        updates.append("operation_type = %s" if DB_TYPE == "postgres" else "operation_type = ?")
        params.append(operation_type)
    
    if not updates:
        return False
    
    updates.append("updated_at = %s" if DB_TYPE == "postgres" else "updated_at = ?")
    params.append(datetime.now())
    params.append(prompt_id)
    
    try:
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                query = f"UPDATE prompts SET {', '.join(updates)} WHERE id = %s"
                cursor.execute(query, params)
                cursor.close()
            else:  # SQLite
                query = f"UPDATE prompts SET {', '.join(updates)} WHERE id = ?"
                conn.execute(query, params)
        return True
    except Exception as e:
        print(f"Error updating prompt: {e}")
        return False


def delete_prompt(prompt_id: int) -> bool:
    """Delete a prompt by ID."""
    try:
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                cursor.execute("DELETE FROM prompts WHERE id = %s", (prompt_id,))
                cursor.close()
            else:  # SQLite
                conn.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
        return True
    except Exception as e:
        print(f"Error deleting prompt: {e}")
        return False


# Generated Content Management Functions
def create_generated_content(
    video_id: str,
    generated_text: str,
    prompt_id: Optional[int] = None,
    prompt_text: Optional[str] = None,
    model: Optional[str] = None,
    temperature: Optional[float] = None,
    max_tokens: Optional[int] = None,
    usage_info: Optional[dict] = None
) -> int:
    """Create a new generated content record and return its ID."""
    import json
    
    usage_json = json.dumps(usage_info) if usage_info else None
    
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO generated_content 
                (video_id, prompt_id, prompt_text, model, temperature, max_tokens, generated_text, usage_info, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (video_id, prompt_id, prompt_text, model, temperature, max_tokens, generated_text, usage_json, datetime.now()))
            content_id = cursor.fetchone()[0]
            cursor.close()
        else:  # SQLite
            cursor = conn.execute("""
                INSERT INTO generated_content 
                (video_id, prompt_id, prompt_text, model, temperature, max_tokens, generated_text, usage_info, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (video_id, prompt_id, prompt_text, model, temperature, max_tokens, generated_text, usage_json, datetime.now()))
            content_id = cursor.lastrowid
        return content_id


def get_generated_content_by_video(video_id: str) -> list:
    """Get all generated content for a specific video."""
    import json
    
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            contents = fetch_all(conn, """
                SELECT * FROM generated_content 
                WHERE video_id = %s 
                ORDER BY created_at DESC
            """, (video_id,))
        else:
            contents = fetch_all(conn, """
                SELECT * FROM generated_content 
                WHERE video_id = ? 
                ORDER BY created_at DESC
            """, (video_id,))
        
        # Parse JSON usage_info
        for content in contents:
            if content.get('usage_info'):
                try:
                    if isinstance(content['usage_info'], str):
                        content['usage_info'] = json.loads(content['usage_info'])
                except (json.JSONDecodeError, TypeError):
                    content['usage_info'] = None
        
        return contents


def get_generated_content(content_id: int) -> Optional[Dict]:
    """Get a specific generated content by ID."""
    import json
    
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            content = fetch_one(conn, "SELECT * FROM generated_content WHERE id = %s", (content_id,))
        else:
            content = fetch_one(conn, "SELECT * FROM generated_content WHERE id = ?", (content_id,))
        
        if content and content.get('usage_info'):
            try:
                if isinstance(content['usage_info'], str):
                    content['usage_info'] = json.loads(content['usage_info'])
            except (json.JSONDecodeError, TypeError):
                content['usage_info'] = None
        
        return content


def delete_generated_content(content_id: int) -> bool:
    """Delete a generated content by ID."""
    try:
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                cursor.execute("DELETE FROM generated_content WHERE id = %s", (content_id,))
                cursor.close()
            else:  # SQLite
                conn.execute("DELETE FROM generated_content WHERE id = ?", (content_id,))
        return True
    except Exception as e:
        print(f"Error deleting generated content: {e}")
        return False


def get_all_generated_content(limit: Optional[int] = None, offset: Optional[int] = None) -> list:
    """Get all generated content, optionally with pagination."""
    import json
    
    query = "SELECT * FROM generated_content ORDER BY created_at DESC"
    params = []
    
    if limit:
        query += " LIMIT %s" if DB_TYPE == "postgres" else " LIMIT ?"
        params.append(limit)
        if offset:
            query += " OFFSET %s" if DB_TYPE == "postgres" else " OFFSET ?"
            params.append(offset)
    
    with get_db_connection() as conn:
        contents = fetch_all(conn, query, tuple(params) if params else None)
        
        # Parse JSON usage_info
        for content in contents:
            if content.get('usage_info'):
                try:
                    if isinstance(content['usage_info'], str):
                        content['usage_info'] = json.loads(content['usage_info'])
                except (json.JSONDecodeError, TypeError):
                    content['usage_info'] = None
        
        return contents


def update_video_ignored_status(video_id: str, ignored: bool) -> bool:
    """Update the ignored status of a video."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_transcriptions 
                SET ignored = %s, updated_at = %s 
                WHERE video_id = %s
            """, (ignored, datetime.now(), video_id))
            conn.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success
        else:  # SQLite
            ignored_int = 1 if ignored else 0
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE video_transcriptions 
                SET ignored = ?, updated_at = ? 
                WHERE video_id = ?
            """, (ignored_int, datetime.now(), video_id))
            conn.commit()
            success = cursor.rowcount > 0
            cursor.close()
            return success


def bulk_update_video_ignored_status(video_ids: List[str], ignored: bool) -> int:
    """Bulk update ignored status for multiple videos. Returns count of updated videos."""
    if not video_ids:
        return 0
    
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            placeholders = ','.join(['%s'] * len(video_ids))
            cursor.execute(f"""
                UPDATE video_transcriptions 
                SET ignored = %s, updated_at = %s 
                WHERE video_id IN ({placeholders})
            """, [ignored, datetime.now()] + video_ids)
            conn.commit()
            count = cursor.rowcount
            cursor.close()
            return count
        else:  # SQLite
            ignored_int = 1 if ignored else 0
            placeholders = ','.join(['?'] * len(video_ids))
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE video_transcriptions 
                SET ignored = ?, updated_at = ? 
                WHERE video_id IN ({placeholders})
            """, [ignored_int, datetime.now()] + video_ids)
            conn.commit()
            count = cursor.rowcount
            cursor.close()
            return count
