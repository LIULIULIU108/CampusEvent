"""活动管理服务测试。"""

from __future__ import annotations

from datetime import timedelta

import pytest

from app.domain.enums import PolicyType
from app.domain.errors import ConflictError, ValidationError
from tests.helpers import NOW, count_rows, make_activity


def form(**overrides):
    data = {
        "title": "测试活动",
        "category": "学术讲座",
        "start_at": (NOW + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
        "location": "A101",
        "capacity": "2",
        "policy_type": "DIRECT",
    }
    data.update({key: str(value) for key, value in overrides.items()})
    return data


def register(app, activity_id: int, student_id: str):
    with app.app_context():
        return app.extensions["services"].registrations.register(
            student_id, activity_id
        )


def test_create_activity(app):
    with app.app_context():
        activity = app.extensions["services"].activities.create(
            form(title="新活动", capacity="5", policy_type="APPROVAL")
        )
    assert activity.activity_id > 0
    assert activity.title == "新活动"
    assert activity.capacity == 5
    assert activity.policy_type is PolicyType.APPROVAL


def test_create_activity_validation(app):
    with app.app_context():
        service = app.extensions["services"].activities
        with pytest.raises(ValidationError) as exc:
            service.create(form(title="", capacity="0", start_at=""))
    assert "title" in exc.value.errors
    assert "capacity" in exc.value.errors
    assert "start_at" in exc.value.errors


def test_create_activity_past_start_rejected(app):
    with app.app_context():
        with pytest.raises(ValidationError) as exc:
            app.extensions["services"].activities.create(
                form(start_at=(NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M"))
            )
    assert "start_at" in exc.value.errors


def test_update_capacity_below_approved_rejected(app):
    activity = make_activity(app, capacity=2)
    register(app, activity.activity_id, "2024001")
    register(app, activity.activity_id, "2024002")
    with app.app_context():
        with pytest.raises(ValidationError) as exc:
            app.extensions["services"].activities.update(
                activity.activity_id, form(capacity="1")
            )
    assert "capacity" in exc.value.errors


def test_update_capacity_equal_approved_allowed(app):
    activity = make_activity(app, capacity=2)
    register(app, activity.activity_id, "2024001")
    register(app, activity.activity_id, "2024002")
    with app.app_context():
        updated = app.extensions["services"].activities.update(
            activity.activity_id, form(capacity="2", title="改名后的活动")
        )
    assert updated.capacity == 2
    assert updated.title == "改名后的活动"


def test_update_policy_with_active_registration_rejected(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.DIRECT)
    register(app, activity.activity_id, "2024001")
    with app.app_context():
        with pytest.raises(ConflictError):
            app.extensions["services"].activities.update(
                activity.activity_id, form(policy_type="APPROVAL")
            )


def test_update_policy_after_only_cancelled_history_allowed(app):
    activity = make_activity(app, capacity=2, policy=PolicyType.DIRECT)
    registration = register(app, activity.activity_id, "2024001")
    with app.app_context():
        app.extensions["services"].registrations.cancel(
            "2024001", registration.registration_id
        )
        updated = app.extensions["services"].activities.update(
            activity.activity_id, form(policy_type="APPROVAL")
        )
    assert updated.policy_type is PolicyType.APPROVAL


def test_delete_activity_with_registration_rejected(app):
    activity = make_activity(app, )
    register(app, activity.activity_id, "2024001")
    with app.app_context():
        with pytest.raises(ConflictError):
            app.extensions["services"].activities.delete(activity.activity_id)
    assert count_rows(app, "activity", "activity_id=?", (activity.activity_id,)) == 1


def test_delete_activity_without_registration(app):
    activity = make_activity(app, )
    with app.app_context():
        app.extensions["services"].activities.delete(activity.activity_id)
    assert count_rows(app, "activity", "activity_id=?", (activity.activity_id,)) == 0


def test_search_by_title(app):
    make_activity(app, title="数据结构讲座")
    make_activity(app, title="校园歌手大赛")
    with app.app_context():
        items = app.extensions["services"].activities.list("讲座")
    assert [item.title for item in items] == ["数据结构讲座"]


def test_update_allows_unchanged_past_start(app):
    activity = make_activity(app, start_at=NOW - timedelta(days=1))
    data = form(start_at=activity.start_at.strftime("%Y-%m-%dT%H:%M"), title="历史活动改名")
    with app.app_context():
        updated = app.extensions["services"].activities.update(
            activity.activity_id, data
        )
    assert updated.title == "历史活动改名"


def test_registration_count(app):
    activity = make_activity(app, )
    register(app, activity.activity_id, "2024001")
    with app.app_context():
        assert app.extensions["services"].activities.registration_count(
            activity.activity_id
        ) == 1


def test_invalid_policy_value_rejected(app):
    with app.app_context():
        with pytest.raises(ValidationError) as exc:
            app.extensions["services"].activities.create(
                form(policy_type="UNKNOWN")
            )
    assert "policy_type" in exc.value.errors
