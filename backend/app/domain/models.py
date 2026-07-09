"""领域模型工厂函数."""

from app.domain.enums import ContractStatus, UserRole


def make_user(store, username: str, email: str, password_hash: str, role: UserRole) -> dict:
    return {
        "id": store.new_id(),
        "username": username,
        "email": email.lower(),
        "password_hash": password_hash,
        "role": role.value,
        "is_active": True,
        "created_at": store.utcnow(),
    }


def make_contract(store, title: str, counterparty: str, handler_id: str,
                  approver_1_id: str, approver_2_id: str,
                  template_id: str | None = None,
                  content_json: dict | None = None,
                  amount: float | None = None,
                  expires_at: str | None = None) -> dict:
    now = store.utcnow()
    return {
        "id": store.new_id(),
        "title": title,
        "counterparty": counterparty,
        "amount": amount,
        "template_id": template_id,
        "content_json": content_json or {},
        "status": ContractStatus.DRAFT.value,
        "handler_id": handler_id,
        "approver_1_id": approver_1_id,
        "approver_2_id": approver_2_id,
        "signed_at": None,
        "expires_at": expires_at,
        "created_at": now,
        "updated_at": now,
    }


def make_approval_record(store, contract_id: str, level: int, approver_id: str) -> dict:
    return {
        "id": store.new_id(),
        "contract_id": contract_id,
        "level": level,
        "approver_id": approver_id,
        "decision": "pending",
        "comment": "",
        "decided_at": None,
    }


def make_message(store, user_id: str, title: str, body: str, contract_id: str | None = None) -> dict:
    return {
        "id": store.new_id(),
        "user_id": user_id,
        "title": title,
        "body": body,
        "contract_id": contract_id,
        "is_read": False,
        "created_at": store.utcnow(),
    }


def make_template(store, name: str, description: str, fields_json: list[dict], created_by: str) -> dict:
    return {
        "id": store.new_id(),
        "name": name,
        "description": description,
        "fields_json": fields_json,
        "is_active": True,
        "created_by": created_by,
        "created_at": store.utcnow(),
    }


def make_audit_log(store, user_id: str, action: str, target_type: str, target_id: str, detail: str) -> dict:
    return {
        "id": store.new_id(),
        "user_id": user_id,
        "action": action,
        "target_type": target_type,
        "target_id": target_id,
        "detail": detail,
        "created_at": store.utcnow(),
    }
