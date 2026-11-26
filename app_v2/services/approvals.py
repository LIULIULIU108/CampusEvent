"""管理员审批用例。"""

from __future__ import annotations

import uuid

from .. import db
from ..domain.capacity import CapacityChecker
from ..domain.enums import EventType, RegistrationStatus
from ..domain.errors import ConflictError, DomainError, NotFoundError
from ..domain.models import DomainEvent, RegistrationWithStudent
from ..repositories import ActivityRepository, RegistrationRepository
from ..validation import format_datetime_cn


class ApprovalService:
    def __init__(
        self,
        activities: ActivityRepository,
        registrations: RegistrationRepository,
        capacity: CapacityChecker,
        publisher,
        clock,
    ) -> None:
        self.activities = activities
        self.registrations = registrations
        self.capacity = capacity
        self.publisher = publisher
        self.clock = clock

    def list_registrations(
        self,
        activity_id: int,
        statuses: tuple[RegistrationStatus, ...] | None = None,
    ) -> list[RegistrationWithStudent]:
        conn = db.get_db()
        activity = self.activities.get(conn, activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        return self.registrations.list_with_student(conn, activity_id, statuses)

    def approve(self, registration_id: int) -> None:
        conn = db.get_db()
        now = self.clock.now()
        event: DomainEvent | None = None

        with db.transaction():
            registration = self.registrations.get(conn, registration_id)
            if registration is None:
                raise NotFoundError("报名记录不存在")
            if registration.status is not RegistrationStatus.PENDING:
                raise ConflictError("只有待审核报名可以批准")

            activity = self.activities.get(conn, registration.activity_id)
            if activity is None:
                raise NotFoundError("活动不存在")
            if now >= activity.start_at:
                raise DomainError("活动已开始，不能批准新的报名")

            approved = self.registrations.count_approved(conn, activity.activity_id)
            if not self.capacity.has_capacity(activity, approved):
                raise DomainError("名额已满，无法批准；报名保持待审核")

            ok = self.registrations.update_status(
                conn,
                registration_id,
                RegistrationStatus.APPROVED,
                now,
                expected=RegistrationStatus.PENDING,
            )
            if not ok:
                raise ConflictError("报名状态已变化，请刷新后重试")

            event = DomainEvent(
                event_id=uuid.uuid4().hex,
                event_type=EventType.REGISTRATION_ADMIN_APPROVED,
                activity_id=activity.activity_id,
                student_id=registration.student_id,
                registration_id=registration_id,
                occurred_at=now,
                payload={
                    "title": activity.title,
                    "start_at_display": format_datetime_cn(activity.start_at),
                    "location": activity.location,
                    "status": RegistrationStatus.APPROVED.value,
                },
            )

        assert event is not None
        self.publisher.publish(event, conn)

    def reject(self, registration_id: int) -> None:
        conn = db.get_db()
        now = self.clock.now()
        event: DomainEvent | None = None

        with db.transaction():
            registration = self.registrations.get(conn, registration_id)
            if registration is None:
                raise NotFoundError("报名记录不存在")
            if registration.status is not RegistrationStatus.PENDING:
                raise ConflictError("只有待审核报名可以拒绝")

            activity = self.activities.get(conn, registration.activity_id)
            if activity is None:
                raise NotFoundError("活动不存在")

            ok = self.registrations.update_status(
                conn,
                registration_id,
                RegistrationStatus.REJECTED,
                now,
                expected=RegistrationStatus.PENDING,
            )
            if not ok:
                raise ConflictError("报名状态已变化，请刷新后重试")

            event = DomainEvent(
                event_id=uuid.uuid4().hex,
                event_type=EventType.REGISTRATION_ADMIN_REJECTED,
                activity_id=activity.activity_id,
                student_id=registration.student_id,
                registration_id=registration_id,
                occurred_at=now,
                payload={
                    "title": activity.title,
                    "start_at_display": format_datetime_cn(activity.start_at),
                    "location": activity.location,
                    "status": RegistrationStatus.REJECTED.value,
                },
            )

        assert event is not None
        self.publisher.publish(event, conn)
