import hashlib

from fastapi import APIRouter, Depends, Request, Response

from app.api.dependencies import get_current_user, get_store, require_admin
from app.api.errors import error
from app.config import get_settings
from app.repositories.json_repository import JsonRepository
from app.schemas.auth import LoginRequest, RegisterRequest, UserResponse
from app.services.auth_service import AuthService
from app.storage.json_store import JsonFileStore

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


def get_auth_service(store=Depends(get_store)) -> AuthService:
    return AuthService(JsonRepository(store))


@router.post("/login")
def login(body: LoginRequest, request: Request, response: Response,
          svc: AuthService = Depends(get_auth_service)):
    result = svc.login(body.username_or_email, body.password)
    if result == "invalid_credentials":
        error("LOGIN_FAILED", "账号或密码错误", 401)
    if result == "account_disabled":
        error("LOGIN_FAILED", "账号已被禁用", 401)
    user, raw_token = result
    settings = get_settings()
    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=raw_token,
        httponly=True,
        samesite="lax",
        secure=settings.SESSION_COOKIE_SECURE,
        max_age=settings.SESSION_TTL_HOURS * 3600,
        path="/",
    )
    return {"user": UserResponse(**user).model_dump()}


@router.post("/logout")
def logout(request: Request, response: Response,
           user: dict = Depends(get_current_user),
           svc: AuthService = Depends(get_auth_service)):
    settings = get_settings()
    token = request.cookies.get(settings.SESSION_COOKIE_NAME, "")
    if token:
        svc.logout(hashlib.sha256(token.encode()).hexdigest())
    response.delete_cookie(settings.SESSION_COOKIE_NAME, path="/")
    return {"message": "已退出登录"}


@router.get("/me")
def me(user: dict = Depends(get_current_user)):
    return {"user": UserResponse(**user).model_dump()}


@router.post("/register")
def register(body: RegisterRequest, admin: dict = Depends(require_admin),
             svc: AuthService = Depends(get_auth_service)):
    result = svc.register(body.username, body.email, body.password, body.role)
    if result == "username_taken":
        error("CONFLICT", "用户名已存在", 409)
    if result == "email_taken":
        error("CONFLICT", "邮箱已存在", 409)
    if result == "invalid_role":
        error("VALIDATION_ERROR", "无效的角色类型", 422)
    return {"user": UserResponse(**result).model_dump()}


@router.get("/approvers")
def list_approvers(user: dict = Depends(get_current_user),
                   store: JsonFileStore = Depends(get_store)):
    """获取活跃审批人列表（所有登录用户可访问）."""
    repo = JsonRepository(store)
    approvers = [u for u in repo.list_users_by_role("approver") if u.get("is_active", True)]
    return {"approvers": [UserResponse(**a).model_dump() for a in approvers]}
