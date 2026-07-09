from app.domain.enums import ContractStatus, ApprovalDecision
from app.domain.models import make_approval_record, make_message, make_audit_log
from app.repositories.json_repository import JsonRepository


class ApprovalService:
    def __init__(self, repo: JsonRepository):
        self.repo = repo

    def create_approval_records(self, contract: dict) -> None:
        """合同提交审批时创建两条审批记录."""
        r1 = make_approval_record(self.repo._store, contract["id"], 1, contract["approver_1_id"])
        r2 = make_approval_record(self.repo._store, contract["id"], 2, contract["approver_2_id"])
        self.repo.create_approval_record(r1)
        self.repo.create_approval_record(r2)

    def approve(self, contract_id: str, user: dict, comment: str = "") -> dict | str:
        contract = self.repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        records = sorted(self.repo.find_approvals_by_contract(contract_id), key=lambda r: r["level"])
        for r in records:
            if r["decision"] == ApprovalDecision.PENDING.value:
                if r["approver_id"] != user["id"]:
                    return "not_your_turn"
                if r["level"] == 2 and records[0]["decision"] != ApprovalDecision.APPROVED.value:
                    return "level1_not_done"
                self.repo.update_approval_record(r["id"], {
                    "decision": ApprovalDecision.APPROVED.value,
                    "comment": comment,
                    "decided_at": self.repo._store.utcnow(),
                })
                self._log(contract_id, user["id"], "approve", f"第{r['level']}级审批通过")
                # 检查是否两级都通过
                updated_records = self.repo.find_approvals_by_contract(contract_id)
                if all(ar["decision"] == ApprovalDecision.APPROVED.value for ar in updated_records):
                    self.repo.update_contract(contract_id, {
                        "status": ContractStatus.APPROVED.value,
                        "updated_at": self.repo._store.utcnow(),
                    })
                    self._log(contract_id, user["id"], "approve", "两级审批通过，合同已通过")
                    self._notify(contract, "审批通过", f"合同「{contract['title']}」已通过审批")
                return self.repo.find_contract_by_id(contract_id)
        return "all_decided"

    def reject(self, contract_id: str, user: dict, comment: str = "") -> dict | str:
        contract = self.repo.find_contract_by_id(contract_id)
        if not contract:
            return "not_found"
        records = sorted(self.repo.find_approvals_by_contract(contract_id), key=lambda r: r["level"])
        for r in records:
            if r["decision"] == ApprovalDecision.PENDING.value:
                if r["approver_id"] != user["id"]:
                    return "not_your_turn"
                self.repo.update_approval_record(r["id"], {
                    "decision": ApprovalDecision.REJECTED.value,
                    "comment": comment,
                    "decided_at": self.repo._store.utcnow(),
                })
                self.repo.update_contract(contract_id, {
                    "status": ContractStatus.REJECTED.value,
                    "updated_at": self.repo._store.utcnow(),
                })
                self._log(contract_id, user["id"], "reject", f"第{r['level']}级审批驳回")
                self._notify(contract, "审批驳回", f"合同「{contract['title']}」被驳回，请修改后重新提交")
                return self.repo.find_contract_by_id(contract_id)
        return "all_decided"

    def get_approvals(self, contract_id: str) -> list[dict]:
        return self.repo.find_approvals_by_contract(contract_id)

    def get_pending_for_approver(self, approver_id: str) -> list[dict]:
        return self.repo.list_contracts_for_approver(approver_id)

    def _log(self, contract_id: str, user_id: str, action: str, detail: str):
        log = make_audit_log(self.repo._store, user_id, action, "contract", contract_id, detail)
        self.repo.create_audit_log(log)

    def _notify(self, contract: dict, title: str, body: str):
        msg = make_message(self.repo._store, contract["handler_id"], title, body, contract["id"])
        self.repo.create_message(msg)
