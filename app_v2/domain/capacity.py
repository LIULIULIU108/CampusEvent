"""名额计算：策略与审批服务共享同一口径。"""

from __future__ import annotations

from .models import Activity


class CapacityChecker:
    def remaining(self, activity: Activity, approved_count: int) -> int:
        return max(0, activity.capacity - approved_count)

    def has_capacity(self, activity: Activity, approved_count: int) -> bool:
        return approved_count < activity.capacity
