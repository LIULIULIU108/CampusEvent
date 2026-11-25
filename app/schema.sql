-- CampusEvent baseline-v1 schema
-- SQLite; 外键在连接级开启（app/db.py）。

CREATE TABLE IF NOT EXISTS student (
    student_id   TEXT PRIMARY KEY,
    name         TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 60),
    password_hash TEXT NOT NULL,
    created_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS activity (
    activity_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    title        TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
    category     TEXT NOT NULL CHECK (length(category) BETWEEN 1 AND 40),
    start_at     TEXT NOT NULL,
    location     TEXT NOT NULL CHECK (length(location) BETWEEN 1 AND 100),
    capacity     INTEGER NOT NULL CHECK (capacity > 0),
    policy_type  TEXT NOT NULL CHECK (policy_type IN ('DIRECT', 'APPROVAL')),
    created_at   TEXT NOT NULL,
    updated_at   TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS registration (
    registration_id INTEGER PRIMARY KEY AUTOINCREMENT,
    activity_id     INTEGER NOT NULL REFERENCES activity(activity_id),
    student_id      TEXT NOT NULL REFERENCES student(student_id),
    status          TEXT NOT NULL CHECK (
                        status IN ('PENDING', 'APPROVED', 'REJECTED', 'CANCELLED')
                    ),
    created_at      TEXT NOT NULL,
    updated_at      TEXT NOT NULL
);

-- 同一学生对同一活动最多一条有效报名；取消/拒绝保留历史，允许再次申请。
CREATE UNIQUE INDEX IF NOT EXISTS ux_registration_active
    ON registration(activity_id, student_id)
    WHERE status IN ('PENDING', 'APPROVED');

CREATE INDEX IF NOT EXISTS ix_registration_activity_status
    ON registration(activity_id, status);

CREATE INDEX IF NOT EXISTS ix_registration_student
    ON registration(student_id, created_at);

CREATE TABLE IF NOT EXISTS message (
    message_id  INTEGER PRIMARY KEY AUTOINCREMENT,
    student_id  TEXT NOT NULL REFERENCES student(student_id),
    activity_id INTEGER REFERENCES activity(activity_id) ON DELETE SET NULL,
    content     TEXT NOT NULL,
    is_read     INTEGER NOT NULL DEFAULT 0 CHECK (is_read IN (0, 1)),
    created_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_message_student_read
    ON message(student_id, is_read, created_at);

-- 通知渠道尝试：event_id + channel 唯一，用于幂等和失败留痕。
CREATE TABLE IF NOT EXISTS notification_attempt (
    event_id   TEXT NOT NULL,
    channel    TEXT NOT NULL,
    status     TEXT NOT NULL CHECK (status IN ('PENDING', 'SENT', 'FAILED')),
    error      TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL,
    PRIMARY KEY (event_id, channel)
);
