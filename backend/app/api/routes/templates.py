"""模板路由 — /api/v1/templates CRUD（4 端点）."""

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_store, require_admin
from app.api.errors import not_found
from app.repositories.json_repository import JsonRepository
from app.schemas.templates import (TemplateCreate, TemplateResponse,
                                   TemplateStatusUpdate, TemplateUpdate)
from app.services.template_service import TemplateService

router = APIRouter(prefix="/api/v1/templates", tags=["templates"])


def get_template_service(store=Depends(get_store)) -> TemplateService:
    """模板 Service 工厂 — 参考 P1 get_auth_service 模式."""
    return TemplateService(JsonRepository(store))


@router.get("/")
def list_templates(user: dict = Depends(get_current_user),
                   svc: TemplateService = Depends(get_template_service)):
    """模板列表 — admin 看全部，其他角色只看启用的."""
    if user["role"] == "admin":
        templates = svc.list_all()
    else:
        templates = svc.list_active()
    return {
        "templates": [TemplateResponse(**t).model_dump() for t in templates]
    }


@router.post("/")
def create_template(body: TemplateCreate,
                    admin: dict = Depends(require_admin),
                    svc: TemplateService = Depends(get_template_service)):
    """创建模板 — 仅 admin."""
    template = svc.create(body, admin)
    return {"template": TemplateResponse(**template).model_dump()}


@router.put("/{template_id}")
def update_template(template_id: str,
                    body: TemplateUpdate,
                    admin: dict = Depends(require_admin),
                    svc: TemplateService = Depends(get_template_service)):
    """编辑模板 — 仅 admin，PATCH 语义."""
    template = svc.update(template_id, body)
    if template is None:
        not_found("模板")
    return {"template": TemplateResponse(**template).model_dump()}


@router.patch("/{template_id}/status")
def toggle_template(template_id: str,
                    body: TemplateStatusUpdate,
                    admin: dict = Depends(require_admin),
                    svc: TemplateService = Depends(get_template_service)):
    """启用/停用模板 — 仅 admin."""
    template = svc.toggle(template_id, body.is_active)
    if template is None:
        not_found("模板")
    return {"template": TemplateResponse(**template).model_dump()}
