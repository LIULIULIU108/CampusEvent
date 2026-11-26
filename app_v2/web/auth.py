"""登录、登出与首页跳转。"""

from __future__ import annotations

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for

from ..domain.enums import Role
from ..domain.errors import ValidationError
from ..validation import validate_login
from .decorators import get_current_user, login_required, safe_next

bp = Blueprint("auth", __name__)


def _services():
    return current_app.extensions["services"]


@bp.route("/login", methods=["GET", "POST"])
def login():
    if get_current_user() is not None:
        return _home_redirect()

    errors: dict[str, str] = {}
    form = {"account_id": "", "password": ""}
    next_path = request.args.get("next") or request.form.get("next") or ""

    if request.method == "POST":
        form = {
            "account_id": request.form.get("account_id", ""),
            "password": request.form.get("password", ""),
        }
        try:
            account_id, password = validate_login(
                form["account_id"], form["password"]
            )
        except ValidationError as exc:
            errors = exc.errors
        else:
            user = _services().auth.authenticate(account_id, password)
            if user is None:
                errors["__all__"] = "账号或密码错误"
            else:
                session.clear()
                session.permanent = True
                session["user_id"] = user.user_id
                session["name"] = user.name
                session["role"] = user.role.value
                flash(f"欢迎，{user.name}！", "success")
                if next_path.startswith("/") and not next_path.startswith("//"):
                    return redirect(next_path)
                return _home_redirect(user.role)

    return render_template(
        "login.html", errors=errors, form=form, next=next_path
    )


@bp.post("/logout")
@login_required
def logout():
    session.clear()
    flash("已退出登录。", "info")
    return redirect(url_for("auth.login"))


@bp.get("/")
def index():
    user = get_current_user()
    if user is None:
        return redirect(url_for("auth.login"))
    return _home_redirect(user.role)


def _home_redirect(role: Role | None = None):
    if role is None:
        user = get_current_user()
        if user is None:
            return redirect(url_for("auth.login"))
        role = user.role
    if role is Role.ADMIN:
        return redirect(url_for("admin.dashboard"))
    return redirect(url_for("student.activities"))
