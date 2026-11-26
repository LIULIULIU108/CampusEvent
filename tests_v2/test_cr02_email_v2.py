"""CR-02：Mock 邮件通知测试（change-v2）。"""

from __future__ import annotations

import uuid

from app_v2 import db
from app_v2.domain.enums import EventType, PolicyType
from app_v2.domain.models import DomainEvent
from tests_v2.helpers import NOW, count_rows, fetch_one, make_activity


def emails(app):
    with app.app_context():
        return app.extensions["services"].emails.list_all()


def register(app, activity_id: int, student_id: str = "2024001"):
    with app.app_context():
        return app.extensions["services"].registrations.register(
            student_id, activity_id
        )


def test_direct_registration_creates_in_app_and_email(app):
    activity = make_activity(app, capacity=2)
    register(app, activity.activity_id)
    rows = emails(app)
    assert len(rows) == 1
    email = rows[0]
    assert email.student_id == "2024001"
    assert email.recipient == "2024001@mock.campus.local"
    assert email.status == "SENT"
    assert "报名成功" in email.subject
    assert count_rows(app, "message", "student_id='2024001'") == 1
    assert count_rows(app, "notification_attempt", "channel='email' AND status='SENT'") == 1


def test_pending_submission_does_not_send_email(app):
    activity = make_activity(app, policy=PolicyType.APPROVAL, capacity=2)
    register(app, activity.activity_id)
    assert emails(app) == []
    assert count_rows(app, "notification_attempt", "channel='email'") == 0
    assert count_rows(app, "message", "student_id='2024001'") == 1


def test_admin_approval_and_rejection_send_email(app):
    activity = make_activity(app, policy=PolicyType.APPROVAL, capacity=2)
    register(app, activity.activity_id, "2024001")
    first = fetch_one(
        app,
        "SELECT registration_id FROM registration WHERE student_id='2024001'",
    )
    with app.app_context():
        app.extensions["services"].approvals.approve(first["registration_id"])

    register(app, activity.activity_id, "2024002")
    second = fetch_one(
        app,
        "SELECT registration_id FROM registration WHERE student_id='2024002'",
    )
    with app.app_context():
        app.extensions["services"].approvals.reject(second["registration_id"])

    rows = emails(app)
    assert len(rows) == 2
    subjects = {row.student_id: row.subject for row in rows}
    assert "审核通过" in subjects["2024001"]
    assert "审核未通过" in subjects["2024002"]
    assert all(row.status == "SENT" for row in rows)


def test_email_failure_is_logged_and_registration_survives(app):
    activity = make_activity(app, capacity=2)
    with app.app_context():
        app.extensions["services"].email_sender.fail = True
        registration = app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
    assert registration.status.value == "APPROVED"
    assert count_rows(app, "registration", "status='APPROVED'") == 1
    assert count_rows(app, "message", "student_id='2024001'") == 1
    email = emails(app)[0]
    assert email.status == "FAILED"
    assert "模拟邮件发送失败" in (email.error or "")
    attempt = fetch_one(
        app,
        "SELECT status, error FROM notification_attempt WHERE channel='email'",
    )
    assert attempt["status"] == "FAILED"
    assert "模拟邮件发送失败" in attempt["error"]


def test_duplicate_event_does_not_send_twice(app):
    activity = make_activity(app, capacity=2)
    with app.app_context():
        publisher = app.extensions["services"].registrations.publisher
        event = DomainEvent(
            event_id=uuid.uuid4().hex,
            event_type=EventType.REGISTRATION_AUTO_APPROVED,
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
    assert count_rows(app, "email_outbox") == 1


def test_admin_notification_page(admin_client, app):
    activity = make_activity(app, capacity=2)
    register(app, activity.activity_id)
    response = admin_client.get("/admin/notifications")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "2024001@mock.campus.local" in text
    assert "已发送" in text
