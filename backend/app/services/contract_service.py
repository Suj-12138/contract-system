"""合同业务服务."""

from app.domain.enums import ContractStatus
from app.domain.models import make_contract, make_approval_record, make_audit_log
from app.repositories.json_repository import JsonRepository
from app.storage.json_store import JsonFileStore


class ContractService:
    """合同业务逻辑."""

    def __init__(self, repo: JsonRepository, store: JsonFileStore) -> None:
        self._repo = repo
        self._store = store

    def create(self, handler_id: str, data: dict) -> dict:
        """创建合同."""
        contract = make_contract(
            self._store,
            title=data["title"],
            counterparty=data["counterparty"],
            handler_id=handler_id,
            approver_1_id=data["approver_1_id"],
            approver_2_id=data["approver_2_id"],
            template_id=data.get("template_id"),
            content_json=data.get("content_json", {}),
            amount=data.get("amount"),
            expires_at=data.get("expires_at"),
        )
        self._repo.create_contract(contract)
        self._log(handler_id, "create_contract", contract["id"], "创建合同")
        return contract

    def update(self, contract_id: str, handler_id: str, updates: dict) -> dict | str:
        """编辑合同（仅草稿或已驳回状态）."""
        contract = self._repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        if contract["handler_id"] != handler_id:
            return "not_owner"
        status = ContractStatus(contract["status"])
        if status not in (ContractStatus.DRAFT, ContractStatus.REJECTED):
            return "invalid_status"

        updates["updated_at"] = self._store.utcnow()
        updated = self._repo.update_contract(contract_id, updates)
        self._log(handler_id, "update_contract", contract_id, "编辑合同")
        return updated

    def get_detail(self, contract_id: str, user_id: str, role: str) -> dict | str:
        """获取合同详情（含审批记录和操作历史）."""
        contract = self._repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        if not self._can_access(contract, user_id, role):
            return "forbidden"

        approvals = self._repo.find_approvals_by_contract(contract_id)
        audit_logs = self._repo.list_audit_logs_by_target("contract", contract_id)
        return {
            "contract": contract,
            "approvals": approvals,
            "audit_logs": audit_logs,
        }

    def list(self, user_id: str, role: str, status: str | None = None, keyword: str | None = None) -> list[dict]:
        """列出合同."""
        if keyword:
            return self._repo.search_contracts(keyword, user_id, role)
        if role == "admin":
            return self._repo.list_all_contracts(status)
        if role == "approver":
            return self._repo.list_contracts_for_approver(user_id)
        return self._repo.list_contracts_by_handler(user_id, status)

    def submit(self, contract_id: str, handler_id: str) -> dict | str:
        """提交审批."""
        contract = self._repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        if contract["handler_id"] != handler_id:
            return "not_owner"
        status = ContractStatus(contract["status"])
        if status not in (ContractStatus.DRAFT, ContractStatus.REJECTED):
            return "invalid_status"

        # 创建两条审批记录
        ar1 = make_approval_record(self._store, contract_id, 1, contract["approver_1_id"])
        ar2 = make_approval_record(self._store, contract_id, 2, contract["approver_2_id"])
        self._repo.create_approval_record(ar1)
        self._repo.create_approval_record(ar2)

        # 更新状态为审批中
        self._repo.update_contract(contract_id, {
            "status": ContractStatus.REVIEW.value,
            "updated_at": self._store.utcnow(),
        })
        self._log(handler_id, "submit_review", contract_id, "提交审批")
        return {"message": "已提交审批"}

    def sign(self, contract_id: str, handler_id: str) -> dict | str:
        """确认签订."""
        contract = self._repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        if contract["handler_id"] != handler_id:
            return "not_owner"
        if ContractStatus(contract["status"]) != ContractStatus.APPROVED:
            return "invalid_status"

        now = self._store.utcnow()
        self._repo.update_contract(contract_id, {
            "status": ContractStatus.SIGNED.value,
            "signed_at": now,
            "updated_at": now,
        })
        self._log(handler_id, "sign_contract", contract_id, "确认签订")

        # 签订后自动进入履行中状态
        self._repo.update_contract(contract_id, {
            "status": ContractStatus.ACTIVE.value,
            "updated_at": self._store.utcnow(),
        })
        self._log(handler_id, "activate_contract", contract_id, "合同进入履行中")
        return {"message": "已确认签订"}

    def archive(self, contract_id: str, user_id: str, role: str) -> dict | str:
        """归档."""
        contract = self._repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        status = ContractStatus(contract["status"])
        if status not in (ContractStatus.EXPIRED, ContractStatus.RENEWED):
            return "invalid_status"
        if role != "admin" and contract["handler_id"] != user_id:
            return "forbidden"

        self._repo.update_contract(contract_id, {
            "status": ContractStatus.ARCHIVED.value,
            "updated_at": self._store.utcnow(),
        })
        self._log(user_id, "archive_contract", contract_id, "归档合同")
        return {"message": "已归档"}

    def _can_access(self, contract: dict, user_id: str, role: str) -> bool:
        """判断用户是否可访问合同."""
        if role == "admin":
            return True
        if contract["handler_id"] == user_id:
            return True
        if contract["approver_1_id"] == user_id or contract["approver_2_id"] == user_id:
            return True
        return False

    def _log(self, user_id: str, action: str, target_id: str, detail: str) -> None:
        """记录审计日志."""
        log = make_audit_log(self._store, user_id, action, "contract", target_id, detail)
        self._repo.create_audit_log(log)