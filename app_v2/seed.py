"""演示数据（初始版本 + change-v2 演示账号/活动）。"""

from __future__ import annotations

from datetime import timedelta

from flask import current_app
from werkzeug.security import generate_password_hash

from . import db
from .domain.enums import PolicyType
from .domain.models import Student
from .repositories import ActivityRepository, StudentRepository

# 学号、姓名、密码、年级（CR-01 起 Student 增加 grade）
STUDENTS = [
    ("2024001", "张三", "123456", 2),
    ("2024002", "李四", "123456", 3),
    ("2024003", "王五", "123456", 1),
    ("2024004", "赵六", "123456", 4),
]


def _seed_students(conn, students: StudentRepository, now) -> int:
    created = 0
    for student_id, name, password, grade in STUDENTS:
        if students.get(conn, student_id) is not None:
            continue
        students.create(
            conn,
            Student(
                student_id=student_id,
                name=name,
                password_hash=generate_password_hash(password),
                created_at=now,
                grade=grade,
            ),
        )
        created += 1
    return created


def seed_students_only() -> dict[str, int]:
    conn = db.get_db()
    students = StudentRepository()
    now = current_app.extensions["clock"].now()
    with db.transaction():
        created = _seed_students(conn, students, now)
    return {"students": created, "skipped": 0 if created else 1}


def set_demo_grades() -> dict[str, int]:
    """把演示学生年级同步为 2/3/1/4；已有库迁移后使用。"""
    conn = db.get_db()
    students = StudentRepository()
    now = current_app.extensions["clock"].now()
    updated = 0
    inserted = 0
    with db.transaction():
        for student_id, name, password, grade in STUDENTS:
            existing = students.get(conn, student_id)
            if existing is None:
                students.create(
                    conn,
                    Student(
                        student_id=student_id,
                        name=name,
                        password_hash=generate_password_hash(password),
                        created_at=now,
                        grade=grade,
                    ),
                )
                inserted += 1
            else:
                students.update_grade(conn, student_id, grade)
                updated += 1
    return {"updated": updated, "inserted": inserted}


def seed_cr_demo_activity() -> dict[str, int]:
    """为已有库补一个年级限定演示活动（幂等）。"""
    from datetime import timedelta

    conn = db.get_db()
    activities = ActivityRepository()
    title = "大二大三专属科研讲座"
    existing = [a for a in activities.list_all(conn) if a.title == title]
    if existing:
        return {"created": 0, "skipped": 1}
    now = current_app.extensions["clock"].now()
    start_at = (now + timedelta(days=12)).replace(
        hour=14, minute=0, second=0, microsecond=0
    )
    with db.transaction():
        activities.create(
            conn,
            title=title,
            category="学术讲座",
            start_at=start_at,
            location="学术交流中心",
            capacity=20,
            policy_type=PolicyType.GRADE_DIRECT,
            now=now,
        )
    return {"created": 1, "skipped": 0}


def seed_demo() -> dict[str, int]:
    conn = db.get_db()
    students = StudentRepository()
    activities = ActivityRepository()

    if students.count(conn) > 0 or activities.count_all(conn) > 0:
        return {"students": 0, "activities": 0, "skipped": 1}

    now = current_app.extensions["clock"].now()

    with db.transaction():
        _seed_students(conn, students, now)

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
            (
                "大二大三专属科研讲座",
                "学术讲座",
                (base + timedelta(days=12)).replace(hour=14, minute=0),
                "学术交流中心",
                20,
                PolicyType.GRADE_DIRECT,
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
