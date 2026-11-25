"""报名服务单测。"""

from __future__ import annotations

import sqlite3
import uuid
from datetime import timedelta

import pytest

from app import db
from app.domain.enums import EventType, PolicyType, RegistrationStatus
from app.domain.errors import (
    ConflictError,
    DomainError,
    NotFoundError,
    PermissionDeniedError,
)
from app.domain.models import DomainEvent
from tests.helpers import (
    NOW,
    active_registration,
    count_rows,
    fetch_one,
    make_activity,
)


def register(app, activity_id: int, student_id: str = "2024001"):
    with app.app_context():
        return app.extensions["services"].registrations.register(
            student_id, activity_id
        )


def cancel(app, registration_id: int, student_id: str = "2024001"):
    with app.app_context():
        return app.extensions["services"].registrations.cancel(
            student_id, registration_id
        )


def test_register_direct_creates_approved_and_message(app):
    activity = make_activity(app, capacity=2)
    registration = register(app, activity.activity_id)
    assert registration.status is RegistrationStatus.APPROVED
    assert active_registration(app, activity.activity_id) is not None
    assert count_rows(app, "message", "student_id=?", ("2024001",)) == 1
    assert count_rows(app, "notification_attempt", "status='SENT'") == 1


def test_duplicate_active_registration_rejected(app):
    activity = make_activity(app, capacity=2)
    register(app, activity.activity_id)
    with pytest.raises(ConflictError):
        register(app, activity.activity_id)
    assert count_rows(app, "registration", "activity_id=?", (activity.activity_id,)) == 1


def test_direct_full_does_not_create_row(app):
    activity = make_activity(app, capacity=1)
    register(app, activity.activity_id, "2024001")
    with pytest.raises(DomainError, match="名额已满"):
        register(app, activity.activity_id, "2024002")
    assert count_rows(app, "registration", "activity_id=?", (activity.activity_id,)) == 1
    assert active_registration(app, activity.activity_id, "2024002") is None


def test_started_activity_rejected(app):
    activity = make_activity(app, start_at=NOW - timedelta(hours=1))
    with pytest.raises(DomainError, match="活动已开始"):
        register(app, activity.activity_id)
    assert count_rows(app, "registration") == 0


def test_cancel_approved_then_reapply(app):
    activity = make_activity(app, capacity=2)
    first = register(app, activity.activity_id)
    cancel(app, first.registration_id)
    assert fetch_one(
        app, "SELECT status FROM registration WHERE registration_id=?",
        (first.registration_id,),
    )["status"] == "CANCELLED"
    second = register(app, activity.activity_id)
    assert second.registration_id != first.registration_id
    assert second.status is RegistrationStatus.APPROVED
    assert count_rows(app, "registration", "activity_id=?", (activity.activity_id,)) == 2


def test_cancel_other_student_denied(app):
    activity = make_activity(app, )
    registration = register(app, activity.activity_id)
    with pytest.raises(PermissionDeniedError):
        cancel(app, registration.registration_id, "2024002")


def test_cancel_cancelled_raises(app):
    activity = make_activity(app, )
    registration = register(app, activity.activity_id)
    cancel(app, registration.registration_id)
    with pytest.raises(ConflictError):
        cancel(app, registration.registration_id)


def test_unique_index_blocks_duplicate_active_insert(app):
    activity = make_activity(app, )
    registration = register(app, activity.activity_id)
    with app.app_context():
        conn = db.get_db()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO registration(activity_id, student_id, status, created_at, updated_at) "
                "VALUES (?, ?, 'APPROVED', ?, ?)",
                (
                    activity.activity_id,
                    "2024001",
                    NOW.isoformat(),
                    NOW.isoformat(),
                ),
            )
    assert registration.status is RegistrationStatus.APPROVED


def test_unknown_activity_or_student(app):
    activity = make_activity(app, )
    with app.app_context():
        service = app.extensions["services"].registrations
        with pytest.raises(NotFoundError):
            service.register("9999999", activity.activity_id)
        with pytest.raises(NotFoundError):
            service.register("2024001", 9999999)


def test_pending_does_not_occupy_capacity(app):
    activity = make_activity(app, capacity=1, policy=PolicyType.APPROVAL)
    pending = register(app, activity.activity_id, "2024001")
    assert pending.status is RegistrationStatus.PENDING
    other = register(app, activity.activity_id, "2024002")
    assert other.status is RegistrationStatus.PENDING
    assert count_rows(
        app,
        "registration",
        "activity_id=? AND status='APPROVED'",
        (activity.activity_id,),
    ) == 0


def test_active_by_student_and_list_with_activity(app):
    activity = make_activity(app, )
    registration = register(app, activity.activity_id)
    with app.app_context():
        service = app.extensions["services"].registrations
        mapping = service.active_by_student("2024001")
        assert mapping[activity.activity_id].registration_id == registration.registration_id
        items = service.list_for_student_with_activity("2024001")
        assert len(items) == 1
        assert items[0].activity.title == activity.title


def test_notification_failure_is_logged_without_rollback(app):
    activity = make_activity(app, capacity=2)

    class FailingObserver:
        channel = "in_app"

        def handle(self, event, conn):  # noqa: ARG002
            raise RuntimeError("模拟通知写入失败")

    with app.app_context():
        service = app.extensions["services"].registrations
        service.publisher.observers = [FailingObserver()]
        registration = service.register("2024001", activity.activity_id)

    assert registration.status is RegistrationStatus.APPROVED
    assert active_registration(app, activity.activity_id) is not None
    assert count_rows(app, "message") == 0
    failed = fetch_one(
        app,
        "SELECT status, error FROM notification_attempt WHERE event_id IS NOT NULL",
    )
    assert failed is not None
    assert failed["status"] == "FAILED"
    assert "模拟通知" in failed["error"]


def test_publish_duplicate_event_only_one_message(app):
    activity = make_activity(app, )
    with app.app_context():
        publisher = app.extensions["services"].registrations.publisher
        event = DomainEvent(
            event_id=uuid.uuid4().hex,
            event_type=EventType.REGISTRATION_PENDING,
            activity_id=activity.activity_id,
            student_id="2024001",
            registration_id=1,
            occurred_at=NOW,
            payload={
                "title": activity.title,
                "start_at_display": "2026-11-28 14:00",
                "location": activity.location,
            },
        )
        conn = db.get_db()
        publisher.publish(event, conn)
        publisher.publish(event, conn)

    assert count_rows(app, "message") == 1
    assert count_rows(app, "notification_attempt", "status='SENT'") == 1
