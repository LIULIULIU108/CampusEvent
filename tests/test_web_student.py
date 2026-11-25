"""学生端 HTTP 集成测试。"""

from __future__ import annotations

from tests.helpers import (
    NOW,
    count_rows,
    fetch_one,
    login,
    make_activity,
)


def test_login_student_redirects_to_activities(app):
    client = app.test_client()
    response = login(client, "2024001")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/activities")


def test_login_admin_redirects_to_admin(app):
    client = app.test_client()
    response = login(client, "admin", "admin123")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/admin/")


def test_login_wrong_password(app):
    client = app.test_client()
    response = login(client, "2024001", "wrong", follow_redirects=True)
    assert response.status_code == 200
    assert "账号或密码错误" in response.get_data(as_text=True)


def test_login_empty_fields(app):
    client = app.test_client()
    response = client.post("/login", data={"account_id": "", "password": ""})
    assert response.status_code == 200
    text = response.get_data(as_text=True)
    assert "请填写账号" in text
    assert "请填写密码" in text


def test_protected_route_redirects_to_login(app):
    client = app.test_client()
    response = client.get("/activities")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_student_cannot_access_admin(student_client):
    response = student_client.get("/admin/")
    assert response.status_code == 403


def test_admin_cannot_register(admin_client, app):
    activity = make_activity(app)
    response = admin_client.post(f"/activities/{activity.activity_id}/registrations")
    assert response.status_code == 403
    assert count_rows(app, "registration") == 0


def test_activities_search(student_client, app):
    make_activity(app, title="数据结构讲座")
    make_activity(app, title="校园歌手大赛")
    response = student_client.get("/activities?q=讲座")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "数据结构讲座" in text
    assert "校园歌手大赛" not in text


def test_activity_detail_shows_registration_status(student_client, app):
    activity = make_activity(app)
    student_client.post(f"/activities/{activity.activity_id}/registrations")
    response = student_client.get(f"/activities/{activity.activity_id}")
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "已通过" in text
    assert "取消报名" in text


def test_register_via_http_creates_message(student_client, app):
    activity = make_activity(app)
    response = student_client.post(
        f"/activities/{activity.activity_id}/registrations", follow_redirects=True
    )
    text = response.get_data(as_text=True)
    assert response.status_code == 200
    assert "报名成功" in text
    messages = student_client.get("/me/messages").get_data(as_text=True)
    assert "报名成功" in messages
    assert count_rows(app, "message", "student_id=?", ("2024001",)) == 1


def test_cancel_via_http(student_client, app):
    activity = make_activity(app)
    student_client.post(f"/activities/{activity.activity_id}/registrations")
    row = fetch_one(
        app,
        "SELECT registration_id FROM registration WHERE activity_id=? AND student_id=?",
        (activity.activity_id, "2024001"),
    )
    response = student_client.post(
        f"/registrations/{row['registration_id']}/cancel",
        data={"next": "/me/registrations"},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert "已取消报名" in response.get_data(as_text=True)
    assert fetch_one(
        app, "SELECT status FROM registration WHERE registration_id=?",
        (row["registration_id"],),
    )["status"] == "CANCELLED"


def test_mark_message_read_via_http(student_client, app):
    activity = make_activity(app)
    student_client.post(f"/activities/{activity.activity_id}/registrations")
    row = fetch_one(app, "SELECT message_id FROM message WHERE student_id='2024001'")
    response = student_client.post(
        f"/me/messages/{row['message_id']}/read", follow_redirects=True
    )
    assert response.status_code == 200
    assert fetch_one(
        app, "SELECT is_read FROM message WHERE message_id=?", (row["message_id"],)
    )["is_read"] == 1


def test_mark_all_messages_read_via_http(student_client, app):
    activity = make_activity(app, capacity=5)
    student_client.post(f"/activities/{activity.activity_id}/registrations")
    response = student_client.post("/me/messages/read-all", follow_redirects=True)
    assert response.status_code == 200
    assert count_rows(app, "message", "student_id=? AND is_read=0", ("2024001",)) == 0


def test_activity_not_found(student_client):
    response = student_client.get("/activities/9999")
    assert response.status_code == 404


def test_logout(student_client):
    response = student_client.post("/logout", follow_redirects=True)
    assert response.status_code == 200
    assert "登录" in response.get_data(as_text=True)
    response = student_client.get("/activities")
    assert response.status_code == 302


def test_started_activity_hides_register_button(student_client, app):
    activity = make_activity(app, start_at=NOW)
    response = student_client.get(f"/activities/{activity.activity_id}")
    text = response.get_data(as_text=True)
    assert "活动已开始" in text
    assert "立即报名" not in text
