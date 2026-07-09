"""首次启动自动创建管理员."""
from app.config import get_settings
from app.domain.enums import UserRole
from app.domain.models import make_user
from app.repositories.json_repository import JsonRepository
from app.security.passwords import hash_password
from app.storage.json_store import JsonFileStore


def bootstrap_admin(store: JsonFileStore) -> None:
    settings = get_settings()
    if not settings.INITIAL_ADMIN_USERNAME or not settings.INITIAL_ADMIN_PASSWORD:
        return
    repo = JsonRepository(store)
    if repo.find_user_by_username(settings.INITIAL_ADMIN_USERNAME):
        return
    admin = make_user(
        store,
        settings.INITIAL_ADMIN_USERNAME,
        settings.INITIAL_ADMIN_EMAIL or f"{settings.INITIAL_ADMIN_USERNAME}@example.com",
        hash_password(settings.INITIAL_ADMIN_PASSWORD),
        UserRole.ADMIN,
    )
    repo.create_user(admin)
