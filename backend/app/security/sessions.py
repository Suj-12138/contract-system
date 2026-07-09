import hashlib
import secrets
from datetime import datetime, timedelta, timezone

from app.config import get_settings


def generate_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def make_session(user_id: str, raw_token: str) -> dict:
    settings = get_settings()
    now = datetime.now(timezone.utc)
    return {
        "user_id": user_id,
        "token_hash": hash_token(raw_token),
        "expires_at": (now + timedelta(hours=settings.SESSION_TTL_HOURS)).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "created_at": now.strftime("%Y-%m-%dT%H:%M:%SZ"),
    }


def is_session_expired(session: dict) -> bool:
    expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
    return datetime.now(timezone.utc) > expires_at
