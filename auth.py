import hashlib
import secrets
import os
import base64
from typing import Optional
from fastapi import HTTPException, Depends, Header, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials, HTTPBasic, HTTPBasicCredentials
from database import get_db_connection, DB_TYPE
from dotenv import load_dotenv

load_dotenv()

security = HTTPBearer(auto_error=False)
basic_security = HTTPBasic(auto_error=False)

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


def authenticate_basic_auth_sync(username: str, password: str) -> Optional[str]:
    """Synchronous Basic Auth authentication."""
    if authenticate_user(username, password):
        return username
    return None


async def authenticate_api_request(
    request: Request,
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    basic_credentials: Optional[HTTPBasicCredentials] = Depends(basic_security)
) -> str:
    """
    Authentication for API endpoints: Accepts Basic Auth or Bearer token.
    
    Priority:
    1. Basic Auth (username:password) - recommended for external API access
    2. Bearer token (session-based auth) - for dashboard sessions
    
    Returns username for authenticated requests.
    """
    # Try Basic Auth first (recommended for external API access)
    if basic_credentials:
        username = authenticate_basic_auth_sync(basic_credentials.username, basic_credentials.password)
        if username:
            return username
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid Basic Auth credentials",
                headers={"WWW-Authenticate": "Basic"}
            )
    
    # Try Bearer token if no Basic Auth provided (for dashboard sessions)
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
        detail="Authentication required. Provide Basic Auth (username:password) or Bearer token (Authorization: Bearer <token>)",
        headers={"WWW-Authenticate": "Basic"}
    )

