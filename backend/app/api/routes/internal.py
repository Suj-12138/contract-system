from fastapi import APIRouter, Depends, Query
from app.api.dependencies import get_store, get_current_user, require_approver
from app.api.errors import error, not_found, forbidden
from app.repositories.json_repository import JsonRepository
from app.services.approval_service import ApprovalService
from app.services.message_service import MessageService

router = APIRouter(tags=["internal"])


def get_approval_svc(store=Depends(get_store)) -> ApprovalService:
    return ApprovalService(JsonRepository(store))


def get_message_svc(store=Depends(get_store)) -> MessageService:
    return MessageService(JsonRepository(store))


# ── 审批 ──

@router.get("/api/v1/approvals/pending")
def list_pending_approvals(user: dict = Depends(get_current_user),
                           svc=Depends(get_approval_svc)):
    contracts = svc.get_pending_for_approver(user["id"])
    return {"contracts": contracts}


@router.get("/api/v1/contracts/{contract_id}/approvals")
def get_approvals(contract_id: str, user: dict = Depends(get_current_user),
                  svc=Depends(get_approval_svc)):
    approvals = svc.get_approvals(contract_id)
    return {"approvals": approvals}


@router.post("/api/v1/contracts/{contract_id}/approve")
def approve(contract_id: str, body: dict = {},
            user: dict = Depends(get_current_user), svc=Depends(get_approval_svc)):
    if user["role"] != "approver":
        forbidden()
    result = svc.approve(contract_id, user, body.get("comment", ""))
    if result == "not_found":
        not_found("合同")
    if result == "not_your_turn":
        error("INVALID_TRANSITION", "当前不是您的审批节点", 409)
    if result == "level1_not_done":
        error("INVALID_TRANSITION", "一级审批尚未通过", 409)
    if result == "all_decided":
        error("INVALID_TRANSITION", "该合同已完成审批", 409)
    return {"contract": result}


@router.post("/api/v1/contracts/{contract_id}/reject")
def reject(contract_id: str, body: dict = {},
           user: dict = Depends(get_current_user), svc=Depends(get_approval_svc)):
    if user["role"] != "approver":
        forbidden()
    result = svc.reject(contract_id, user, body.get("comment", ""))
    if result == "not_found":
        not_found("合同")
    if result == "not_your_turn":
        error("INVALID_TRANSITION", "当前不是您的审批节点", 409)
    if result == "all_decided":
        error("INVALID_TRANSITION", "该合同已完成审批", 409)
    return {"contract": result}


# ── 消息 ──

@router.get("/api/v1/messages")
def list_messages(is_read: bool | None = Query(None),
                  user: dict = Depends(get_current_user), svc=Depends(get_message_svc)):
    messages = svc.list_for_user(user["id"], is_read)
    return {"messages": messages, "total": len(messages)}


@router.get("/api/v1/messages/unread-count")
def unread_count(user: dict = Depends(get_current_user), svc=Depends(get_message_svc)):
    return {"count": svc.unread_count(user["id"])}


@router.patch("/api/v1/messages/{message_id}/read")
def mark_read(message_id: str, user: dict = Depends(get_current_user),
              svc=Depends(get_message_svc)):
    result = svc.mark_read(message_id, user["id"])
    if result == "not_found":
        not_found("消息")
    return {"message": result}
