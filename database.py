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
        


def get_video_record(video_id: str) -> Optional[Dict]:
    """Get video record from database by video_id."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            return fetch_one(conn, "SELECT * FROM video_transcriptions WHERE video_id = %s", (video_id,))
        else:  # SQLite
            return fetch_one(conn, "SELECT * FROM video_transcriptions WHERE video_id = ?", (video_id,))


def create_video_record(video_id: str, video_url: str = None, status: str = "processing"):
    """Create a new video record in the database."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO video_transcriptions 
                (video_id, video_url, status, created_at, updated_at)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (video_id) DO NOTHING
            """, (video_id, video_url, status, datetime.now(), datetime.now()))
            cursor.close()
        else:  # SQLite
            conn.execute("""
                INSERT OR IGNORE INTO video_transcriptions 
                (video_id, video_url, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?)
            """, (video_id, video_url, status, datetime.now(), datetime.now()))


def update_video_record(
    video_id: str,
    status: str = None,
    transcript: str = None,
    audio_file_path: str = None,
    error_message: str = None
):
    """Update video record in the database."""
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
    """Get all videos from database (for admin dashboard)."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            return fetch_all(conn, """
                SELECT id, video_id, video_url, status, transcript, error_message, 
                       created_at, updated_at
                FROM video_transcriptions
                ORDER BY updated_at DESC
            """)
        else:  # SQLite
            return fetch_all(conn, """
                SELECT id, video_id, video_url, status, transcript, error_message, 
                       created_at, updated_at
                FROM video_transcriptions
                ORDER BY updated_at DESC
            """)


def get_stats():
    """Get statistics about videos."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            total = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions")
            success = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'success'")
            failed = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'failed'")
            processing = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'processing'")
        else:  # SQLite
            total = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions")
            success = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'success'")
            failed = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'failed'")
            processing = fetch_one(conn, "SELECT COUNT(*) as count FROM video_transcriptions WHERE status = 'processing'")
        
        return {
            "total": total['count'] if total else 0,
            "success": success['count'] if success else 0,
            "failed": failed['count'] if failed else 0,
            "processing": processing['count'] if processing else 0
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
