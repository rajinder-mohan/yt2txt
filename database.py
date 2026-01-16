import os
import hashlib
from datetime import datetime
from typing import Optional, Dict, Any
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
                       created_at, updated_at
                FROM video_transcriptions
                ORDER BY updated_at DESC
            """)
        else:  # SQLite
            videos = fetch_all(conn, """
                SELECT id, video_id, video_url, status, transcript, error_message, 
                       title, duration, view_count, upload_date, channel_name, channel_id, metadata,
                       created_at, updated_at
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
