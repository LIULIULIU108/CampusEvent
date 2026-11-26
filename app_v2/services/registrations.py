"""报名与取消用例。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import datetime

from .. import db
from ..domain.enums import ACTIVE_STATUSES, EventType, RegistrationStatus
from ..domain.errors import ConflictError, DomainError, NotFoundError, PermissionDeniedError
from ..domain.models import (
    DomainEvent,
    Registration,
    RegistrationContext,
    RegistrationWithActivity,
)
from ..domain.policies import PolicyRegistry
from ..repositories import (
    ActivityRepository,
    RegistrationRepository,
    StudentRepository,
)
from ..validation import format_datetime_cn


class RegistrationService:
    def __init__(
        self,
        activities: ActivityRepository,
        students: StudentRepository,
        registrations: RegistrationRepository,
        registry: PolicyRegistry,
        publisher,
        clock,
    ) -> None:
        self.activities = activities
        self.students = students
        self.registrations = registrations
        self.registry = registry
        self.publisher = publisher
        self.clock = clock

    def register(self, student_id: str, activity_id: int) -> Registration:
        conn = db.get_db()
        now = self.clock.now()
        event: DomainEvent | None = None

        try:
            with db.transaction():
                activity = self.activities.get(conn, activity_id)
                if activity is None:
                    raise NotFoundError("活动不存在")
                student = self.students.get(conn, student_id)
                if student is None:
                    raise NotFoundError("学生不存在")

                if not activity.is_open(now):
                    raise DomainError("活动已开始，无法报名")
                if self.registrations.get_active(conn, activity_id, student_id):
                    raise ConflictError("您已报名该活动，请勿重复提交")

                approved = self.registrations.count_approved(conn, activity_id)
                policy = self.registry.resolve(activity.policy_type)
                decision = policy.decide(
                    RegistrationContext(activity, student, approved, now)
                )
                if not decision.accepted:
                    raise DomainError(decision.reason or "报名失败")

                assert decision.status is not None
                registration = self.registrations.create(
                    conn,
                    activity_id=activity_id,
                    student_id=student_id,
                    status=decision.status,
                    now=now,
                )

                event_type = (
                    EventType.REGISTRATION_AUTO_APPROVED
                    if decision.status is RegistrationStatus.APPROVED
                    else EventType.REGISTRATION_PENDING
                )
                event = DomainEvent(
                    event_id=uuid.uuid4().hex,
                    event_type=event_type,
                    activity_id=activity_id,
                    student_id=student_id,
                    registration_id=registration.registration_id,
                    occurred_at=now,
                    payload={
                        "title": activity.title,
                        "start_at_display": format_datetime_cn(activity.start_at),
                        "location": activity.location,
                        "status": decision.status.value,
                    },
                )
        except sqlite3.IntegrityError as exc:
            raise ConflictError("您已报名该活动，请勿重复提交") from exc

        assert event is not None
        self.publisher.publish(event, conn)
        return registration

    def cancel(self, student_id: str, registration_id: int) -> None:
        conn = db.get_db()
        now = self.clock.now()
        with db.transaction():
            registration = self.registrations.get(conn, registration_id)
            if registration is None:
                raise NotFoundError("报名记录不存在")
            if registration.student_id != student_id:
                raise PermissionDeniedError("只能取消自己的报名")
            if registration.status not in ACTIVE_STATUSES:
                raise ConflictError("当前状态不可取消")
            ok = self.registrations.update_status(
                conn,
                registration_id,
                RegistrationStatus.CANCELLED,
                now,
                expected=registration.status,
            )
            if not ok:
                raise ConflictError("报名状态已变化，请刷新后重试")

    def get_active(self, student_id: str, activity_id: int) -> Registration | None:
        conn = db.get_db()
        return self.registrations.get_active(conn, activity_id, student_id)

    def active_by_student(self, student_id: str) -> dict[int, Registration]:
        conn = db.get_db()
        result: dict[int, Registration] = {}
        for registration in self.registrations.list_for_student(conn, student_id):
            if registration.is_active():
                result[registration.activity_id] = registration
        return result

    def list_for_student_with_activity(
        self, student_id: str
    ) -> list[RegistrationWithActivity]:
        conn = db.get_db()
        items: list[RegistrationWithActivity] = []
        for registration in self.registrations.list_for_student(conn, student_id):
            activity = self.activities.get(conn, registration.activity_id)
            if activity is not None:
                items.append(RegistrationWithActivity(registration, activity))
        return items
