"""报名策略（Strategy）与策略注册表。"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Iterable

from .capacity import CapacityChecker
from .enums import PolicyType, RegistrationStatus
from .errors import UnsupportedPolicyError
from .models import PolicyDecision, RegistrationContext


class RegistrationPolicy(ABC):
    """报名规则抽象：只负责决定受理结果与目标状态。"""

    policy_type: PolicyType

    @abstractmethod
    def decide(self, ctx: RegistrationContext) -> PolicyDecision:
        raise NotImplementedError


class DirectRegistrationPolicy(RegistrationPolicy):
    policy_type = PolicyType.DIRECT

    def __init__(self, capacity: CapacityChecker) -> None:
        self.capacity = capacity

    def decide(self, ctx: RegistrationContext) -> PolicyDecision:
        if self.capacity.has_capacity(ctx.activity, ctx.approved_count):
            return PolicyDecision(True, RegistrationStatus.APPROVED)
        return PolicyDecision(False, reason="名额已满，无法报名")


class ApprovalRegistrationPolicy(RegistrationPolicy):
    policy_type = PolicyType.APPROVAL

    def decide(self, ctx: RegistrationContext) -> PolicyDecision:
        # 提交阶段不占名额；名额在管理员批准时再次检查。
        return PolicyDecision(True, RegistrationStatus.PENDING)


class PolicyRegistry:
    """按活动报名方式选择策略；未知类型显式失败，避免静默降级。"""

    def __init__(self, policies: Iterable[RegistrationPolicy]) -> None:
        self._policies = {policy.policy_type: policy for policy in policies}

    def resolve(self, policy_type: PolicyType | str) -> RegistrationPolicy:
        try:
            key = PolicyType(policy_type)
        except ValueError as exc:
            raise UnsupportedPolicyError(f"未支持的报名方式：{policy_type}") from exc
        try:
            return self._policies[key]
        except KeyError as exc:
            raise UnsupportedPolicyError(f"未注册报名策略：{policy_type}") from exc
