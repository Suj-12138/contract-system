"""审批 + 消息路由测试 — P5 Task 29."""
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


async def _create_and_submit(client, h_cookie, approver1_id, approver2_id):
    """辅助: 创建合同并提交审批，返回合同ID."""
    resp = await client.post("/api/v1/contracts/", json={
        "title": "审批测试合同",
        "counterparty": "测试公司",
        "approver_1_id": approver1_id,
        "approver_2_id": approver2_id,
    }, cookies={"contract_session": h_cookie})
    cid = resp.json()["contract"]["id"]
    await client.post(f"/api/v1/contracts/{cid}/submit",
                      cookies={"contract_session": h_cookie})
    return cid


def test_approve_level1_then_level2(tmp_path):
    """两级审批通过：一级→二级."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            # 一级审批通过
            a1_cookie = await login(client, "approver1", "pass123456")
            resp = await client.post(
                f"/api/v1/contracts/{cid}/approve",
                json={"comment": "一级同意"},
                cookies={"contract_session": a1_cookie},
            )
            assert resp.status_code == 200

            # 二级审批通过
            a2_cookie = await login(client, "approver2", "pass123456")
            resp = await client.post(
                f"/api/v1/contracts/{cid}/approve",
                json={"comment": "二级同意"},
                cookies={"contract_session": a2_cookie},
            )
            assert resp.status_code == 200

    anyio.run(run)


def test_approve_wrong_approver(tmp_path):
    """越级审批 → 409."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            # approver2 尝试审批一级节点 → 应被拒绝
            a2_cookie = await login(client, "approver2", "pass123456")
            resp = await client.post(
                f"/api/v1/contracts/{cid}/approve",
                json={"comment": "越级审批"},
                cookies={"contract_session": a2_cookie},
            )
            assert resp.status_code == 409

    anyio.run(run)


def test_reject_contract(tmp_path):
    """审批驳回."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            # 一级审批驳回
            a1_cookie = await login(client, "approver1", "pass123456")
            resp = await client.post(
                f"/api/v1/contracts/{cid}/reject",
                json={"comment": "不符合要求"},
                cookies={"contract_session": a1_cookie},
            )
            assert resp.status_code == 200

            # 验证合同状态变为 rejected
            detail = await client.get(f"/api/v1/contracts/{cid}",
                                      cookies={"contract_session": h_cookie})
            assert detail.json()["contract"]["status"] == "rejected"

    anyio.run(run)


def test_get_approvals(tmp_path):
    """查询审批记录."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            resp = await client.get(
                f"/api/v1/contracts/{cid}/approvals",
                cookies={"contract_session": h_cookie},
            )
            assert resp.status_code == 200
            approvals = resp.json()["approvals"]
            assert len(approvals) == 2
            assert approvals[0]["level"] == 1
            assert approvals[1]["level"] == 2

    anyio.run(run)


def test_messages_list(tmp_path):
    """消息列表."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            # 两级审批通过（会发消息给经办人）
            a1_cookie = await login(client, "approver1", "pass123456")
            await client.post(f"/api/v1/contracts/{cid}/approve",
                            json={"comment": "通过"},
                            cookies={"contract_session": a1_cookie})
            a2_cookie = await login(client, "approver2", "pass123456")
            await client.post(f"/api/v1/contracts/{cid}/approve",
                            json={"comment": "通过"},
                            cookies={"contract_session": a2_cookie})

            # 查消息
            resp = await client.get("/api/v1/messages",
                                    cookies={"contract_session": h_cookie})
            assert resp.status_code == 200
            data = resp.json()
            assert data["total"] >= 1

    anyio.run(run)


def test_messages_unread_count(tmp_path):
    """未读消息数."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            # 两级审批通过
            a1_cookie = await login(client, "approver1", "pass123456")
            await client.post(f"/api/v1/contracts/{cid}/approve",
                            json={"comment": "通过"},
                            cookies={"contract_session": a1_cookie})
            a2_cookie = await login(client, "approver2", "pass123456")
            await client.post(f"/api/v1/contracts/{cid}/approve",
                            json={"comment": "通过"},
                            cookies={"contract_session": a2_cookie})

            resp = await client.get("/api/v1/messages/unread-count",
                                    cookies={"contract_session": h_cookie})
            assert resp.status_code == 200
            # 两级审批通过后有通知
            assert resp.json()["count"] >= 1

    anyio.run(run)


def test_mark_message_read(tmp_path):
    """标记消息为已读."""
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
            cid = await _create_and_submit(client, h_cookie,
                                           approver1["id"], approver2["id"])

            # 一级审批通过（会产生消息）
            a1_cookie = await login(client, "approver1", "pass123456")
            await client.post(f"/api/v1/contracts/{cid}/approve",
                            json={"comment": "通过"},
                            cookies={"contract_session": a1_cookie})

            # 获取消息列表
            msg_resp = await client.get("/api/v1/messages",
                                        cookies={"contract_session": h_cookie})
            messages = msg_resp.json()["messages"]
            if messages:
                msg_id = messages[0]["id"]
                resp = await client.patch(f"/api/v1/messages/{msg_id}/read",
                                          cookies={"contract_session": h_cookie})
                assert resp.status_code == 200
                assert resp.json()["message"]["is_read"] is True

    anyio.run(run)
