"""认证路由测试 — P5 Task 28."""
import anyio

from app.config import get_settings
from app.main import app

from .conftest import (
    login,
    make_client,
    make_repo,
    make_settings,
    seed_admin,
    seed_handler,
)


def test_login_success(tmp_path):
    """正常登录：返回用户信息 + 设置 cookie."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.post("/api/v1/auth/login", json={
                "username_or_email": "admin",
                "password": "pass123456",
            })
            assert resp.status_code == 200
            data = resp.json()
            assert data["user"]["username"] == "admin"
            assert data["user"]["role"] == "admin"
            assert resp.cookies.get("contract_session")

    anyio.run(run)


def test_login_with_email(tmp_path):
    """邮箱登录：等同用户名登录."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.post("/api/v1/auth/login", json={
                "username_or_email": "admin@test.com",
                "password": "pass123456",
            })
            assert resp.status_code == 200
            assert resp.json()["user"]["username"] == "admin"

    anyio.run(run)


def test_login_wrong_password(tmp_path):
    """密码错误 → 401."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.post("/api/v1/auth/login", json={
                "username_or_email": "admin",
                "password": "wrong",
            })
            assert resp.status_code == 401

    anyio.run(run)


def test_login_nonexistent_user(tmp_path):
    """不存在的用户 → 401."""
    settings = make_settings(tmp_path)
    make_repo(settings)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.post("/api/v1/auth/login", json={
                "username_or_email": "ghost",
                "password": "pass123456",
            })
            assert resp.status_code == 401

    anyio.run(run)


def test_login_disabled_user(tmp_path):
    """禁用用户无法登录 → 401."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    admin = seed_admin(repo)
    repo.update_user(admin["id"], {"is_active": False})
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.post("/api/v1/auth/login", json={
                "username_or_email": "admin",
                "password": "pass123456",
            })
            assert resp.status_code == 401

    anyio.run(run)


def test_me_authenticated(tmp_path):
    """已登录用户 GET /me → 返回自身信息."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.get("/api/v1/auth/me",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["user"]["username"] == "admin"

    anyio.run(run)


def test_me_requires_auth(tmp_path):
    """未登录 GET /me → 401."""
    settings = make_settings(tmp_path)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            resp = await client.get("/api/v1/auth/me")
            assert resp.status_code == 401

    anyio.run(run)


def test_register_requires_admin(tmp_path):
    """管理员创建用户成功."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.post("/api/v1/auth/register", json={
                "username": "newuser",
                "email": "new@test.com",
                "password": "pass123456",
                "role": "handler",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["user"]["username"] == "newuser"

    anyio.run(run)


def test_register_duplicate_username(tmp_path):
    """重复用户名 → 409."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            # 第一次成功
            await client.post("/api/v1/auth/register", json={
                "username": "dup", "email": "a@test.com",
                "password": "pass123456", "role": "handler",
            }, cookies={"contract_session": cookie})
            # 第二次重名
            resp = await client.post("/api/v1/auth/register", json={
                "username": "dup", "email": "b@test.com",
                "password": "pass123456", "role": "handler",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 409

    anyio.run(run)


def test_register_requires_admin_role(tmp_path):
    """非管理员注册 → 403."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            resp = await client.post("/api/v1/auth/register", json={
                "username": "hacker", "email": "h@ck.com",
                "password": "pass123456", "role": "admin",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 403

    anyio.run(run)


def test_logout(tmp_path):
    """登出后 /me 返回 401."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            # 登出
            resp = await client.post("/api/v1/auth/logout",
                                     cookies={"contract_session": cookie})
            assert resp.status_code == 200
            # 然后用旧 cookie 应不能访问
            resp2 = await client.get("/api/v1/auth/me",
                                     cookies={"contract_session": cookie})
            assert resp2.status_code == 401

    anyio.run(run)
