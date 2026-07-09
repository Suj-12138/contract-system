"""测试配置工厂函数 — P5 Task 27."""
import os
from pathlib import Path

from app.config import Settings
from app.domain.enums import UserRole
from app.domain.models import make_user
from app.repositories.json_repository import JsonRepository
from app.security.passwords import hash_password
from app.storage.json_store import JsonFileStore


def make_settings(tmp_path: Path) -> Settings:
    """创建指向临时目录的测试配置."""
    data_file = str(tmp_path / "store.json")
    settings = Settings()
    settings.DATA_FILE = data_file
    return settings


def make_store(settings: Settings) -> JsonFileStore:
    """创建使用测试数据文件的存储实例."""
    return JsonFileStore(settings.DATA_FILE)


def make_repo(settings: Settings) -> JsonRepository:
    """创建仓储实例."""
    return JsonRepository(make_store(settings))


async def make_client(app_with_overrides):
    """创建 httpx AsyncClient，绑定被 override 后的 app."""
    from httpx import ASGITransport, AsyncClient

    transport = ASGITransport(app=app_with_overrides)
    return AsyncClient(transport=transport, base_url="http://test")


def seed_admin(repo: JsonRepository) -> dict:
    """创建测试管理员并返回用户字典."""
    admin = make_user(
        repo._store, "admin", "admin@test.com",
        hash_password("pass123456"), UserRole.ADMIN,
    )
    return repo.create_user(admin)


def seed_handler(repo: JsonRepository) -> dict:
    """创建测试经办人."""
    user = make_user(
        repo._store, "handler1", "handler@test.com",
        hash_password("pass123456"), UserRole.HANDLER,
    )
    return repo.create_user(user)


def seed_approver(repo: JsonRepository) -> dict:
    """创建测试审批人."""
    user = make_user(
        repo._store, "approver1", "approver@test.com",
        hash_password("pass123456"), UserRole.APPROVER,
    )
    return repo.create_user(user)


def seed_approver2(repo: JsonRepository) -> dict:
    """创建第二个测试审批人（用于两级审批）."""
    user = make_user(
        repo._store, "approver2", "approver2@test.com",
        hash_password("pass123456"), UserRole.APPROVER,
    )
    return repo.create_user(user)


async def login(client, username_or_email: str, password: str) -> str:
    """登录并返回 session cookie 值."""
    resp = await client.post("/api/v1/auth/login", json={
        "username_or_email": username_or_email,
        "password": password,
    })
    assert resp.status_code == 200
    return resp.cookies.get("contract_session")
