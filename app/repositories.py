"""SQLite 仓储：参数化 SQL 与行映射。"""

from __future__ import annotations

import sqlite3
from datetime import datetime

from .domain.enums import PolicyType, RegistrationStatus
from .domain.models import (
    Activity,
    Message,
    Registration,
    RegistrationWithStudent,
    Student,
)


def _dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value)


def _student(row: sqlite3.Row) -> Student:
    return Student(
        student_id=row["student_id"],
        name=row["name"],
        password_hash=row["password_hash"],
        created_at=_dt(row["created_at"]),
    )


def _activity(row: sqlite3.Row) -> Activity:
    return Activity(
        activity_id=row["activity_id"],
        title=row["title"],
        category=row["category"],
        start_at=_dt(row["start_at"]),
        location=row["location"],
        capacity=row["capacity"],
        policy_type=PolicyType(row["policy_type"]),
        created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]),
    )


def _registration(row: sqlite3.Row) -> Registration:
    return Registration(
        registration_id=row["registration_id"],
        activity_id=row["activity_id"],
        student_id=row["student_id"],
        status=RegistrationStatus(row["status"]),
        created_at=_dt(row["created_at"]),
        updated_at=_dt(row["updated_at"]),
    )


def _message(row: sqlite3.Row) -> Message:
    return Message(
        message_id=row["message_id"],
        student_id=row["student_id"],
        activity_id=row["activity_id"],
        content=row["content"],
        is_read=bool(row["is_read"]),
        created_at=_dt(row["created_at"]),
    )


class StudentRepository:
    def get(self, conn: sqlite3.Connection, student_id: str) -> Student | None:
        row = conn.execute(
            "SELECT * FROM student WHERE student_id = ?", (student_id,)
        ).fetchone()
        return _student(row) if row else None

    def create(self, conn: sqlite3.Connection, student: Student) -> None:
        conn.execute(
            "INSERT INTO student(student_id, name, password_hash, created_at) "
            "VALUES (?, ?, ?, ?)",
            (
                student.student_id,
                student.name,
                student.password_hash,
                (student.created_at or datetime.now()).isoformat(),
            ),
        )

    def count(self, conn: sqlite3.Connection) -> int:
        return conn.execute("SELECT COUNT(*) FROM student").fetchone()[0]


class ActivityRepository:
    def get(self, conn: sqlite3.Connection, activity_id: int) -> Activity | None:
        row = conn.execute(
            "SELECT * FROM activity WHERE activity_id = ?", (activity_id,)
        ).fetchone()
        return _activity(row) if row else None

    def list_all(self, conn: sqlite3.Connection, query: str | None = None) -> list[Activity]:
        sql = "SELECT * FROM activity"
        params: list[object] = []
        if query:
            sql += " WHERE title LIKE ?"
            params.append(f"%{query}%")
        sql += " ORDER BY start_at ASC, activity_id ASC"
        return [_activity(row) for row in conn.execute(sql, params).fetchall()]

    def count_all(self, conn: sqlite3.Connection) -> int:
        return conn.execute("SELECT COUNT(*) FROM activity").fetchone()[0]

    def create(
        self,
        conn: sqlite3.Connection,
        *,
        title: str,
        category: str,
        start_at: datetime,
        location: str,
        capacity: int,
        policy_type: PolicyType,
        now: datetime,
    ) -> Activity:
        cur = conn.execute(
            "INSERT INTO activity(title, category, start_at, location, capacity, "
            "policy_type, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
            (
                title,
                category,
                start_at.isoformat(),
                location,
                capacity,
                policy_type.value,
                now.isoformat(),
                now.isoformat(),
            ),
        )
        activity = self.get(conn, int(cur.lastrowid))
        assert activity is not None
        return activity

    def update(
        self,
        conn: sqlite3.Connection,
        activity_id: int,
        *,
        title: str,
        category: str,
        start_at: datetime,
        location: str,
        capacity: int,
        policy_type: PolicyType,
        now: datetime,
    ) -> Activity | None:
        conn.execute(
            "UPDATE activity SET title=?, category=?, start_at=?, location=?, "
            "capacity=?, policy_type=?, updated_at=? WHERE activity_id=?",
            (
                title,
                category,
                start_at.isoformat(),
                location,
                capacity,
                policy_type.value,
                now.isoformat(),
                activity_id,
            ),
        )
        return self.get(conn, activity_id)

    def delete(self, conn: sqlite3.Connection, activity_id: int) -> bool:
        cur = conn.execute("DELETE FROM activity WHERE activity_id = ?", (activity_id,))
        return cur.rowcount == 1


