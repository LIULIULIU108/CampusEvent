"""登录与当前用户。"""

from __future__ import annotations

import hmac
from dataclasses import dataclass

from werkzeug.security import check_password_hash

from .. import db
from ..domain.enums import Role
from ..repositories import StudentRepository


@dataclass(frozen=True)
class CurrentUser:
    user_id: str
    name: str
    role: Role


class AuthService:
    def __init__(
        self,
        students: StudentRepository,
        *,
        admin_id: str,
        admin_name: str,
        admin_password_hash: str,
    ) -> None:
        self.students = students
        self.admin_id = admin_id
        self.admin_name = admin_name
        self.admin_password_hash = admin_password_hash

    def authenticate(self, account_id: str, password: str) -> CurrentUser | None:
        conn = db.get_db()
        student = self.students.get(conn, account_id)
        if student is not None and check_password_hash(student.password_hash, password):
            return CurrentUser(student.student_id, student.name, Role.STUDENT)

        if hmac.compare_digest(account_id, self.admin_id) and check_password_hash(
            self.admin_password_hash, password
        ):
            return CurrentUser(self.admin_id, self.admin_name, Role.ADMIN)
        return None
