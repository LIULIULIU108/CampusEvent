"""测试辅助函数。"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from werkzeug.security import generate_password_hash

from app_v2 import db
from app_v2.domain.enums import PolicyType
from app_v2.domain.models import Student
from app_v2.repositories import ActivityRepository, StudentRepository

TZ = ZoneInfo("Asia/Shanghai")
NOW = datetime(2026, 11, 25, 10, 0, tzinfo=TZ)
STUDENT_PASSWORD_HASH = generate_password_hash(
    "123456", method="pbkdf2:sha256:1000"
)


class FixedClock:
    def __init__(self, current: datetime) -> None:
        self.current = current

    def now(self) -> datetime:
        return self.current

    def set(self, value: datetime) -> None:
        self.current = value

    def advance(self, **kwargs) -> None:
        self.current = self.current + timedelta(**kwargs)


def seed_students(app) -> None:
    with app.app_context():
        conn = db.get_db()
        students = StudentRepository()
        with db.transaction():
            for student_id, name, grade in (
                ("2024001", "张三", 2),
                ("2024002", "李四", 3),
                ("2024003", "王五", 1),
                ("2024004", "赵六", 4),
            ):
                students.create(
                    conn,
                    Student(
                        student_id=student_id,
                        name=name,
                        password_hash=STUDENT_PASSWORD_HASH,
                        created_at=NOW,
                        grade=grade,
                    ),
                )


def make_activity(
    app,
    *,
    title: str = "测试活动",
    category: str = "测试",
    location: str = "A101",
    capacity: int = 2,
    policy: PolicyType = PolicyType.DIRECT,
    start_at: datetime | None = None,
):
    start_at = start_at or (NOW + timedelta(days=3))
    if isinstance(policy, str):
        policy = PolicyType(policy)
    with app.app_context():
        conn = db.get_db()
        with db.transaction():
            return ActivityRepository().create(
                conn,
                title=title,
                category=category,
                start_at=start_at,
                location=location,
                capacity=capacity,
                policy_type=policy,
                now=NOW,
            )


def login(client, account: str, password: str = "123456", follow_redirects: bool = False):
    return client.post(
        "/login",
        data={"account_id": account, "password": password},
        follow_redirects=follow_redirects,
    )


def active_registration(app, activity_id: int, student_id: str = "2024001"):
    with app.app_context():
        conn = db.get_db()
        return conn.execute(
            "SELECT * FROM registration WHERE activity_id=? AND student_id=? "
            "AND status IN ('PENDING','APPROVED')",
            (activity_id, student_id),
        ).fetchone()


def count_rows(app, table: str, where: str = "1=1", params: tuple = ()) -> int:
    with app.app_context():
        conn = db.get_db()
        return conn.execute(
            f"SELECT COUNT(*) FROM {table} WHERE {where}", params
        ).fetchone()[0]


def fetch_one(app, sql: str, params: tuple = ()):
    with app.app_context():
        conn = db.get_db()
        return conn.execute(sql, params).fetchone()
