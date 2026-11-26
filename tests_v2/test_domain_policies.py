"""策略、注册表与名额计算单测。"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app_v2.domain.capacity import CapacityChecker
from app_v2.domain.enums import PolicyType, RegistrationStatus
from app_v2.domain.errors import UnsupportedPolicyError
from app_v2.domain.models import (
    Activity,
    PolicyDecision,
    RegistrationContext,
    Student,
)
from app_v2.domain.policies import (
    ApprovalRegistrationPolicy,
    DirectRegistrationPolicy,
    PolicyRegistry,
)

TZ = ZoneInfo("Asia/Shanghai")
NOW = datetime(2026, 11, 25, 10, 0, tzinfo=TZ)


def make_context(capacity: int, approved: int, policy=PolicyType.DIRECT):
    activity = Activity(
        activity_id=1,
        title="测试活动",
        category="测试",
        start_at=NOW + timedelta(days=3),
        location="A101",
        capacity=capacity,
        policy_type=policy,
    )
    student = Student("2024001", "张三", "hash")
    return RegistrationContext(activity, student, approved, NOW)


def test_direct_policy_approves_when_capacity_available():
    policy = DirectRegistrationPolicy(CapacityChecker())
    decision = policy.decide(make_context(capacity=2, approved=1))
    assert decision.accepted is True
    assert decision.status is RegistrationStatus.APPROVED


def test_direct_policy_rejects_when_full():
    policy = DirectRegistrationPolicy(CapacityChecker())
    decision = policy.decide(make_context(capacity=2, approved=2))
    assert decision.accepted is False
    assert decision.status is None
    assert "名额已满" in decision.reason


def test_approval_policy_returns_pending():
    decision = ApprovalRegistrationPolicy().decide(
        make_context(capacity=1, approved=1, policy=PolicyType.APPROVAL)
    )
    assert decision.accepted is True
    assert decision.status is RegistrationStatus.PENDING


def test_registry_resolves_both_policies():
    registry = PolicyRegistry(
        [DirectRegistrationPolicy(CapacityChecker()), ApprovalRegistrationPolicy()]
    )
    assert registry.resolve(PolicyType.DIRECT).policy_type is PolicyType.DIRECT
    assert registry.resolve("APPROVAL").policy_type is PolicyType.APPROVAL


def test_registry_unknown_policy_raises():
    registry = PolicyRegistry([ApprovalRegistrationPolicy()])
    with pytest.raises(UnsupportedPolicyError):
        registry.resolve("UNKNOWN")
    with pytest.raises(UnsupportedPolicyError):
        registry.resolve(PolicyType.DIRECT)


def test_capacity_checker_remaining_never_negative():
    checker = CapacityChecker()
    activity = make_context(2, 0).activity
    assert checker.remaining(activity, 0) == 2
    assert checker.remaining(activity, 3) == 0
    assert checker.has_capacity(activity, 1) is True
    assert checker.has_capacity(activity, 2) is False


def test_policy_decision_shape_validation():
    with pytest.raises(ValueError):
        PolicyDecision(True)
    with pytest.raises(ValueError):
        PolicyDecision(False, RegistrationStatus.APPROVED)
