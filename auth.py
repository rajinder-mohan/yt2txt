import hashlib
import secrets
from typing import Optional
from fastapi import HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from database import get_db_connection

security = HTTPBearer()

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


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Dependency to get current authenticated user."""
    token = credentials.credentials
    username = get_user_from_token(token)
    if not username:
        raise HTTPException(status_code=401, detail="Invalid or expired session")
    return username

