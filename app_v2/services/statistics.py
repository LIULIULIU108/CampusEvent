"""活动统计。"""

from __future__ import annotations

from collections import OrderedDict

from .. import db
from ..domain.models import Activity, ActivityStats
from ..repositories import ActivityRepository, RegistrationRepository


class StatisticsService:
    def __init__(
        self,
        activities: ActivityRepository,
        registrations: RegistrationRepository,
    ) -> None:
        self.activities = activities
        self.registrations = registrations

    def for_activity(self, activity: Activity, conn=None) -> ActivityStats:
        conn = conn or db.get_db()
        approved = self.registrations.count_approved(conn, activity.activity_id)
        pending = self.registrations.count_pending(conn, activity.activity_id)
        return ActivityStats(
            activity_id=activity.activity_id,
            capacity=activity.capacity,
            approved_count=approved,
            pending_count=pending,
            remaining=max(0, activity.capacity - approved),
        )

    def for_activities(
        self, activities: list[Activity], conn=None
    ) -> "OrderedDict[int, ActivityStats]":
        conn = conn or db.get_db()
        result: OrderedDict[int, ActivityStats] = OrderedDict()
        for activity in activities:
            result[activity.activity_id] = self.for_activity(activity, conn)
        return result

    def dashboard(self, conn=None) -> dict[str, int]:
        conn = conn or db.get_db()
        activities = self.activities.list_all(conn)
        stats = self.for_activities(activities, conn)
        return {
            "activity_count": len(activities),
            "approved_total": sum(item.approved_count for item in stats.values()),
            "pending_total": sum(item.pending_count for item in stats.values()),
        }
