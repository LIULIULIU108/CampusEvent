"""站内消息与通知留痕测试。"""

from __future__ import annotations

import uuid

import pytest

from app_v2 import db
from app_v2.domain.enums import EventType, PolicyType
from app_v2.domain.models import DomainEvent
from app_v2.domain.notifications import build_message
from tests_v2.helpers import NOW, count_rows, fetch_one, make_activity


def event(event_type: EventType) -> DomainEvent:
    return DomainEvent(
        event_id=uuid.uuid4().hex,
        event_type=event_type,
        activity_id=1,
        student_id="2024001",
        registration_id=1,
        occurred_at=NOW,
        payload={
            "title": "数据结构讲座",
            "start_at_display": "2026-11-28 14:00",
            "location": "图书馆报告厅",
        },
    )


def test_auto_approved_message_text():
    text = build_message(event(EventType.REGISTRATION_AUTO_APPROVED))
    assert "报名成功" in text
    assert "数据结构讲座" in text
    assert "图书馆报告厅" in text


def test_pending_message_text():
    text = build_message(event(EventType.REGISTRATION_PENDING))
    assert "报名已提交" in text
    assert "等待管理员审核" in text


def test_admin_approved_message_text():
    text = build_message(event(EventType.REGISTRATION_ADMIN_APPROVED))
    assert "审核通过" in text
    assert "图书馆报告厅" in text


def test_admin_rejected_message_text():
    text = build_message(event(EventType.REGISTRATION_ADMIN_REJECTED))
    assert "审核未通过" in text
    assert "数据结构讲座" in text


def test_message_unread_and_mark_read(app):
    activity = make_activity(app, )
    with app.app_context():
        service = app.extensions["services"].registrations
        registration = service.register("2024001", activity.activity_id)
        messages = app.extensions["services"].messages
        items = messages.list_for_student("2024001")
        assert len(items) == 1
        assert messages.unread_count("2024001") == 1
        assert messages.mark_read("2024001", items[0].message_id) is True
        assert messages.unread_count("2024001") == 0
        assert registration.registration_id > 0


def test_mark_read_other_student_returns_false(app):
    activity = make_activity(app, )
    with app.app_context():
        app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
        messages = app.extensions["services"].messages
        item = messages.list_for_student("2024001")[0]
        assert messages.mark_read("2024002", item.message_id) is False
        assert messages.unread_count("2024001") == 1


def test_mark_all_read(app):
    activity = make_activity(app, capacity=5)
    with app.app_context():
        service = app.extensions["services"].registrations
        service.register("2024001", activity.activity_id)
        service.register("2024002", activity.activity_id)
        messages = app.extensions["services"].messages
        assert messages.unread_count("2024001") == 1
        assert messages.mark_all_read("2024001") == 1
        assert messages.unread_count("2024001") == 0


def test_notification_attempt_sent_record(app):
    activity = make_activity(app)
    with app.app_context():
        app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
        rows = db.get_db().execute(
            "SELECT channel, status, error FROM notification_attempt ORDER BY channel"
        ).fetchall()
    assert count_rows(app, "notification_attempt") == 2
    statuses = {row["channel"]: row["status"] for row in rows}
    assert statuses == {"email": "SENT", "in_app": "SENT"}


def test_pending_registration_creates_pending_message(app):
    activity = make_activity(app, policy=PolicyType.APPROVAL)
    with app.app_context():
        app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
    row = fetch_one(app, "SELECT content FROM message WHERE student_id='2024001'")
    assert "等待管理员审核" in row["content"]
    assert count_rows(app, "message") == 1
