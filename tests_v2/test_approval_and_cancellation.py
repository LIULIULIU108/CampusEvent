"""审批、取消与统计口径测试。"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app_v2.domain.enums import PolicyType, RegistrationStatus
from app_v2.domain.errors import ConflictError, DomainError
from tests_v2.helpers import NOW, active_registration, count_rows, fetch_one, make_activity


def register(app, activity_id: int, student_id: str):
    with app.app_context():
        return app.extensions["services"].registrations.register(
            student_id, activity_id
        )


def registration_id(app, activity_id: int, student_id: str) -> int:
    row = fetch_one(
        app,
        "SELECT registration_id FROM registration WHERE activity_id=? AND student_id=? "
        "ORDER BY registration_id DESC LIMIT 1",
        (activity_id, student_id),
    )
    assert row is not None
    return row["registration_id"]


def test_approval_submission_is_pending_and_notifies(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    registration = register(app, activity.activity_id, "2024001")
    assert registration.status is RegistrationStatus.PENDING
    assert active_registration(app, activity.activity_id) is not None
    row = fetch_one(app, "SELECT content FROM message WHERE student_id='2024001'")
    assert "等待管理员审核" in row["content"]


def test_approve_pending_approves_and_notifies(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    register(app, activity.activity_id, "2024001")
    rid = registration_id(app, activity.activity_id, "2024001")
    with app.app_context():
        app.extensions["services"].approvals.approve(rid)
    row = fetch_one(app, "SELECT status FROM registration WHERE registration_id=?", (rid,))
    assert row["status"] == "APPROVED"
    messages = fetch_one(
        app,
        "SELECT content FROM message WHERE student_id='2024001' ORDER BY message_id DESC",
    )
    assert "审核通过" in messages["content"]


def test_reject_pending_rejects_and_notifies(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    register(app, activity.activity_id, "2024001")
    rid = registration_id(app, activity.activity_id, "2024001")
    with app.app_context():
        app.extensions["services"].approvals.reject(rid)
    row = fetch_one(app, "SELECT status FROM registration WHERE registration_id=?", (rid,))
    assert row["status"] == "REJECTED"
    message = fetch_one(
        app,
        "SELECT content FROM message WHERE student_id='2024001' ORDER BY message_id DESC",
    )
    assert "审核未通过" in message["content"]


def test_approve_full_keeps_pending(app):
    activity = make_activity(app, capacity=1, policy=PolicyType.APPROVAL)
    register(app, activity.activity_id, "2024001")
    register(app, activity.activity_id, "2024002")
    rid_a = registration_id(app, activity.activity_id, "2024001")
    rid_b = registration_id(app, activity.activity_id, "2024002")

    with app.app_context():
        app.extensions["services"].approvals.approve(rid_a)
        with pytest.raises(DomainError, match="名额已满"):
            app.extensions["services"].approvals.approve(rid_b)

    assert fetch_one(
        app, "SELECT status FROM registration WHERE registration_id=?", (rid_a,)
    )["status"] == "APPROVED"
    assert fetch_one(
        app, "SELECT status FROM registration WHERE registration_id=?", (rid_b,)
    )["status"] == "PENDING"
    assert count_rows(
        app,
        "registration",
        "activity_id=? AND status='APPROVED'",
        (activity.activity_id,),
    ) == 1


def test_approve_non_pending_conflict(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.DIRECT)
    registration = register(app, activity.activity_id, "2024001")
    with app.app_context():
        with pytest.raises(ConflictError):
            app.extensions["services"].approvals.approve(registration.registration_id)


def test_approve_twice_conflict(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    register(app, activity.activity_id, "2024001")
    rid = registration_id(app, activity.activity_id, "2024001")
    with app.app_context():
        app.extensions["services"].approvals.approve(rid)
        with pytest.raises(ConflictError):
            app.extensions["services"].approvals.approve(rid)


def test_approve_after_start_rejected_but_reject_allowed(app, clock):
    activity = make_activity(app, 
        capacity=2,
        policy=PolicyType.APPROVAL,
        start_at=NOW + timedelta(hours=1),
    )
    register(app, activity.activity_id, "2024001")
    register(app, activity.activity_id, "2024002")
    rid_a = registration_id(app, activity.activity_id, "2024001")
    rid_b = registration_id(app, activity.activity_id, "2024002")

    clock.set(NOW + timedelta(hours=2))
    with app.app_context():
        with pytest.raises(DomainError, match="活动已开始"):
            app.extensions["services"].approvals.approve(rid_a)
        app.extensions["services"].approvals.reject(rid_b)

    assert fetch_one(
        app, "SELECT status FROM registration WHERE registration_id=?", (rid_a,)
    )["status"] == "PENDING"
    assert fetch_one(
        app, "SELECT status FROM registration WHERE registration_id=?", (rid_b,)
    )["status"] == "REJECTED"


def test_cancel_pending_updates_stats(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    registration = register(app, activity.activity_id, "2024001")
    with app.app_context():
        stats_before = app.extensions["services"].statistics.for_activity(activity)
        app.extensions["services"].registrations.cancel(
            "2024001", registration.registration_id
        )
        stats_after = app.extensions["services"].statistics.for_activity(activity)
    assert stats_before.pending_count == 1
    assert stats_after.pending_count == 0
    assert stats_after.remaining == 2


def test_capacity_counts_only_approved(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    register(app, activity.activity_id, "2024001")
    register(app, activity.activity_id, "2024002")
    with app.app_context():
        stats = app.extensions["services"].statistics.for_activity(activity)
    assert stats.approved_count == 0
    assert stats.pending_count == 2
    assert stats.remaining == 2


def test_list_registrations_with_student_names(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.APPROVAL)
    register(app, activity.activity_id, "2024001")
    with app.app_context():
        items = app.extensions["services"].approvals.list_registrations(
            activity.activity_id
        )
    assert len(items) == 1
    assert items[0].student_name == "张三"
