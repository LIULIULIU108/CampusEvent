"""会话用户、登录与角色装饰器。"""

from __future__ import annotations

from dataclasses import dataclass
from functools import wraps

from flask import abort, redirect, request, session, url_for

from ..domain.enums import Role


@dataclass(frozen=True)
class SessionUser:
    user_id: str
    name: str
    role: Role


def get_current_user() -> SessionUser | None:
    user_id = session.get("user_id")
    role_text = session.get("role")
    if not user_id or not role_text:
        return None
    try:
        role = Role(role_text)
    except ValueError:
        return None
    return SessionUser(user_id=user_id, name=session.get("name", ""), role=role)


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if get_current_user() is None:
            next_path = request.path
            if request.query_string:
                next_path += "?" + request.query_string.decode("utf-8", "ignore")
            return redirect(url_for("auth.login", next=next_path))
        return view(*args, **kwargs)

    return wrapped


def role_required(role: Role):
    def decorator(view):
        @wraps(view)
        @login_required
        def wrapped(*args, **kwargs):
            user = get_current_user()
            if user is None or user.role is not role:
                abort(403)
            return view(*args, **kwargs)

        return wrapped

    return decorator


def safe_next(default_endpoint: str) -> str:
    """只允许站内相对路径，避免开放重定向。"""
    target = request.form.get("next") or request.args.get("next")
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for(default_endpoint)
