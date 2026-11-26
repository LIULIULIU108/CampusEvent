"""学生端路由。"""

from __future__ import annotations

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from ..domain.enums import Role
from ..domain.errors import AppError, NotFoundError
from .decorators import get_current_user, role_required, safe_next

bp = Blueprint("student", __name__)


def _services():
    return current_app.extensions["services"]


@bp.get("/activities")
@role_required(Role.STUDENT)
def activities():
    user = get_current_user()
    q = request.args.get("q", "")
    try:
        items = _services().activities.list(q)
    except AppError as exc:
        flash(str(exc), "error")
        items = []
    stats = _services().statistics.for_activities(items)
    active = _services().registrations.active_by_student(user.user_id)
    return render_template(
        "student/activities.html",
        activities=items,
        stats=stats,
        active=active,
        q=q,
    )


@bp.get("/activities/<int:activity_id>")
@role_required(Role.STUDENT)
def activity_detail(activity_id: int):
    user = get_current_user()
    try:
        activity = _services().activities.get(activity_id)
    except NotFoundError as exc:
        abort(404, description=str(exc))
    stats = _services().statistics.for_activity(activity)
    my_registration = _services().registrations.get_active(user.user_id, activity_id)
    return render_template(
        "student/activity_detail.html",
        activity=activity,
        stats=stats,
        my_registration=my_registration,
    )


@bp.post("/activities/<int:activity_id>/registrations")
@role_required(Role.STUDENT)
def register(activity_id: int):
    user = get_current_user()
    try:
        registration = _services().registrations.register(user.user_id, activity_id)
    except AppError as exc:
        flash(str(exc), "error")
    else:
        if registration.status.value == "APPROVED":
            flash("报名成功，已通过。", "success")
        else:
            flash("报名已提交，等待管理员审核。", "success")
    return redirect(url_for("student.activity_detail", activity_id=activity_id))


@bp.post("/registrations/<int:registration_id>/cancel")
@role_required(Role.STUDENT)
def cancel(registration_id: int):
    user = get_current_user()
    try:
        _services().registrations.cancel(user.user_id, registration_id)
    except AppError as exc:
        flash(str(exc), "error")
    else:
        flash("已取消报名。", "success")
    return redirect(safe_next("student.registrations"))


@bp.get("/me/registrations")
@role_required(Role.STUDENT)
def registrations():
    user = get_current_user()
    items = _services().registrations.list_for_student_with_activity(user.user_id)
    return render_template("student/registrations.html", items=items)


@bp.get("/me/messages")
@role_required(Role.STUDENT)
def messages():
    user = get_current_user()
    items = _services().messages.list_for_student(user.user_id)
    return render_template("student/messages.html", messages=items)


@bp.post("/me/messages/<int:message_id>/read")
@role_required(Role.STUDENT)
def read_message(message_id: int):
    user = get_current_user()
    ok = _services().messages.mark_read(user.user_id, message_id)
    if not ok:
        flash("消息不存在或无权操作。", "error")
    return redirect(url_for("student.messages"))


@bp.post("/me/messages/read-all")
@role_required(Role.STUDENT)
def read_all_messages():
    user = get_current_user()
    count = _services().messages.mark_all_read(user.user_id)
    flash(f"已将 {count} 条消息标为已读。", "info")
    return redirect(url_for("student.messages"))
