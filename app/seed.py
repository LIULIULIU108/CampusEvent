"""演示数据（仅在空库时写入）。"""

from __future__ import annotations

from datetime import timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from . import db
from .domain.enums import PolicyType
from .domain.models import Student
from .repositories import ActivityRepository, StudentRepository

STUDENTS = [
    ("2024001", "张三", "123456"),
    ("2024002", "李四", "123456"),
    ("2024003", "王五", "123456"),
]


def seed_students_only() -> dict[str, int]:
    conn = db.get_db()
    students = StudentRepository()
    if students.count(conn) > 0:
        return {"students": 0, "skipped": 1}

    now = current_app.extensions["clock"].now()
    with db.transaction():
        for student_id, name, password in STUDENTS:
            students.create(
                conn,
                Student(
                    student_id=student_id,
                    name=name,
                    password_hash=generate_password_hash(password),
                    created_at=now,
                ),
            )
    return {"students": len(STUDENTS), "skipped": 0}


def seed_demo() -> dict[str, int]:
    conn = db.get_db()
    students = StudentRepository()
    activities = ActivityRepository()

    if students.count(conn) > 0 or activities.count_all(conn) > 0:
        return {"students": 0, "activities": 0, "skipped": 1}

    now = current_app.extensions["clock"].now()
    hashes = {
        student_id: generate_password_hash(password)
        for student_id, _name, password in STUDENTS
    }

    with db.transaction():
        for student_id, name, _password in STUDENTS:
            students.create(
                conn,
                Student(
                    student_id=student_id,
                    name=name,
                    password_hash=hashes[student_id],
                    created_at=now,
                ),
            )

        base = now.replace(hour=14, minute=0, second=0, microsecond=0)
        rows = [
            (
                "数据结构期中复习讲座",
                "学术讲座",
                base + timedelta(days=3),
                "图书馆报告厅",
                2,
                PolicyType.DIRECT,
            ),
            (
                "校园歌手大赛",
                "文体活动",
                (base + timedelta(days=5)).replace(hour=19, minute=0),
                "大学生活动中心",
                2,
                PolicyType.APPROVAL,
            ),
            (
                "软件工程实验答疑",
                "学术讲座",
                (base + timedelta(days=7)).replace(hour=15, minute=30),
                "实验楼 A305",
                30,
                PolicyType.DIRECT,
            ),
            (
                "图书馆志愿服务",
                "志愿服务",
                (base + timedelta(days=10)).replace(hour=9, minute=0),
                "图书馆一楼",
                10,
                PolicyType.APPROVAL,
            ),
        ]
        for title, category, start_at, location, capacity, policy in rows:
            activities.create(
                conn,
                title=title,
                category=category,
                start_at=start_at,
                location=location,
                capacity=capacity,
                policy_type=policy,
                now=now,
            )

    return {"students": len(STUDENTS), "activities": len(rows), "skipped": 0}
