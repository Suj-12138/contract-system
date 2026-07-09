"""领域枚举定义."""

from enum import Enum


class UserRole(str, Enum):
    HANDLER = "handler"
    APPROVER = "approver"
    ADMIN = "admin"


class ContractStatus(str, Enum):
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    SIGNED = "signed"
    ACTIVE = "active"
    EXPIRED = "expired"
    RENEWED = "renewed"
    ARCHIVED = "archived"

    @classmethod
    def next_statuses(cls, current: "ContractStatus") -> list["ContractStatus"]:
        transitions = {
            cls.DRAFT: [cls.REVIEW],
            cls.REVIEW: [cls.APPROVED, cls.REJECTED],
            cls.REJECTED: [cls.REVIEW],
            cls.APPROVED: [cls.SIGNED],
            cls.SIGNED: [cls.ACTIVE],
            cls.ACTIVE: [cls.EXPIRED, cls.RENEWED],
            cls.EXPIRED: [cls.ARCHIVED],
            cls.RENEWED: [cls.ARCHIVED],
        }
        return transitions.get(current, [])


class ApprovalDecision(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
