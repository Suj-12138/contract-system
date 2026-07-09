"""合同路由."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_store
from app.api.errors import error, not_found
from app.repositories.json_repository import JsonRepository
from app.schemas.contracts import (
    ContractCreate,
    ContractDetailResponse,
    ContractListResponse,
    ContractResponse,
    ContractUpdate,
)
from app.services.contract_service import ContractService
from app.storage.json_store import JsonFileStore

router = APIRouter(prefix="/api/v1/contracts", tags=["contracts"])


def get_contract_service(store: JsonFileStore = Depends(get_store)) -> ContractService:
    return ContractService(JsonRepository(store), store)


@router.get("/")
def list_contracts(
    status: str | None = None,
    q: str | None = None,
    page: int = 1,
    page_size: int = 20,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """合同列表（支持分页）."""
    if page < 1:
        page = 1
    if page_size < 1 or page_size > 100:
        page_size = 20
    all_contracts = svc.list(user["id"], user["role"], status, q)
    total = len(all_contracts)
    total_pages = (total + page_size - 1) // page_size
    start = (page - 1) * page_size
    end = start + page_size
    contracts = all_contracts[start:end]
    return ContractListResponse(
        contracts=[ContractResponse(**c) for c in contracts],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    ).model_dump()


@router.post("/")
def create_contract(
    body: ContractCreate,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """创建合同."""
    if user["role"] != "handler":
        error("FORBIDDEN", "仅经办人可创建合同", 403)
    # 验证两级审批人不能相同
    if body.approver_1_id == body.approver_2_id:
        error("VALIDATION_ERROR", "两级审批人不能是同一个人", 422)
    # 验证审批人是否存在且角色正确
    repo = JsonRepository(svc._store)
    for approver_id in [body.approver_1_id, body.approver_2_id]:
        approver = repo.find_user_by_id(approver_id)
        if not approver or approver["role"] != "approver":
            error("VALIDATION_ERROR", f"审批人 {approver_id} 不存在或角色不正确", 422)

    contract = svc.create(user["id"], body.model_dump())
    return {"contract": ContractResponse(**contract).model_dump()}


@router.get("/{contract_id}")
def get_contract(
    contract_id: str,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """合同详情."""
    result = svc.get_detail(contract_id, user["id"], user["role"])
    if result == "not_found":
        not_found("合同")
    if result == "forbidden":
        error("FORBIDDEN", "无权访问此合同", 403)
    return ContractDetailResponse(
        contract=ContractResponse(**result["contract"]),
        approvals=[
            {
                "id": a["id"],
                "contract_id": a["contract_id"],
                "level": a["level"],
                "approver_id": a["approver_id"],
                "decision": a["decision"],
                "comment": a.get("comment"),
                "decided_at": a.get("decided_at"),
            }
            for a in result["approvals"]
        ],
        audit_logs=[
            {
                "id": l["id"],
                "user_id": l["user_id"],
                "action": l["action"],
                "target_type": l["target_type"],
                "target_id": l["target_id"],
                "detail": l["detail"],
                "created_at": l["created_at"],
            }
            for l in result["audit_logs"]
        ],
    ).model_dump()


@router.put("/{contract_id}")
def update_contract(
    contract_id: str,
    body: ContractUpdate,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """编辑合同."""
    result = svc.update(contract_id, user["id"], body.model_dump(exclude_unset=True))
    if result == "not_found":
        not_found("合同")
    if result == "not_owner":
        error("FORBIDDEN", "仅经办人可编辑合同", 403)
    if result == "invalid_status":
        error("INVALID_TRANSITION", "仅草稿或已驳回状态可编辑", 409)
    return {"contract": ContractResponse(**result).model_dump()}


@router.post("/{contract_id}/submit")
def submit_contract(
    contract_id: str,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """提交审批."""
    result = svc.submit(contract_id, user["id"])
    if result == "not_found":
        not_found("合同")
    if result == "not_owner":
        error("FORBIDDEN", "仅经办人可提交审批", 403)
    if result == "invalid_status":
        error("INVALID_TRANSITION", "仅草稿或已驳回状态可提交", 409)
    return result


@router.post("/{contract_id}/sign")
def sign_contract(
    contract_id: str,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """确认签订."""
    result = svc.sign(contract_id, user["id"])
    if result == "not_found":
        not_found("合同")
    if result == "not_owner":
        error("FORBIDDEN", "仅经办人可确认签订", 403)
    if result == "invalid_status":
        error("INVALID_TRANSITION", "仅已通过状态可签订", 409)
    return result


@router.post("/{contract_id}/archive")
def archive_contract(
    contract_id: str,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """归档."""
    result = svc.archive(contract_id, user["id"], user["role"])
    if result == "not_found":
        not_found("合同")
    if result == "forbidden":
        error("FORBIDDEN", "仅经办人或管理员可归档", 403)
    if result == "invalid_status":
        error("INVALID_TRANSITION", "仅已到期或已续签状态可归档", 409)
    return result


@router.post("/{contract_id}/renew")
def renew_contract(
    contract_id: str,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
    expires_at: str | None = None,
):
    """续签合同."""
    result = svc.renew(contract_id, user["id"], expires_at)
    if result == "not_found":
        not_found("合同")
    if result == "not_owner":
        error("FORBIDDEN", "仅经办人可续签合同", 403)
    if result == "invalid_status":
        error("INVALID_TRANSITION", "仅履行中状态可续签", 409)
    return result


@router.delete("/{contract_id}")
def delete_contract(
    contract_id: str,
    user: dict = Depends(get_current_user),
    svc: ContractService = Depends(get_contract_service),
):
    """删除草稿合同."""
    result = svc.delete(contract_id, user["id"])
    if result == "not_found":
        not_found("合同")
    if result == "not_owner":
        error("FORBIDDEN", "仅经办人可删除合同", 403)
    if result == "invalid_status":
        error("INVALID_TRANSITION", "仅草稿状态可删除", 409)
    return result