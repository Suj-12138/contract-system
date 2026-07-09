"""模板 Pydantic Schema — 请求/响应模型."""
from typing import Literal

from pydantic import BaseModel, Field


class TemplateField(BaseModel):
    """模板动态字段定义."""
    label: str
    type: Literal["text", "number", "date", "textarea"]
    required: bool = False


class TemplateCreate(BaseModel):
    """创建模板请求."""
    name: str = Field(..., min_length=1, max_length=100)
    description: str = ""
    fields_json: list[TemplateField] = []


class TemplateUpdate(BaseModel):
    """更新模板请求 — 所有字段可选（PATCH 语义）."""
    name: str | None = None
    description: str | None = None
    fields_json: list[TemplateField] | None = None


class TemplateStatusUpdate(BaseModel):
    """模板启用/停用请求."""
    is_active: bool


class TemplateResponse(BaseModel):
    """模板响应（对外输出）."""
    id: str
    name: str
    description: str
    fields_json: list[dict]
    is_active: bool
    created_by: str
    created_at: str