class RegistrationRepository:
    def get(
        self, conn: sqlite3.Connection, registration_id: int
    ) -> Registration | None:
        row = conn.execute(
            "SELECT * FROM registration WHERE registration_id = ?", (registration_id,)
        ).fetchone()
        return _registration(row) if row else None

    def get_active(
        self, conn: sqlite3.Connection, activity_id: int, student_id: str
    ) -> Registration | None:
        row = conn.execute(
            "SELECT * FROM registration WHERE activity_id=? AND student_id=? "
            "AND status IN ('PENDING','APPROVED')",
            (activity_id, student_id),
        ).fetchone()
        return _registration(row) if row else None

    def create(
        self,
        conn: sqlite3.Connection,
        *,
        activity_id: int,
        student_id: str,
        status: RegistrationStatus,
        now: datetime,
    ) -> Registration:
        cur = conn.execute(
            "INSERT INTO registration(activity_id, student_id, status, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (activity_id, student_id, status.value, now.isoformat(), now.isoformat()),
        )
        registration = self.get(conn, int(cur.lastrowid))
        assert registration is not None
        return registration

    def update_status(
        self,
        conn: sqlite3.Connection,
        registration_id: int,
        status: RegistrationStatus,
        now: datetime,
        *,
        expected: RegistrationStatus | None = None,
    ) -> bool:
        sql = "UPDATE registration SET status=?, updated_at=? WHERE registration_id=?"
        params: list[object] = [status.value, now.isoformat(), registration_id]
        if expected is not None:
            sql += " AND status=?"
            params.append(expected.value)
        cur = conn.execute(sql, params)
        return cur.rowcount == 1

    def list_for_student(
        self, conn: sqlite3.Connection, student_id: str
    ) -> list[Registration]:
        rows = conn.execute(
            "SELECT * FROM registration WHERE student_id=? "
            "ORDER BY created_at DESC, registration_id DESC",
            (student_id,),
        ).fetchall()
        return [_registration(row) for row in rows]

    def list_for_activity(
        self,
        conn: sqlite3.Connection,
        activity_id: int,
        statuses: tuple[RegistrationStatus, ...] | None = None,
    ) -> list[Registration]:
        sql = "SELECT * FROM registration WHERE activity_id=?"
        params: list[object] = [activity_id]
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            sql += f" AND status IN ({placeholders})"
            params.extend(status.value for status in statuses)
        sql += " ORDER BY created_at ASC, registration_id ASC"
        return [_registration(row) for row in conn.execute(sql, params).fetchall()]

    def list_with_student(
        self,
        conn: sqlite3.Connection,
        activity_id: int,
        statuses: tuple[RegistrationStatus, ...] | None = None,
    ) -> list[RegistrationWithStudent]:
        sql = (
            "SELECT r.*, s.name AS student_name FROM registration r "
            "JOIN student s ON s.student_id = r.student_id WHERE r.activity_id=?"
        )
        params: list[object] = [activity_id]
        if statuses:
            placeholders = ",".join("?" for _ in statuses)
            sql += f" AND r.status IN ({placeholders})"
            params.extend(status.value for status in statuses)
        sql += " ORDER BY r.created_at ASC, r.registration_id ASC"
        rows = conn.execute(sql, params).fetchall()
        return [
            RegistrationWithStudent(
                registration=_registration(row), student_name=row["student_name"]
            )
            for row in rows
        ]

    def count_by_status(
        self, conn: sqlite3.Connection, activity_id: int, status: RegistrationStatus
    ) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM registration WHERE activity_id=? AND status=?",
            (activity_id, status.value),
        ).fetchone()[0]

    def count_approved(self, conn: sqlite3.Connection, activity_id: int) -> int:
        return self.count_by_status(conn, activity_id, RegistrationStatus.APPROVED)

    def count_pending(self, conn: sqlite3.Connection, activity_id: int) -> int:
        return self.count_by_status(conn, activity_id, RegistrationStatus.PENDING)

    def count_for_activity(self, conn: sqlite3.Connection, activity_id: int) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM registration WHERE activity_id=?", (activity_id,)
        ).fetchone()[0]

    def count_for_student(self, conn: sqlite3.Connection, student_id: str) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM registration WHERE student_id=?", (student_id,)
        ).fetchone()[0]


