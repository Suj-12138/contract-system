"""JSON 文件仓储实现 — 面向协议的具体适配器."""
from app.storage.json_store import JsonFileStore


class JsonRepository:
    """统一仓储，封装所有实体操作."""

    def __init__(self, store: JsonFileStore) -> None:
        self._store = store

    # ── 用户 ──
    def find_user_by_username(self, username: str) -> dict | None:
        data = self._store.read()
        for u in data["users"]:
            if u["username"] == username:
                return u
        return None

    def find_user_by_email(self, email: str) -> dict | None:
        normalized = email.lower()
        data = self._store.read()
        for u in data["users"]:
            if u["email"] == normalized:
                return u
        return None

    def find_user_by_id(self, user_id: str) -> dict | None:
        data = self._store.read()
        for u in data["users"]:
            if u["id"] == user_id:
                return u
        return None

    def list_users(self) -> list[dict]:
        return self._store.read()["users"]

    def list_users_by_role(self, role: str) -> list[dict]:
        return [u for u in self._store.read()["users"] if u["role"] == role]

    def create_user(self, user: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["users"].append(user)
            return user
        return self._store.transaction(mutator)

    def update_user(self, user_id: str, updates: dict) -> dict | None:
        def mutator(data: dict) -> dict | None:
            for i, u in enumerate(data["users"]):
                if u["id"] == user_id:
                    data["users"][i].update(updates)
                    return data["users"][i]
            return None
        return self._store.transaction(mutator)

    # ── 合同 ──
    def find_contract_by_id(self, contract_id: str) -> dict | None:
        data = self._store.read()
        for c in data["contracts"]:
            if c["id"] == contract_id:
                return c
        return None

    def list_contracts_by_handler(self, handler_id: str, status: str | None = None) -> list[dict]:
        data = self._store.read()
        result = [c for c in data["contracts"] if c["handler_id"] == handler_id]
        if status:
            result = [c for c in result if c["status"] == status]
        return sorted(result, key=lambda c: c["updated_at"], reverse=True)

    def list_all_contracts(self, status: str | None = None) -> list[dict]:
        data = self._store.read()
        result = data["contracts"]
        if status:
            result = [c for c in result if c["status"] == status]
        return sorted(result, key=lambda c: c["updated_at"], reverse=True)

    def list_contracts_for_approver(self, approver_id: str) -> list[dict]:
        data = self._store.read()
        contract_ids = set()
        for ar in data["approval_records"]:
            if ar["approver_id"] == approver_id and ar["decision"] == "pending":
                contract_ids.add(ar["contract_id"])
        return [c for c in data["contracts"] if c["id"] in contract_ids]

    def create_contract(self, contract: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["contracts"].append(contract)
            return contract
        return self._store.transaction(mutator)

    def update_contract(self, contract_id: str, updates: dict) -> dict | None:
        def mutator(data: dict) -> dict | None:
            for i, c in enumerate(data["contracts"]):
                if c["id"] == contract_id:
                    data["contracts"][i].update(updates)
                    return data["contracts"][i]
            return None
        return self._store.transaction(mutator)

    def search_contracts(self, keyword: str, user_id: str | None, role: str | None) -> list[dict]:
        data = self._store.read()
        kw = keyword.lower()
        results = [c for c in data["contracts"]
                   if kw in c["title"].lower() or kw in c["counterparty"].lower()]
        if role == "handler" and user_id:
            results = [c for c in results if c["handler_id"] == user_id]
        return sorted(results, key=lambda c: c["updated_at"], reverse=True)

    # ── 审批记录 ──
    def find_approvals_by_contract(self, contract_id: str) -> list[dict]:
        data = self._store.read()
        return sorted(
            [a for a in data["approval_records"] if a["contract_id"] == contract_id],
            key=lambda a: a["level"]
        )

    def create_approval_record(self, record: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["approval_records"].append(record)
            return record
        return self._store.transaction(mutator)

    def update_approval_record(self, record_id: str, updates: dict) -> dict | None:
        def mutator(data: dict) -> dict | None:
            for i, a in enumerate(data["approval_records"]):
                if a["id"] == record_id:
                    data["approval_records"][i].update(updates)
                    return data["approval_records"][i]
            return None
        return self._store.transaction(mutator)

    # ── 消息 ──
    def list_messages_by_user(self, user_id: str, is_read: bool | None = None) -> list[dict]:
        data = self._store.read()
        result = [m for m in data["messages"] if m["user_id"] == user_id]
        if is_read is not None:
            result = [m for m in result if m["is_read"] == is_read]
        return sorted(result, key=lambda m: m["created_at"], reverse=True)

    def create_message(self, message: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["messages"].append(message)
            return message
        return self._store.transaction(mutator)

    def mark_message_read(self, message_id: str) -> dict | None:
        def mutator(data: dict) -> dict | None:
            for i, m in enumerate(data["messages"]):
                if m["id"] == message_id:
                    data["messages"][i]["is_read"] = True
                    return data["messages"][i]
            return None
        return self._store.transaction(mutator)

    def unread_message_count(self, user_id: str) -> int:
        data = self._store.read()
        return sum(1 for m in data["messages"] if m["user_id"] == user_id and not m["is_read"])

    # ── 模板 ──
    def list_active_templates(self) -> list[dict]:
        return [t for t in self._store.read()["templates"] if t["is_active"]]

    def list_all_templates(self) -> list[dict]:
        return self._store.read()["templates"]

    def find_template_by_id(self, template_id: str) -> dict | None:
        data = self._store.read()
        for t in data["templates"]:
            if t["id"] == template_id:
                return t
        return None

    def create_template(self, template: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["templates"].append(template)
            return template
        return self._store.transaction(mutator)

    def update_template(self, template_id: str, updates: dict) -> dict | None:
        def mutator(data: dict) -> dict | None:
            for i, t in enumerate(data["templates"]):
                if t["id"] == template_id:
                    data["templates"][i].update(updates)
                    return data["templates"][i]
            return None
        return self._store.transaction(mutator)

    # ── 审计日志 ──
    def create_audit_log(self, log: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["audit_logs"].append(log)
            return log
        return self._store.transaction(mutator)

    def list_audit_logs_by_target(self, target_type: str, target_id: str) -> list[dict]:
        data = self._store.read()
        return sorted(
            [l for l in data["audit_logs"] if l["target_type"] == target_type and l["target_id"] == target_id],
            key=lambda l: l["created_at"]
        )

    # ── 会话 ──
    def create_session(self, session: dict) -> dict:
        def mutator(data: dict) -> dict:
            data["sessions"].append(session)
            return session
        return self._store.transaction(mutator)

    def destroy_sessions_by_user(self, user_id: str) -> None:
        def mutator(data: dict) -> None:
            data["sessions"] = [s for s in data["sessions"] if s["user_id"] != user_id]
            return None
        self._store.transaction(mutator)

    def destroy_session_by_token(self, token_hash: str) -> None:
        def mutator(data: dict) -> None:
            data["sessions"] = [s for s in data["sessions"] if s["token_hash"] != token_hash]
            return None
        self._store.transaction(mutator)
