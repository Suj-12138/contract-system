"""合同相关 Pydantic 模型."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field

from app.domain.enums import ContractStatus


class ContractCreate(BaseModel):
    """创建合同请求."""
    title: str = Field(..., min_length=1, max_length=200, description="合同标题")
    counterparty: str = Field(..., min_length=1, max_length=200, description="对方名称")
    party_a: str = Field(default="本公司", max_length=200, description="甲方")
    party_b: str = Field(default="", max_length=200, description="乙方")
    amount: Optional[float] = Field(None, ge=0, description="合同金额")
    template_id: Optional[str] = Field(None, description="模板ID")
    approver_1_id: str = Field(..., description="一级审批人ID")
    approver_2_id: str = Field(..., description="二级审批人ID")
    expires_at: Optional[str] = Field(None, description="到期日期 (ISO 8601)")
    content_text: str = Field(default="", description="合同正文内容（自由填写）")


class ContractUpdate(BaseModel):
    """编辑合同请求."""
    title: Optional[str] = Field(None, min_length=1, max_length=200)
    counterparty: Optional[str] = Field(None, min_length=1, max_length=200)
    party_a: Optional[str] = Field(None, max_length=200)
    party_b: Optional[str] = Field(None, max_length=200)
    amount: Optional[float] = Field(None, ge=0)
    content_text: Optional[str] = None
    expires_at: Optional[str] = None


class ContractResponse(BaseModel):
    """合同响应."""
    id: str
    title: str
    counterparty: str
    amount: Optional[float]
    template_id: Optional[str]
    content_json: dict
    status: str
    handler_id: str
    approver_1_id: str
    approver_2_id: str
    signed_at: Optional[str]
    expires_at: Optional[str]
    created_at: str
    updated_at: str


class ApprovalRecordResponse(BaseModel):
    """审批记录响应."""
    id: str
    contract_id: str
    level: int
    approver_id: str
    decision: str
    comment: Optional[str]
    decided_at: Optional[str]


class AuditLogResponse(BaseModel):
    """审计日志响应."""
    id: str
    user_id: str
    action: str
    target_type: str
    target_id: str
    detail: str
    created_at: str


class ContractDetailResponse(BaseModel):
    """合同详情响应（含审批记录和操作历史）."""
    contract: ContractResponse
    approvals: list[ApprovalRecordResponse]
    audit_logs: list[AuditLogResponse]


class ContractListResponse(BaseModel):
    """合同列表响应."""
    contracts: list[ContractResponse]
    total: int
