"""领域枚举与中文标签。"""

from __future__ import annotations

from enum import StrEnum


class Role(StrEnum):
    STUDENT = "STUDENT"
    ADMIN = "ADMIN"


class PolicyType(StrEnum):
    DIRECT = "DIRECT"
    APPROVAL = "APPROVAL"
    GRADE_DIRECT = "GRADE_DIRECT"


class RegistrationStatus(StrEnum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    CANCELLED = "CANCELLED"


class EventType(StrEnum):
    REGISTRATION_AUTO_APPROVED = "REGISTRATION_AUTO_APPROVED"
    REGISTRATION_PENDING = "REGISTRATION_PENDING"
    REGISTRATION_ADMIN_APPROVED = "REGISTRATION_ADMIN_APPROVED"
    REGISTRATION_ADMIN_REJECTED = "REGISTRATION_ADMIN_REJECTED"


POLICY_LABELS = {
    PolicyType.DIRECT: "直接报名",
    PolicyType.APPROVAL: "审核报名",
    PolicyType.GRADE_DIRECT: "年级限定报名",
}

GRADE_LABELS = {
    1: "大一",
    2: "大二",
    3: "大三",
    4: "大四",
}

STATUS_LABELS = {
    RegistrationStatus.PENDING: "待审核",
    RegistrationStatus.APPROVED: "已通过",
    RegistrationStatus.REJECTED: "已拒绝",
    RegistrationStatus.CANCELLED: "已取消",
}

STATUS_CLASSES = {
    RegistrationStatus.PENDING: "pending",
    RegistrationStatus.APPROVED: "approved",
    RegistrationStatus.REJECTED: "rejected",
    RegistrationStatus.CANCELLED: "cancelled",
}

ACTIVE_STATUSES = (RegistrationStatus.PENDING, RegistrationStatus.APPROVED)
