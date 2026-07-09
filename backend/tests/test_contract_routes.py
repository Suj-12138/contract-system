"""合同路由测试 — P5 Task 29: CRUD + 状态流转."""
import anyio

from app.config import get_settings
from app.main import app

from .conftest import (
    login,
    make_client,
    make_repo,
    make_settings,
    seed_admin,
    seed_approver,
    seed_approver2,
    seed_handler,
)


def test_create_contract(tmp_path):
    """经办人创建合同成功."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            resp = await client.post("/api/v1/contracts/", json={
                "title": "测试合同",
                "counterparty": "甲方公司",
                "amount": 100000.0,
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            data = resp.json()
            assert data["contract"]["title"] == "测试合同"
            assert data["contract"]["status"] == "draft"
            assert data["contract"]["handler_id"] == handler["id"]

    anyio.run(run)


def test_create_contract_requires_handler(tmp_path):
    """管理员不能创建合同."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "admin", "pass123456")
            resp = await client.post("/api/v1/contracts/", json={
                "title": "管理员不能创建合同",
                "counterparty": "对方",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 403

    anyio.run(run)


def test_list_contracts_handler(tmp_path):
    """经办人查看自己的合同列表."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            # 创建两笔合同
            for i in range(2):
                await client.post("/api/v1/contracts/", json={
                    "title": f"合同{i}",
                    "counterparty": f"公司{i}",
                    "approver_1_id": approver1["id"],
                    "approver_2_id": approver2["id"],
                }, cookies={"contract_session": cookie})
            resp = await client.get("/api/v1/contracts/",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 2

    anyio.run(run)


def test_get_contract_detail(tmp_path):
    """查看合同详情（含审批记录和审计日志）."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            create_resp = await client.post("/api/v1/contracts/", json={
                "title": "详情测试合同",
                "counterparty": "测试公司",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})
            contract_id = create_resp.json()["contract"]["id"]

            resp = await client.get(f"/api/v1/contracts/{contract_id}",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            data = resp.json()
            assert data["contract"]["title"] == "详情测试合同"
            assert "approvals" in data
            assert "audit_logs" in data
            assert len(data["audit_logs"]) >= 1  # 至少有一条创建日志

    anyio.run(run)


def test_get_contract_forbidden(tmp_path):
    """经办人不能看别人的合同."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler1 = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)

    # 再创建一个 handler2
    from app.domain.enums import UserRole
    from app.domain.models import make_user
    from app.security.passwords import hash_password
    handler2 = make_user(repo._store, "handler2", "h2@test.com",
                         hash_password("pass123456"), UserRole.HANDLER)
    repo.create_user(handler2)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            # handler1 创建合同
            c1 = await login(client, "handler1", "pass123456")
            create_resp = await client.post("/api/v1/contracts/", json={
                "title": "handler1 的合同",
                "counterparty": "公司A",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": c1})
            contract_id = create_resp.json()["contract"]["id"]

            # handler2 尝试查看
            c2 = await login(client, "handler2", "pass123456")
            resp = await client.get(f"/api/v1/contracts/{contract_id}",
                                    cookies={"contract_session": c2})
            assert resp.status_code == 403

    anyio.run(run)


def test_update_contract_draft(tmp_path):
    """草稿状态可编辑."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            create_resp = await client.post("/api/v1/contracts/", json={
                "title": "旧标题",
                "counterparty": "公司",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})
            contract_id = create_resp.json()["contract"]["id"]

            resp = await client.put(f"/api/v1/contracts/{contract_id}", json={
                "title": "新标题",
            }, cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["contract"]["title"] == "新标题"

    anyio.run(run)


def test_submit_contract(tmp_path):
    """提交审批：草稿 → 审批中."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            create_resp = await client.post("/api/v1/contracts/", json={
                "title": "待提交合同",
                "counterparty": "公司",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})
            contract_id = create_resp.json()["contract"]["id"]

            resp = await client.post(f"/api/v1/contracts/{contract_id}/submit",
                                     cookies={"contract_session": cookie})
            assert resp.status_code == 200
            assert resp.json()["message"] == "已提交审批"

            # 验证状态已变
            detail = await client.get(f"/api/v1/contracts/{contract_id}",
                                      cookies={"contract_session": cookie})
            assert detail.json()["contract"]["status"] == "review"

    anyio.run(run)


def test_submit_non_owner(tmp_path):
    """非经办人不能提交审批."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            # handler1 创建合同
            h_cookie = await login(client, "handler1", "pass123456")
            create_resp = await client.post("/api/v1/contracts/", json={
                "title": "h1 合同",
                "counterparty": "公司",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": h_cookie})
            contract_id = create_resp.json()["contract"]["id"]

            # approver 尝试提交
            a_cookie = await login(client, "approver1", "pass123456")
            resp = await client.post(f"/api/v1/contracts/{contract_id}/submit",
                                     cookies={"contract_session": a_cookie})
            assert resp.status_code == 403

    anyio.run(run)


def test_sign_contract_full_flow(tmp_path):
    """签订流程：需要审批通过后才能签订."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            # 1. 创建合同
            h_cookie = await login(client, "handler1", "pass123456")
            create_resp = await client.post("/api/v1/contracts/", json={
                "title": "签订测试",
                "counterparty": "公司",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": h_cookie})
            contract_id = create_resp.json()["contract"]["id"]

            # 2. 提交审批
            await client.post(f"/api/v1/contracts/{contract_id}/submit",
                            cookies={"contract_session": h_cookie})

            # 3. 审批通过（两级）
            a1_cookie = await login(client, "approver1", "pass123456")
            await client.post(f"/api/v1/contracts/{contract_id}/approve",
                            json={"comment": "同意"},
                            cookies={"contract_session": a1_cookie})

            a2_cookie = await login(client, "approver2", "pass123456")
            await client.post(f"/api/v1/contracts/{contract_id}/approve",
                            json={"comment": "同意"},
                            cookies={"contract_session": a2_cookie})

            # 4. 签订
            resp = await client.post(f"/api/v1/contracts/{contract_id}/sign",
                                     cookies={"contract_session": h_cookie})
            assert resp.status_code == 200

            # 5. 验证状态已变为 active（签订后自动进入履行中）
            detail = await client.get(f"/api/v1/contracts/{contract_id}",
                                      cookies={"contract_session": h_cookie})
            assert detail.json()["contract"]["status"] == "active"

    anyio.run(run)


def test_archive_contract(tmp_path):
    """归档：需要 expired/renewed 状态."""
    from app.domain.models import make_contract
    from app.domain.enums import ContractStatus

    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            h_cookie = await login(client, "handler1", "pass123456")
            # 直接用仓库创建已到期合同
            contract = make_contract(
                repo._store, "到期合同", "公司",
                handler["id"], approver1["id"], approver2["id"],
            )
            repo.create_contract(contract)
            # 手动改状态为 expired
            repo.update_contract(contract["id"], {"status": ContractStatus.EXPIRED.value})

            resp = await client.post(
                f"/api/v1/contracts/{contract['id']}/archive",
                cookies={"contract_session": h_cookie},
            )
            assert resp.status_code == 200
            assert resp.json()["message"] == "已归档"

    anyio.run(run)


def test_contract_search(tmp_path):
    """合同搜索：按标题/对方名称模糊匹配."""
    settings = make_settings(tmp_path)
    repo = make_repo(settings)
    seed_admin(repo)
    handler = seed_handler(repo)
    approver1 = seed_approver(repo)
    approver2 = seed_approver2(repo)
    app.dependency_overrides[get_settings] = lambda: settings

    async def run():
        async with await make_client(app) as client:
            cookie = await login(client, "handler1", "pass123456")
            await client.post("/api/v1/contracts/", json={
                "title": "软件开发合同",
                "counterparty": "百度科技",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})
            await client.post("/api/v1/contracts/", json={
                "title": "硬件采购合同",
                "counterparty": "华为技术",
                "approver_1_id": approver1["id"],
                "approver_2_id": approver2["id"],
            }, cookies={"contract_session": cookie})

            # 搜索"软件"
            resp = await client.get("/api/v1/contracts/?q=软件",
                                    cookies={"contract_session": cookie})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] == 1
            assert data["contracts"][0]["title"] == "软件开发合同"

    anyio.run(run)