class MessageRepository:
    def create(
        self,
        conn: sqlite3.Connection,
        *,
        student_id: str,
        activity_id: int | None,
        content: str,
        now: datetime,
    ) -> Message:
        cur = conn.execute(
            "INSERT INTO message(student_id, activity_id, content, is_read, created_at) "
            "VALUES (?, ?, ?, 0, ?)",
            (student_id, activity_id, content, now.isoformat()),
        )
        row = conn.execute(
            "SELECT * FROM message WHERE message_id=?", (int(cur.lastrowid),)
        ).fetchone()
        assert row is not None
        return _message(row)

    def list_for_student(
        self, conn: sqlite3.Connection, student_id: str
    ) -> list[Message]:
        rows = conn.execute(
            "SELECT * FROM message WHERE student_id=? "
            "ORDER BY created_at DESC, message_id DESC",
            (student_id,),
        ).fetchall()
        return [_message(row) for row in rows]

    def unread_count(self, conn: sqlite3.Connection, student_id: str) -> int:
        return conn.execute(
            "SELECT COUNT(*) FROM message WHERE student_id=? AND is_read=0",
            (student_id,),
        ).fetchone()[0]

    def mark_read(
        self, conn: sqlite3.Connection, message_id: int, student_id: str
    ) -> bool:
        cur = conn.execute(
            "UPDATE message SET is_read=1 WHERE message_id=? AND student_id=?",
            (message_id, student_id),
        )
        return cur.rowcount == 1

    def mark_all_read(self, conn: sqlite3.Connection, student_id: str) -> int:
        cur = conn.execute(
            "UPDATE message SET is_read=1 WHERE student_id=? AND is_read=0",
            (student_id,),
        )
        return cur.rowcount


class NotificationAttemptRepository:
    def claim(
        self, conn: sqlite3.Connection, event_id: str, channel: str, now: datetime
    ) -> bool:
        cur = conn.execute(
            "INSERT OR IGNORE INTO notification_attempt"
            "(event_id, channel, status, error, created_at, updated_at) "
            "VALUES (?, ?, 'PENDING', NULL, ?, ?)",
            (event_id, channel, now.isoformat(), now.isoformat()),
        )
        return cur.rowcount == 1

    def mark_sent(
        self, conn: sqlite3.Connection, event_id: str, channel: str, now: datetime
    ) -> None:
        conn.execute(
            "UPDATE notification_attempt SET status='SENT', error=NULL, updated_at=? "
            "WHERE event_id=? AND channel=?",
            (now.isoformat(), event_id, channel),
        )

    def mark_failed(
        self,
        conn: sqlite3.Connection,
        event_id: str,
        channel: str,
        error: str,
        now: datetime,
    ) -> None:
        conn.execute(
            "INSERT INTO notification_attempt"
            "(event_id, channel, status, error, created_at, updated_at) "
            "VALUES (?, ?, 'FAILED', ?, ?, ?) "
            "ON CONFLICT(event_id, channel) DO UPDATE SET "
            "status='FAILED', error=excluded.error, updated_at=excluded.updated_at",
            (event_id, channel, error, now.isoformat(), now.isoformat()),
        )
