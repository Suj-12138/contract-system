"""管理员路由 — /api/v1/admin 用户管理 + 统计（4 端点）."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_store, require_admin
from app.api.errors import conflict, error, not_found
from app.repositories.json_repository import JsonRepository
from app.schemas.auth import RegisterRequest, UserResponse
from app.schemas.users import UserStatusUpdate
from app.services.admin_service import AdminService

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


def get_admin_service(store=Depends(get_store)) -> AdminService:
    """管理员 Service 工厂 — 参考 P1 get_auth_service 模式."""
    return AdminService(JsonRepository(store))


@router.get("/users")
def list_users(admin: dict = Depends(require_admin),
               svc: AdminService = Depends(get_admin_service)):
    """用户列表 — 仅 admin."""
    users = svc.list_users()
    return {
        "users": [UserResponse(**u).model_dump() for u in users]
    }


@router.post("/users")
def create_user(body: RegisterRequest,
                admin: dict = Depends(require_admin),
                svc: AdminService = Depends(get_admin_service)):
    """创建用户 — 仅 admin，复用 P1 RegisterRequest schema."""
    result = svc.create_user(body.username, body.email, body.password, body.role)
    if result == "username_taken":
        conflict("用户名已存在")
    if result == "email_taken":
        conflict("邮箱已存在")
    if result == "invalid_role":
        error("VALIDATION_ERROR", "无效的角色类型", 422)
    return {"user": UserResponse(**result).model_dump()}


@router.patch("/users/{user_id}/status")
def toggle_user(user_id: str,
                body: UserStatusUpdate,
                admin: dict = Depends(require_admin),
                svc: AdminService = Depends(get_admin_service)):
    """启用/禁用用户 — 仅 admin，复用 P1 UserStatusUpdate schema."""
    user = svc.toggle_user(user_id, body.is_active)
    if user is None:
        not_found("用户")
    return {"user": UserResponse(**user).model_dump()}


@router.get("/stats")
def get_stats(admin: dict = Depends(require_admin),
              svc: AdminService = Depends(get_admin_service)):
    """数据看板 — 仅 admin."""
    return svc.get_stats()
