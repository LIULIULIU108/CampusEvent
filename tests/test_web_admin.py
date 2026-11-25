"""管理端 HTTP 集成测试。"""

from __future__ import annotations

from datetime import timedelta

from tests.helpers import NOW, count_rows, fetch_one, make_activity


def activity_form(**overrides):
    data = {
        "title": "HTTP 新建活动",
        "category": "学术讲座",
        "start_at": (NOW + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
        "location": "A101",
        "capacity": "3",
        "policy_type": "DIRECT",
    }
    data.update({key: str(value) for key, value in overrides.items()})
    return data


def register(app, activity_id: int, student_id: str = "2024001"):
    with app.app_context():
        return app.extensions["services"].registrations.register(
            student_id, activity_id
        )


def test_admin_dashboard(admin_client, app):
    make_activity(app, title="仪表盘活动")
    response = admin_client.get("/admin/")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "仪表盘活动" in text
    assert "活动总数" in text


def test_create_activity_via_http(admin_client, app):
    response = admin_client.post(
        "/admin/activities/new", data=activity_form(), follow_redirects=True
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "HTTP 新建活动" in text
    assert count_rows(app, "activity", "title=?", ("HTTP 新建活动",)) == 1


def test_create_activity_validation_error(admin_client, app):
    response = admin_client.post(
        "/admin/activities/new", data=activity_form(title="", capacity="0")
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "请填写活动名称" in text
    assert "人数上限必须大于 0" in text
    assert count_rows(app, "activity") == 0


def test_edit_activity_via_http(admin_client, app):
    activity = make_activity(app)
    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/edit",
        data=activity_form(title="改名后的活动"),
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "改名后的活动" in response.get_data(as_text=True)


def test_edit_capacity_below_approved_shows_error(admin_client, app):
    activity = make_activity(app, capacity=2)
    register(app, activity.activity_id, "2024001")
    register(app, activity.activity_id, "2024002")
    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/edit",
        data=activity_form(capacity="1"),
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "人数上限不能低于" in text
    assert fetch_one(
        app, "SELECT capacity FROM activity WHERE activity_id=?", (activity.activity_id,)
    )["capacity"] == 2


def test_delete_activity_without_registration(admin_client, app):
    activity = make_activity(app)
    page = admin_client.get(f"/admin/activities/{activity.activity_id}/delete")
    assert "确认删除" in page.get_data(as_text=True)
    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert count_rows(app, "activity", "activity_id=?", (activity.activity_id,)) == 0


def test_delete_activity_with_registration_rejected(admin_client, app):
    activity = make_activity(app)
    register(app, activity.activity_id)
    page = admin_client.get(f"/admin/activities/{activity.activity_id}/delete")
    assert "不能删除" in page.get_data(as_text=True)
    response = admin_client.post(
        f"/admin/activities/{activity.activity_id}/delete", follow_redirects=True
    )
    assert response.status_code == 200
    assert count_rows(app, "activity", "activity_id=?", (activity.activity_id,)) == 1


def test_approve_via_http(admin_client, app):
    activity = make_activity(app, policy="APPROVAL")
    registration = register(app, activity.activity_id)
    response = admin_client.post(
        f"/admin/registrations/{registration.registration_id}/approve",
        data={"activity_id": activity.activity_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "已批准" in response.get_data(as_text=True)
    assert fetch_one(
        app,
        "SELECT status FROM registration WHERE registration_id=?",
        (registration.registration_id,),
    )["status"] == "APPROVED"


def test_reject_via_http(admin_client, app):
    activity = make_activity(app, policy="APPROVAL")
    registration = register(app, activity.activity_id)
    response = admin_client.post(
        f"/admin/registrations/{registration.registration_id}/reject",
        data={"activity_id": activity.activity_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "已拒绝" in response.get_data(as_text=True)
    assert fetch_one(
        app,
        "SELECT status FROM registration WHERE registration_id=?",
        (registration.registration_id,),
    )["status"] == "REJECTED"


def test_registrations_page_lists_pending(admin_client, app):
    activity = make_activity(app, policy="APPROVAL")
    register(app, activity.activity_id)
    response = admin_client.get(
        f"/admin/activities/{activity.activity_id}/registrations"
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "张三" in text
    assert "待审核（1）" in text
