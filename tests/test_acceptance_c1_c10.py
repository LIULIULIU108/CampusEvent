"""实验二初始验收用例 C1—C10 的自动化实现。"""

from __future__ import annotations

from datetime import timedelta

from app import create_app
from app.domain.enums import PolicyType
from tests.helpers import (
    NOW,
    active_registration,
    count_rows,
    fetch_one,
    login,
    make_activity,
)


def direct_activity(app, **kwargs):
    return make_activity(app, policy=PolicyType.DIRECT, **kwargs)


def approval_activity(app, **kwargs):
    return make_activity(app, policy=PolicyType.APPROVAL, **kwargs)


def student_client(app, account="2024001"):
    client = app.test_client()
    login(client, account)
    return client


def post_register(client, activity_id: int, follow_redirects: bool = True):
    return client.post(
        f"/activities/{activity_id}/registrations",
        follow_redirects=follow_redirects,
    )


def stats(app, activity):
    with app.app_context():
        return app.extensions["services"].statistics.for_activity(activity)


def test_c1_admin_creates_direct_activity(admin_client, app):
    response = admin_client.post(
        "/admin/activities/new",
        data={
            "title": "C1 直接报名活动",
            "category": "测试",
            "start_at": (NOW + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
            "location": "A101",
            "capacity": "2",
            "policy_type": "DIRECT",
        },
        follow_redirects=True,
    )
    assert response.status_code == 200
    row = fetch_one(app, "SELECT * FROM activity WHERE title='C1 直接报名活动'")
    assert row is not None
    assert row["capacity"] == 2
    assert row["policy_type"] == "DIRECT"


def test_c2_student_direct_registration_approved_and_notified(student_client, app):
    activity = direct_activity(app, title="C2 活动", capacity=2)
    response = post_register(student_client, activity.activity_id)
    assert response.status_code == 200
    assert "报名成功" in response.get_data(as_text=True)
    row = active_registration(app, activity.activity_id, "2024001")
    assert row is not None
    assert row["status"] == "APPROVED"
    message = fetch_one(app, "SELECT content FROM message WHERE student_id='2024001'")
    assert "报名成功" in message["content"]


def test_c3_duplicate_active_registration_rejected(student_client, app):
    activity = direct_activity(app, title="C3 活动", capacity=2)
    post_register(student_client, activity.activity_id)
    response = post_register(student_client, activity.activity_id)
    assert response.status_code == 200
    assert "请勿重复提交" in response.get_data(as_text=True)
    assert count_rows(
        app,
        "registration",
        "activity_id=? AND student_id=? AND status IN ('PENDING','APPROVED')",
        (activity.activity_id, "2024001"),
    ) == 1


def test_c4_capacity_full_blocks_third_student(app):
    activity = direct_activity(app, title="C4 活动", capacity=2)
    a = student_client(app, "2024001")
    b = student_client(app, "2024002")
    c = student_client(app, "2024003")
    assert post_register(a, activity.activity_id).status_code == 200
    assert post_register(b, activity.activity_id).status_code == 200
    response = post_register(c, activity.activity_id)
    assert "名额已满" in response.get_data(as_text=True)
    assert active_registration(app, activity.activity_id, "2024002") is not None
    assert active_registration(app, activity.activity_id, "2024003") is None
    assert count_rows(
        app,
        "registration",
        "activity_id=? AND status='APPROVED'",
        (activity.activity_id,),
    ) == 2


def test_c5_approval_activity_creates_pending(student_client, app):
    activity = approval_activity(app, title="C5 活动", capacity=2)
    response = post_register(student_client, activity.activity_id)
    assert response.status_code == 200
    assert "等待管理员审核" in response.get_data(as_text=True)
    row = active_registration(app, activity.activity_id, "2024001")
    assert row is not None
    assert row["status"] == "PENDING"


def test_c6_admin_approves_pending_and_notifies(admin_client, app):
    activity = approval_activity(app, title="C6 活动", capacity=2)
    client = student_client(app, "2024001")
    post_register(client, activity.activity_id)
    registration = active_registration(app, activity.activity_id, "2024001")
    response = admin_client.post(
        f"/admin/registrations/{registration['registration_id']}/approve",
        data={"activity_id": activity.activity_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert fetch_one(
        app,
        "SELECT status FROM registration WHERE registration_id=?",
        (registration["registration_id"],),
    )["status"] == "APPROVED"
    message = fetch_one(
        app,
        "SELECT content FROM message WHERE student_id='2024001' ORDER BY message_id DESC",
    )
    assert "审核通过" in message["content"]


def test_c7_admin_rejects_pending_and_notifies(admin_client, app):
    activity = approval_activity(app, title="C7 活动", capacity=2)
    client = student_client(app, "2024001")
    post_register(client, activity.activity_id)
    registration = active_registration(app, activity.activity_id, "2024001")
    response = admin_client.post(
        f"/admin/registrations/{registration['registration_id']}/reject",
        data={"activity_id": activity.activity_id},
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert fetch_one(
        app,
        "SELECT status FROM registration WHERE registration_id=?",
        (registration["registration_id"],),
    )["status"] == "REJECTED"
    message = fetch_one(
        app,
        "SELECT content FROM message WHERE student_id='2024001' ORDER BY message_id DESC",
    )
    assert "审核未通过" in message["content"]


def test_c8_approval_fails_when_capacity_full(admin_client, app):
    activity = approval_activity(app, title="C8 活动", capacity=1)
    a = student_client(app, "2024001")
    b = student_client(app, "2024002")
    post_register(a, activity.activity_id)
    post_register(b, activity.activity_id)
    ra = active_registration(app, activity.activity_id, "2024001")
    rb = active_registration(app, activity.activity_id, "2024002")

    admin_client.post(
        f"/admin/registrations/{ra['registration_id']}/approve",
        data={"activity_id": activity.activity_id},
        follow_redirects=True,
    )
    response = admin_client.post(
        f"/admin/registrations/{rb['registration_id']}/approve",
        data={"activity_id": activity.activity_id},
        follow_redirects=True,
    )
    assert "名额已满" in response.get_data(as_text=True)
    assert fetch_one(
        app,
        "SELECT status FROM registration WHERE registration_id=?",
        (rb["registration_id"],),
    )["status"] == "PENDING"
    assert count_rows(
        app,
        "registration",
        "activity_id=? AND status='APPROVED'",
        (activity.activity_id,),
    ) == 1


def test_c9_cancel_updates_status_and_stats(student_client, app):
    activity = direct_activity(app, title="C9 活动", capacity=2)
    post_register(student_client, activity.activity_id)
    registration = active_registration(app, activity.activity_id, "2024001")
    before = stats(app, activity)
    assert before.approved_count == 1
    assert before.remaining == 1

    response = student_client.post(
        f"/registrations/{registration['registration_id']}/cancel",
        follow_redirects=True,
    )
    assert response.status_code == 200
    assert fetch_one(
        app,
        "SELECT status FROM registration WHERE registration_id=?",
        (registration["registration_id"],),
    )["status"] == "CANCELLED"
    after = stats(app, activity)
    assert after.approved_count == 0
    assert after.remaining == 2


def test_c10_restart_preserves_data(app, student_client, tmp_path):
    activity = direct_activity(app, title="C10 活动", capacity=2)
    post_register(student_client, activity.activity_id)

    database = app.config["DATABASE"]
    new_app = create_app(
        {
            "DATABASE": database,
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_ID": "admin",
            "ADMIN_PASSWORD": "admin123",
            "ADMIN_NAME": "校园管理员",
        },
        clock=app.extensions["clock"],
    )
    with new_app.app_context():
        services = new_app.extensions["services"]
        activities = services.activities.list()
        assert any(item.title == "C10 活动" for item in activities)
        messages = services.messages.list_for_student("2024001")
        assert any("报名成功" in item.content for item in messages)
        registration = new_app.test_client()
        login(registration, "2024001")
        response = registration.get(f"/activities/{activity.activity_id}")
        assert response.status_code == 200
        assert "已通过" in response.get_data(as_text=True)
