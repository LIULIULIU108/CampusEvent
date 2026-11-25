"""领域实体与值对象。"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from .enums import ACTIVE_STATUSES, EventType, PolicyType, RegistrationStatus


@dataclass(frozen=True)
class Student:
    student_id: str
    name: str
    password_hash: str = ""
    created_at: datetime | None = None


@dataclass(frozen=True)
class Activity:
    activity_id: int
    title: str
    category: str
    start_at: datetime
    location: str
    capacity: int
    policy_type: PolicyType
    created_at: datetime | None = None
    updated_at: datetime | None = None

    def is_open(self, now: datetime) -> bool:
        return now < self.start_at

    def remaining(self, approved_count: int) -> int:
        return max(0, self.capacity - approved_count)


@dataclass(frozen=True)
class Registration:
    registration_id: int
    activity_id: int
    student_id: str
    status: RegistrationStatus
    created_at: datetime
    updated_at: datetime

    def is_active(self) -> bool:
        return self.status in ACTIVE_STATUSES


@dataclass(frozen=True)
class RegistrationWithStudent:
    registration: Registration
    student_name: str


@dataclass(frozen=True)
class RegistrationWithActivity:
    registration: Registration
    activity: Activity


@dataclass(frozen=True)
class Message:
    message_id: int
    student_id: str
    activity_id: int | None
    content: str
    is_read: bool
    created_at: datetime


@dataclass(frozen=True)
class RegistrationContext:
    activity: Activity
    student: Student
    approved_count: int
    now: datetime


@dataclass(frozen=True)
class PolicyDecision:
    accepted: bool
    status: RegistrationStatus | None = None
    reason: str | None = None

    def __post_init__(self) -> None:
        if self.accepted and self.status is None:
            raise ValueError("受理的决策必须给出目标状态")
        if not self.accepted and self.status is not None:
            raise ValueError("拒绝的决策不应给出目标状态")


@dataclass(frozen=True)
class ActivityStats:
    activity_id: int
    capacity: int
    approved_count: int
    pending_count: int
    remaining: int


@dataclass(frozen=True)
class DomainEvent:
    event_id: str
    event_type: EventType
    activity_id: int
    student_id: str
    registration_id: int
    occurred_at: datetime
    payload: dict[str, Any] = field(default_factory=dict)
