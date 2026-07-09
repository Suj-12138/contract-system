"""管理员路由测试 — P5 Task 29: 用户管理 + 统计看板."""
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


def test_list_users_requires_admin(tmp_path):
    """非管理员不能查看用户列表."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            resp = await client.get("/api/v1/admin/users",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 403

    anyio.run(run)


def test_list_users(tmp_path):
    """管理员查看用户列表."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.get("/api/v1/admin/users",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            users = resp.json()["users"]
            assert len(users) >= 2  # admin + handler

    anyio.run(run)


def test_create_user(tmp_path):
    """管理员创建用户."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.post("/api/v1/admin/users", json={
                "username": "newguy",
                "email": "newguy@test.com",
                "password": "pass123456",
                "role": "handler",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["user"]["username"] == "newguy"

    anyio.run(run)


def test_create_user_duplicate(tmp_path):
    """重复用户名 → 409."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            # 第一次
            await client.post("/api/v1/admin/users", json={
                "username": "dupuser", "email": "a@t.com",
                "password": "pass123456", "role": "handler",
            }, cookies={"contract_session": cookie})
            # 第二次
            resp = await client.post("/api/v1/admin/users", json={
                "username": "dupuser", "email": "b@t.com",
                "password": "pass123456", "role": "handler",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 409

    anyio.run(run)


def test_toggle_user_status(tmp_path):
    """启用/禁用用户."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")

            # 禁用
            resp = await client.patch(
                f"/api/v1/admin/users/{handler['id']}/status",
                json={"is_active": False},
                cookies={"contract_session": cookie},
            )
            assert resp.status_code == 200
            assert resp.json()["user"]["is_active"] is False

            # 重新启用
            resp = await client.patch(
                f"/api/v1/admin/users/{handler['id']}/status",
                json={"is_active": True},
                cookies={"contract_session": cookie},
            )
            assert resp.status_code == 200
            assert resp.json()["user"]["is_active"] is True

    anyio.run(run)


def test_get_stats(tmp_path):
    """管理员查看数据看板."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.get("/api/v1/admin/stats",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            data = resp.json()
            # 统计字段存在
            assert "total_contracts" in data or "contract_count" in data or "total_users" in data

    anyio.run(run)


def test_get_stats_requires_admin(tmp_path):
    """非管理员不能看数据看板."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            resp = await client.get("/api/v1/admin/stats",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 403

    anyio.run(run)
