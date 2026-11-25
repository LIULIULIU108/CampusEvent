"""SQLite 持久化、约束与迁移版本测试。"""

from __future__ import annotations

import sqlite3

import pytest

from app import db
from app.domain.enums import PolicyType, RegistrationStatus
from tests.helpers import NOW, count_rows, fetch_one, make_activity


def test_schema_init_is_idempotent(app):
    with app.app_context():
        db.init_db()
        db.init_db()
        tables = {
            row["name"]
            for row in db.get_db()
            .execute("SELECT name FROM sqlite_master WHERE type='table'")
            .fetchall()
        }
    assert {"student", "activity", "registration", "message", "notification_attempt"} <= tables


def test_schema_version(app):
    with app.app_context():
        version = db.get_db().execute("PRAGMA user_version").fetchone()[0]
    assert version == 1


def test_foreign_keys_enabled(app):
    with app.app_context():
        value = db.get_db().execute("PRAGMA foreign_keys").fetchone()[0]
    assert value == 1


def test_status_check_constraint(app):
    activity = make_activity(app)
    with app.app_context():
        conn = db.get_db()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO registration(activity_id, student_id, status, created_at, updated_at) "
                "VALUES (?, '2024001', 'UNKNOWN', ?, ?)",
                (activity.activity_id, NOW.isoformat(), NOW.isoformat()),
            )


def test_capacity_check_constraint(app):
    with app.app_context():
        conn = db.get_db()
        with pytest.raises(sqlite3.IntegrityError):
            conn.execute(
                "INSERT INTO activity(title, category, start_at, location, capacity, "
                "policy_type, created_at, updated_at) VALUES (?, ?, ?, ?, 0, 'DIRECT', ?, ?)",
                ("非法容量", "测试", NOW.isoformat(), "A101", NOW.isoformat(), NOW.isoformat()),
            )


def test_cancelled_history_allows_new_active_registration(app):
    activity = make_activity(app, capacity=2)
    with app.app_context():
        service = app.extensions["services"].registrations
        first = service.register("2024001", activity.activity_id)
        service.cancel("2024001", first.registration_id)
        second = service.register("2024001", activity.activity_id)
    assert second.registration_id != first.registration_id
    assert count_rows(
        app,
        "registration",
        "activity_id=? AND student_id=? AND status='CANCELLED'",
        (activity.activity_id, "2024001"),
    ) == 1


def test_transaction_rollback_on_capacity_error(app):
    activity = make_activity(app, capacity=1)
    with app.app_context():
        service = app.extensions["services"].registrations
        service.register("2024001", activity.activity_id)
        with pytest.raises(Exception):
            service.register("2024002", activity.activity_id)
    assert count_rows(app, "registration", "activity_id=?", (activity.activity_id,)) == 1


def test_message_is_persisted(app):
    activity = make_activity(app)
    with app.app_context():
        app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
    row = fetch_one(app, "SELECT content, is_read FROM message WHERE student_id='2024001'")
    assert "报名成功" in row["content"]
    assert row["is_read"] == 0


def test_reopen_same_database_preserves_rows(app):
    activity = make_activity(app)
    with app.app_context():
        app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
    with app.app_context():
        conn = db.get_db()
        assert conn.execute("SELECT COUNT(*) FROM registration").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM message").fetchone()[0] == 1


def test_activity_policy_type_round_trip(app):
    activity = make_activity(app, policy=PolicyType.APPROVAL)
    with app.app_context():
        loaded = app.extensions["services"].activities.get(activity.activity_id)
    assert loaded.policy_type is PolicyType.APPROVAL
    assert isinstance(loaded.start_at.tzinfo, object)


def test_registration_status_enum_round_trip(app):
    activity = make_activity(app)
    with app.app_context():
        registration = app.extensions["services"].registrations.register(
            "2024001", activity.activity_id
        )
    assert registration.status is RegistrationStatus.APPROVED
