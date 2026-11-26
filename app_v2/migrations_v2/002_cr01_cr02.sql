-- CR-01 + CR-02: v1 -> v2
-- 1) student 增加 grade（1—4）
-- 2) activity.policy_type 增加 GRADE_DIRECT
-- 3) 新增 email_outbox
--
-- 说明：SQLite 不能直接修改 CHECK 约束，因此重建 student/activity；
-- 外键在迁移调用方关闭，重建完成后由 db.py 重新开启。
-- 迁移前由 schema.sql 创建的 email_outbox 不会被覆盖。

BEGIN IMMEDIATE;

DROP TABLE IF EXISTS student_new;
CREATE TABLE student_new (
    student_id    TEXT PRIMARY KEY,
    name          TEXT NOT NULL CHECK (length(name) BETWEEN 1 AND 60),
    password_hash TEXT NOT NULL,
    created_at    TEXT NOT NULL,
    grade         INTEGER NOT NULL DEFAULT 1 CHECK (grade BETWEEN 1 AND 4)
);
INSERT INTO student_new(student_id, name, password_hash, created_at, grade)
SELECT student_id, name, password_hash, created_at, 1 FROM student;
DROP TABLE student;
ALTER TABLE student_new RENAME TO student;

DROP TABLE IF EXISTS activity_new;
CREATE TABLE activity_new (
    activity_id INTEGER PRIMARY KEY AUTOINCREMENT,
    title       TEXT NOT NULL CHECK (length(title) BETWEEN 1 AND 100),
    category    TEXT NOT NULL CHECK (length(category) BETWEEN 1 AND 40),
    start_at    TEXT NOT NULL,
    location    TEXT NOT NULL CHECK (length(location) BETWEEN 1 AND 100),
    capacity    INTEGER NOT NULL CHECK (capacity > 0),
    policy_type TEXT NOT NULL CHECK (policy_type IN ('DIRECT', 'APPROVAL', 'GRADE_DIRECT')),
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);
INSERT INTO activity_new(
    activity_id, title, category, start_at, location, capacity,
    policy_type, created_at, updated_at
)
SELECT activity_id, title, category, start_at, location, capacity,
       policy_type, created_at, updated_at
FROM activity;
DROP TABLE activity;
ALTER TABLE activity_new RENAME TO activity;

-- 重建 AUTOINCREMENT 表后修正序列，避免新活动 ID 回退。
DELETE FROM sqlite_sequence WHERE name = 'activity';
INSERT INTO sqlite_sequence(name, seq)
SELECT 'activity', COALESCE(MAX(activity_id), 0) FROM activity;

CREATE TABLE IF NOT EXISTS email_outbox (
    email_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id    TEXT NOT NULL UNIQUE,
    student_id  TEXT NOT NULL REFERENCES student(student_id),
    activity_id INTEGER REFERENCES activity(activity_id) ON DELETE SET NULL,
    recipient   TEXT NOT NULL,
    subject     TEXT NOT NULL,
    content     TEXT NOT NULL,
    status      TEXT NOT NULL CHECK (status IN ('PENDING', 'SENT', 'FAILED')),
    error       TEXT,
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS ix_email_outbox_created
    ON email_outbox(created_at);

COMMIT;
