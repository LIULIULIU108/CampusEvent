"""v1 -> v2 数据库迁移测试（change-v2）。"""

from __future__ import annotations

import sqlite3

from app_v2 import create_app_v2, db
from app_v2.domain.enums import PolicyType
from app_v2.repositories import ActivityRepository
from tests_v2.helpers import NOW, FixedClock

V1_SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE student (
    student_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT NOT NULL
);
CREATE TABLE activity (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    category TEXT NOT NULL,
    start_at TEXT NOT NULL,
    location TEXT NOT NULL,
    capacity INTEGER NOT NULL CHECK (capacity > 0),
    policy_type TEXT NOT NULL CHECK (policy_type IN ('DIRECT', 'APPROVAL')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE TABLE registration (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id INTEGER NOT NULL REFERENCES activity(activity_id),
    student_id TEXT NOT NULL REFERENCES student(student_id),
    status TEXT NOT NULL CHECK (status IN ('PENDING','APPROVED','REJECTED','CANCELLED')),
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE UNIQUE INDEX ux_registration_active
    ON registration(activity_id, student_id)
    WHERE status IN ('PENDING', 'APPROVED');
CREATE TABLE message (
    message_id INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id TEXT NOT NULL REFERENCES student(student_id),
    activity_id INTEGER REFERENCES activity(activity_id) ON DELETE SET NULL,
    content TEXT NOT NULL,
    is_read INTEGER NOT NULL DEFAULT 0,
    created_at TEXT NOT NULL
);
CREATE TABLE notification_attempt (
    event_id TEXT NOT NULL,
    channel TEXT NOT NULL,
    status TEXT NOT NULL,
    error TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (event_id, channel)
);
INSERT INTO student(student_id, name, password_hash, created_at)
VALUES ('2024001', '张三', 'hash', '2026-11-25T10:00:00+08:00');
INSERT INTO activity(title, category, start_at, location, capacity, policy_type, created_at, updated_at)
VALUES ('v1 活动', '测试', '2026-11-28T14:00:00+08:00', 'A101', 2, 'DIRECT',
        '2026-11-25T10:00:00+08:00', '2026-11-25T10:00:00+08:00');
INSERT INTO registration(activity_id, student_id, status, created_at, updated_at)
VALUES (1, '2024001', 'APPROVED', '2026-11-25T10:00:00+08:00', '2026-11-25T10:00:00+08:00');
INSERT INTO message(student_id, activity_id, content, is_read, created_at)
VALUES ('2024001', 1, 'v1 消息', 0, '2026-11-25T10:00:00+08:00');
PRAGMA user_version = 1;
"""


def make_v1_database(path) -> None:
    conn = sqlite3.connect(path)
    try:
        conn.executescript(V1_SCHEMA)
        conn.commit()
    finally:
        conn.close()


def test_v1_to_v2_preserves_data_and_adds_columns(tmp_path):
    path = tmp_path / "v1.db"
    make_v1_database(path)
    app = create_app_v2(
        {
            "DATABASE": str(path),
            "TESTING": True,
            "SECRET_KEY": "test",
            "ADMIN_PASSWORD": "admin123",
            "PASSWORD_HASH_METHOD": "pbkdf2:sha256:1000",
        },
        clock=FixedClock(NOW),
    )
    with app.app_context():
        conn = db.get_db()
        assert conn.execute("PRAGMA user_version").fetchone()[0] == 2
        columns = {row["name"] for row in conn.execute("PRAGMA table_info(student)")}
        assert "grade" in columns
        assert conn.execute("SELECT grade FROM student WHERE student_id='2024001'").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM activity").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM registration").fetchone()[0] == 1
        assert conn.execute("SELECT COUNT(*) FROM message").fetchone()[0] == 1
        assert conn.execute("PRAGMA foreign_key_check").fetchall() == []
        tables = {
            row["name"]
            for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
        }
        assert "email_outbox" in tables

        new_activity = ActivityRepository().create(
            conn,
            title="v2 年级限定活动",
            category="测试",
            start_at=NOW,
            location="B201",
            capacity=5,
            policy_type=PolicyType.GRADE_DIRECT,
            now=NOW,
        )
        assert new_activity.activity_id == 2
