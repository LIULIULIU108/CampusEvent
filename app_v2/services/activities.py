"""活动管理用例。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo

from .. import db
from ..domain.enums import ACTIVE_STATUSES
from ..domain.errors import ConflictError, NotFoundError, ValidationError
from ..domain.models import Activity
from ..repositories import ActivityRepository, RegistrationRepository
from ..validation import validate_activity_form, validate_search


class ActivityService:
    def __init__(
        self,
        activities: ActivityRepository,
        registrations: RegistrationRepository,
        clock,
        tz: ZoneInfo,
    ) -> None:
        self.activities = activities
        self.registrations = registrations
        self.clock = clock
        self.tz = tz

    def list(self, query: str | None = None) -> list[Activity]:
        query = validate_search(query)
        conn = db.get_db()
        return self.activities.list_all(conn, query or None)

    def get(self, activity_id: int) -> Activity:
        conn = db.get_db()
        activity = self.activities.get(conn, activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        return activity

    def create(self, form) -> Activity:
        now = self.clock.now()
        data = validate_activity_form(form, now=now, tz=self.tz)
        conn = db.get_db()
        with db.transaction():
            return self.activities.create(conn, now=now, **data)

    def update(self, activity_id: int, form) -> Activity:
        now = self.clock.now()
        conn = db.get_db()
        with db.transaction():
            activity = self.activities.get(conn, activity_id)
            if activity is None:
                raise NotFoundError("活动不存在")

            data = validate_activity_form(
                form, now=now, tz=self.tz, existing=activity
            )

            approved = self.registrations.count_approved(conn, activity_id)
            if int(data["capacity"]) < approved:
                raise ValidationError(
                    {"capacity": f"人数上限不能低于当前已通过人数（{approved}）"}
                )

            if data["policy_type"] != activity.policy_type:
                active = self.registrations.list_for_activity(
                    conn, activity_id, ACTIVE_STATUSES
                )
                if active:
                    raise ConflictError(
                        "该活动已有有效报名，不能修改报名方式；请新建活动或先处理报名"
                    )

            updated = self.activities.update(
                conn, activity_id, now=now, **data
            )
            if updated is None:
                raise NotFoundError("活动不存在")
            return updated

    def registration_count(self, activity_id: int) -> int:
        conn = db.get_db()
        activity = self.activities.get(conn, activity_id)
        if activity is None:
            raise NotFoundError("活动不存在")
        return self.registrations.count_for_activity(conn, activity_id)

    def delete(self, activity_id: int) -> None:
        conn = db.get_db()
        with db.transaction():
            activity = self.activities.get(conn, activity_id)
            if activity is None:
                raise NotFoundError("活动不存在")
            count = self.registrations.count_for_activity(conn, activity_id)
            if count > 0:
                raise ConflictError(
                    f"该活动已有 {count} 条报名记录，不能删除；可选择保留活动"
                )
            self.activities.delete(conn, activity_id)
