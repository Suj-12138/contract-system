from fastapi import HTTPException


def error(code: str, message: str, status_code: int = 400, field_errors: dict | None = None):
    body = {"error": {"code": code, "message": message}}
    if field_errors:
        body["error"]["field_errors"] = field_errors
    raise HTTPException(status_code=status_code, detail=body["error"])


def authentication_required():
    error("AUTHENTICATION_REQUIRED", "请先登录", 401)


def forbidden():
    error("FORBIDDEN", "权限不足", 403)


def not_found(resource: str = "记录"):
    error("RESOURCE_NOT_FOUND", f"{resource}不存在", 404)


def conflict(message: str):
    error("CONFLICT", message, 409)


def invalid_transition():
    error("INVALID_TRANSITION", "不允许的状态流转", 409)
