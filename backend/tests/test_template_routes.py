"""模板路由测试 — P5 Task 29: CRUD + 启停."""
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


def test_list_templates_admin(tmp_path):
    """管理员查看全部模板（含停用的）."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            # 创建两个模板
            for i in range(2):
                await client.post("/api/v1/templates/", json={
                    "name": f"模板{i}",
                    "description": f"描述{i}",
                    "fields_json": [
                        {"label": "甲方", "type": "text", "required": True},
                    ],
                }, cookies={"contract_session": cookie})

            resp = await client.get("/api/v1/templates/",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert len(resp.json()["templates"]) == 2

    anyio.run(run)


def test_list_templates_handler_sees_active(tmp_path):
    """经办人只看启用的模板."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    admin = seed_admin(repo)
    handler = seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            admin_cookie = await login(client, "admin", "pass123456")
            # 创建并停用一个模板
            create_resp = await client.post("/api/v1/templates/", json={
                "name": "活跃模板",
                "fields_json": [{"label": "甲", "type": "text", "required": True}],
            }, cookies={"contract_session": admin_cookie})
            tid = create_resp.json()["template"]["id"]

            await client.patch(f"/api/v1/templates/{tid}/status", json={
                "is_active": False,
            }, cookies={"contract_session": admin_cookie})

            # 经办人只能看到启用的（当前 0 个）
            h_cookie = await login(client, "handler1", "pass123456")
            resp = await client.get("/api/v1/templates/",
                                    cookies={"contract_session": h_cookie})
            assert resp.status_code == 200
            templates = resp.json()["templates"]
            assert all(t["is_active"] for t in templates)

    anyio.run(run)


def test_create_template_requires_admin(tmp_path):
    """非管理员不能创建模板."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            resp = await client.post("/api/v1/templates/", json={
                "name": "非法模板",
                "fields_json": [],
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 403

    anyio.run(run)


def test_update_template(tmp_path):
    """编辑模板."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            create_resp = await client.post("/api/v1/templates/", json={
                "name": "旧名",
                "description": "旧描述",
                "fields_json": [{"label": "合同金额", "type": "number", "required": True}],
            }, cookies={"contract_session": cookie})
            tid = create_resp.json()["template"]["id"]

            resp = await client.put(f"/api/v1/templates/{tid}", json={
                "name": "新名",
                "description": "新描述",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["template"]["name"] == "新名"

    anyio.run(run)


def test_toggle_template_status(tmp_path):
    """启用/停用模板."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            create_resp = await client.post("/api/v1/templates/", json={
                "name": "开关测试模板",
                "fields_json": [{"label": "金额", "type": "number", "required": True}],
            }, cookies={"contract_session": cookie})
            tid = create_resp.json()["template"]["id"]

            # 停用
            resp = await client.patch(f"/api/v1/templates/{tid}/status", json={
                "is_active": False,
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["template"]["is_active"] is False

            # 启用
            resp = await client.patch(f"/api/v1/templates/{tid}/status", json={
                "is_active": True,
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["template"]["is_active"] is True

    anyio.run(run)


def test_get_template_not_found(tmp_path):
    """不存在的模板 → 404."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.put("/api/v1/templates/nonexistent-id", json={
                "name": "不存在",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 404

    anyio.run(run)
