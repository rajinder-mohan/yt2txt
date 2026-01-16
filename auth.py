import hashlib
import secrets
import os
from typing import Optional
from fastapi import HTTPException, Depends, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db_connection, DB_TYPE
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer(auto_error=False)

# API Key from environment variable
API_KEY = os.getenv("API_KEY", "")

# Simple session storage (in production, use Redis or database)
active_sessions = {}


def hash_password(password: str) -> str:
    """Hash password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash."""
    return hash_password(password) == password_hash


def authenticate_user(username: str, password: str) -> bool:
    """Authenticate user credentials."""
    with get_db_connection() as conn:
        if DB_TYPE == "postgres":
            from psycopg2.extras import RealDictCursor
            cursor = conn.cursor(cursor_factory=RealDictCursor)
            cursor.execute(
                "SELECT password_hash FROM admin_users WHERE username = %s",
                (username,)
            )
            row = cursor.fetchone()
            cursor.close()
        else:  # SQLite
            cursor = conn.execute(
                "SELECT password_hash FROM admin_users WHERE username = ?",
                (username,)
            )
            row = cursor.fetchone()
        
        if row:
            return verify_password(password, row['password_hash'])
        return False


def create_session(username: str) -> str:
    """Create a new session token."""
    token = secrets.token_urlsafe(32)
    active_sessions[token] = username
    return token


def get_user_from_token(token: str) -> Optional[str]:
    """Get username from session token."""
    return active_sessions.get(token)


def delete_session(token: str):
    """Delete a session."""
    if token in active_sessions:
        del active_sessions[token]


def update_user_password(username: str, new_password: str) -> bool:
    """Update user password in database."""
    try:
        new_password_hash = hash_password(new_password)
        with get_db_connection() as conn:
            if DB_TYPE == "postgres":
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE admin_users SET password_hash = %s WHERE username = %s",
                    (new_password_hash, username)
                )
                cursor.close()
            else:  # SQLite
                conn.execute(
                    "UPDATE admin_users SET password_hash = ? WHERE username = ?",
                    (new_password_hash, username)
                )
        return True
    except Exception as e:
        print(f"Error updating password: {e}")
        return False


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    username = get_user_from_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return username


async def get_api_key_header(x_api_key: Optional[str] = Header(None)) -> Optional[str]:
    """Get API key from X-API-Key header."""
    return x_api_key


async def authenticate_api_request(
    x_api_key: Optional[str] = Header(None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Flexible authentication: Accepts either Bearer token OR API key.
    
    Priority:
    1. X-API-Key header (API key auth) - checked first
    2. Bearer token (session-based auth) - checked if no API key
    
    Returns username or 'api_user' for API key authentication.
    """
    # Try API key first (easier to check)
    if x_api_key:
        if API_KEY and x_api_key == API_KEY:
            return "api_user"
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid API key"
            )
    
    # Try Bearer token if no API key provided
    if credentials:
        token = credentials.credentials
        username = get_user_from_token(token)
        if username:
            return username
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid or expired session token"
            )
    
    # No valid authentication found
    raise HTTPException(
        status_code=401,
        detail="Authentication required. Provide either Bearer token (Authorization: Bearer <token>) or X-API-Key header"
    )

