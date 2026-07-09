"""模板业务逻辑 — CRUD + 启用/停用."""

from app.domain.models import make_template
from app.repositories.json_repository import JsonRepository
from app.schemas.templates import TemplateCreate, TemplateUpdate


class TemplateService:
    """模板服务 — 封装模板相关业务逻辑."""

    def __init__(self, repo: JsonRepository) -> None:
        self._repo = repo

    def list_active(self) -> list[dict]:
        """返回启用的模板（经办人选模板用）."""
        return self._repo.list_active_templates()

    def list_all(self) -> list[dict]:
        """返回全部模板（管理员管理用）."""
        return self._repo.list_all_templates()

    def get(self, template_id: str) -> dict | None:
        """查询单个模板."""
        return self._repo.find_template_by_id(template_id)

    def create(self, data: TemplateCreate, admin: dict) -> dict:
        """创建模板 — 使用 make_template 工厂生成完整模板对象."""
        fields = [f.model_dump() for f in data.fields_json]
        template = make_template(
            self._repo._store,
            data.name,
            data.description,
            fields,
            admin["id"],
        )
        return self._repo.create_template(template)

    def update(self, template_id: str, data: TemplateUpdate) -> dict | None:
        """更新模板 — 仅更新请求中提供的字段（PATCH 语义）."""
        updates: dict = {}
        if data.name is not None:
            updates["name"] = data.name
        if data.description is not None:
            updates["description"] = data.description
        if data.fields_json is not None:
            updates["fields_json"] = [f.model_dump() for f in data.fields_json]
        if not updates:
            return self._repo.find_template_by_id(template_id)
        return self._repo.update_template(template_id, updates)

    def toggle(self, template_id: str, is_active: bool) -> dict | None:
        """启用/停用模板."""
        return self._repo.update_template(template_id, {"is_active": is_active})
