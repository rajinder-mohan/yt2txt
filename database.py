import sqlite3
import os
import hashlib
from datetime import datetime
from typing import Optional, Dict
from contextlib import contextmanager
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_PATH = "youtube_transcriptions.db"


@contextmanager
def get_db_connection():
    """Context manager for database connections."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_database():
    """Initialize the database and create tables if they don't exist."""
    with get_db_connection() as conn:
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
        
        # Create admin users table
        conn.execute("""
            CREATE TABLE IF NOT EXISTS admin_users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create default admin user from environment variables or defaults
        default_username = os.getenv("ADMIN_USERNAME", "admin")
        default_password = os.getenv("ADMIN_PASSWORD", "admin")
        default_password_hash = hashlib.sha256(default_password.encode()).hexdigest()
        
        conn.execute("""
            INSERT OR IGNORE INTO admin_users (username, password_hash)
            VALUES (?, ?)
        """, (default_username, default_password_hash))


def get_video_record(video_id: str) -> Optional[Dict]:
    """Get video record from database by video_id."""
    with get_db_connection() as conn:
        cursor = conn.execute(
            "SELECT * FROM video_transcriptions WHERE video_id = ?",
            (video_id,)
        )
        row = cursor.fetchone()
        if row:
            return dict(row)
        return None


def create_video_record(video_id: str, video_url: str = None, status: str = "processing"):
    """Create a new video record in the database."""
    with get_db_connection() as conn:
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
        updates.append("status = ?")
        params.append(status)
    
    if transcript is not None:
        updates.append("transcript = ?")
        params.append(transcript)
    
    if audio_file_path is not None:
        updates.append("audio_file_path = ?")
        params.append(audio_file_path)
    
    if error_message is not None:
        updates.append("error_message = ?")
        params.append(error_message)
    
    updates.append("updated_at = ?")
    params.append(datetime.now())
    params.append(video_id)
    
    with get_db_connection() as conn:
        conn.execute(
            f"UPDATE video_transcriptions SET {', '.join(updates)} WHERE video_id = ?",
            params
        )


def delete_audio_file_path(video_id: str):
    """Remove audio_file_path from database after successful deletion."""
    with get_db_connection() as conn:
        conn.execute(
            "UPDATE video_transcriptions SET audio_file_path = NULL, updated_at = ? WHERE video_id = ?",
            (datetime.now(), video_id)
        )

