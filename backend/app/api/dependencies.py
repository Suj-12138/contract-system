import hashlib
from datetime import datetime, timezone

from fastapi import Depends, Request

from app.api.errors import authentication_required, forbidden
from app.config import Settings, get_settings
from app.storage.json_store import JsonFileStore


def get_store(settings: Settings = Depends(get_settings)) -> JsonFileStore:
    return JsonFileStore(settings.DATA_FILE)


def get_current_user(request: Request, store: JsonFileStore = Depends(get_store)) -> dict:
    settings = get_settings()
    token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if not token:
        authentication_required()
    token_hash = hashlib.sha256(token.encode()).hexdigest()
    data = store.read()
    for session in data.get("sessions", []):
        if session["token_hash"] == token_hash:
            expires_at = datetime.fromisoformat(session["expires_at"].replace("Z", "+00:00"))
            if datetime.now(timezone.utc) > expires_at:
                authentication_required()
            for user in data.get("users", []):
                if user["id"] == session["user_id"]:
                    if not user.get("is_active", True):
                        authentication_required()
                    return user
    authentication_required()


def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "admin":
        forbidden()
    return user


def require_handler(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "handler":
        forbidden()
    return user


def require_approver(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] != "approver":
        forbidden()
    return user


def require_internal(user: dict = Depends(get_current_user)) -> dict:
    if user["role"] not in ("approver", "admin"):
        forbidden()
    return user
