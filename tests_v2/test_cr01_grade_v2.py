"""CR-01：年级限定直接报名测试（change-v2）。"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app_v2.domain.capacity import CapacityChecker
from app_v2.domain.enums import PolicyType, RegistrationStatus
from app_v2.domain.errors import ConflictError, DomainError
from app_v2.domain.models import Activity, RegistrationContext, Student
from app_v2.domain.policies import (
    ApprovalRegistrationPolicy,
    DirectRegistrationPolicy,
    GradeLimitedDirectRegistrationPolicy,
    PolicyRegistry,
)
from tests_v2.helpers import NOW, active_registration, count_rows, make_activity


def context(grade: int, *, capacity: int = 10, approved: int = 0):
    activity = Activity(
        activity_id=1,
        title="年级限定活动",
        category="测试",
        start_at=NOW + timedelta(days=3),
        location="A101",
        capacity=capacity,
        policy_type=PolicyType.GRADE_DIRECT,
    )
    student = Student("2024001", "张三", "hash", grade=grade)
    return RegistrationContext(activity, student, approved, NOW)


def test_policy_allows_grade_two_and_three():
    policy = GradeLimitedDirectRegistrationPolicy(CapacityChecker())
    for grade in (2, 3):
        decision = policy.decide(context(grade))
        assert decision.accepted is True
        assert decision.status is RegistrationStatus.APPROVED


def test_policy_rejects_grade_one_and_four_with_reason():
    policy = GradeLimitedDirectRegistrationPolicy(CapacityChecker())
    for grade in (1, 4):
        decision = policy.decide(context(grade))
        assert decision.accepted is False
        assert "仅限大二、大三" in decision.reason


def test_policy_still_checks_capacity():
    policy = GradeLimitedDirectRegistrationPolicy(CapacityChecker())
    decision = policy.decide(context(2, capacity=1, approved=1))
    assert decision.accepted is False
    assert "名额已满" in decision.reason


def test_registry_resolves_grade_policy():
    registry = PolicyRegistry(
        [
            DirectRegistrationPolicy(CapacityChecker()),
            ApprovalRegistrationPolicy(),
            GradeLimitedDirectRegistrationPolicy(CapacityChecker()),
        ]
    )
    assert registry.resolve(PolicyType.GRADE_DIRECT).policy_type is PolicyType.GRADE_DIRECT


def test_service_grade_two_and_three_can_register(app):
    activity = make_activity(app, policy=PolicyType.GRADE_DIRECT, capacity=5)
    with app.app_context():
        service = app.extensions["services"].registrations
        first = service.register("2024001", activity.activity_id)
        second = service.register("2024002", activity.activity_id)
    assert first.status is RegistrationStatus.APPROVED
    assert second.status is RegistrationStatus.APPROVED


def test_service_grade_one_and_four_rejected(app):
    activity = make_activity(app, policy=PolicyType.GRADE_DIRECT, capacity=5)
    with app.app_context():
        service = app.extensions["services"].registrations
        with pytest.raises(DomainError, match="仅限大二、大三"):
            service.register("2024003", activity.activity_id)
        with pytest.raises(DomainError, match="仅限大二、大三"):
            service.register("2024004", activity.activity_id)
    assert count_rows(app, "registration", "activity_id=?", (activity.activity_id,)) == 0


def test_service_grade_limited_obeys_duplicate_and_capacity(app):
    activity = make_activity(app, policy=PolicyType.GRADE_DIRECT, capacity=1)
    with app.app_context():
        service = app.extensions["services"].registrations
        service.register("2024001", activity.activity_id)
        with pytest.raises(ConflictError):
            service.register("2024001", activity.activity_id)
        with pytest.raises(DomainError, match="名额已满"):
            service.register("2024002", activity.activity_id)
    assert active_registration(app, activity.activity_id, "2024001") is not None
    assert active_registration(app, activity.activity_id, "2024002") is None


def test_service_grade_limited_obeys_start_time(app):
    activity = make_activity(
        app,
        policy=PolicyType.GRADE_DIRECT,
        start_at=NOW - timedelta(hours=1),
    )
    with app.app_context():
        with pytest.raises(DomainError, match="活动已开始"):
            app.extensions["services"].registrations.register(
                "2024001", activity.activity_id
            )


def test_activity_service_can_create_grade_limited(app):
    form = {
        "title": "年级限定新活动",
        "category": "学术讲座",
        "start_at": (NOW + timedelta(days=4)).strftime("%Y-%m-%dT%H:%M"),
        "location": "A101",
        "capacity": "10",
        "policy_type": "GRADE_DIRECT",
    }
    with app.app_context():
        activity = app.extensions["services"].activities.create(form)
    assert activity.policy_type is PolicyType.GRADE_DIRECT
