"""管理端路由。"""

from __future__ import annotations

from datetime import timedelta

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for

from ..domain.enums import Role, RegistrationStatus
from ..domain.errors import AppError, NotFoundError, ValidationError
from ..validation import format_datetime_local
from .decorators import role_required

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _services():
    return current_app.extensions["services"]


def _empty_form() -> dict[str, str]:
    now = _services().clock.now()
    default_start = now.replace(
        hour=14, minute=0, second=0, microsecond=0
    ) + timedelta(days=3)
    return {
        "title": "",
        "category": "",
        "start_at": format_datetime_local(default_start),
        "location": "",
        "capacity": "",
        "policy_type": "DIRECT",
    }


def _form_from_activity(activity) -> dict[str, str]:
    return {
        "title": activity.title,
        "category": activity.category,
        "start_at": format_datetime_local(activity.start_at),
        "location": activity.location,
        "capacity": str(activity.capacity),
        "policy_type": activity.policy_type.value,
    }


@bp.get("/")
@role_required(Role.ADMIN)
def dashboard():
    items = _services().activities.list()
    stats = _services().statistics.for_activities(items)
    summary = _services().statistics.dashboard()
    return render_template(
        "admin/dashboard.html", activities=items, stats=stats, summary=summary
    )


@bp.route("/activities/new", methods=["GET", "POST"])
@role_required(Role.ADMIN)
def new_activity():
    errors: dict[str, str] = {}
    form = _empty_form()
    if request.method == "POST":
        form = request.form.to_dict()
        try:
            activity = _services().activities.create(request.form)
        except ValidationError as exc:
            errors = exc.errors
        except AppError as exc:
            flash(str(exc), "error")
        else:
            flash(f"活动「{activity.title}」已创建。", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template(
        "admin/activity_form.html",
        form=form,
        errors=errors,
        mode="new",
        activity=None,
    )


@bp.route("/activities/<int:activity_id>/edit", methods=["GET", "POST"])
@role_required(Role.ADMIN)
def edit_activity(activity_id: int):
    try:
        activity = _services().activities.get(activity_id)
    except NotFoundError as exc:
        abort(404, description=str(exc))

    errors: dict[str, str] = {}
    form = _form_from_activity(activity)
    if request.method == "POST":
        form = request.form.to_dict()
        try:
            updated = _services().activities.update(activity_id, request.form)
        except ValidationError as exc:
            errors = exc.errors
        except AppError as exc:
            flash(str(exc), "error")
        else:
            flash(f"活动「{updated.title}」已更新。", "success")
            return redirect(url_for("admin.dashboard"))
    return render_template(
        "admin/activity_form.html",
        form=form,
        errors=errors,
        mode="edit",
        activity=activity,
    )


@bp.route("/activities/<int:activity_id>/delete", methods=["GET", "POST"])
@role_required(Role.ADMIN)
def delete_activity(activity_id: int):
    try:
        activity = _services().activities.get(activity_id)
    except NotFoundError as exc:
        abort(404, description=str(exc))

    if request.method == "POST":
        try:
            _services().activities.delete(activity_id)
        except AppError as exc:
            flash(str(exc), "error")
            return redirect(
                url_for("admin.activity_registrations", activity_id=activity_id)
            )
        else:
            flash(f"活动「{activity.title}」已删除。", "success")
            return redirect(url_for("admin.dashboard"))

    stats = _services().statistics.for_activity(activity)
    registration_count = _services().activities.registration_count(activity_id)
    return render_template(
        "admin/activity_delete.html",
        activity=activity,
        stats=stats,
        registration_count=registration_count,
    )


@bp.get("/activities/<int:activity_id>/registrations")
@role_required(Role.ADMIN)
def activity_registrations(activity_id: int):
    try:
        activity = _services().activities.get(activity_id)
    except NotFoundError as exc:
        abort(404, description=str(exc))

    pending = _services().approvals.list_registrations(
        activity_id, (RegistrationStatus.PENDING,)
    )
    approved = _services().approvals.list_registrations(
        activity_id, (RegistrationStatus.APPROVED,)
    )
    history = _services().approvals.list_registrations(
        activity_id, (RegistrationStatus.REJECTED, RegistrationStatus.CANCELLED)
    )
    stats = _services().statistics.for_activity(activity)
    return render_template(
        "admin/registrations.html",
        activity=activity,
        stats=stats,
        pending=pending,
        approved=approved,
        history=history,
    )


@bp.post("/registrations/<int:registration_id>/approve")
@role_required(Role.ADMIN)
def approve(registration_id: int):
    activity_id = request.form.get("activity_id", type=int)
    try:
        _services().approvals.approve(registration_id)
    except AppError as exc:
        flash(str(exc), "error")
    else:
        flash("已批准该报名，并发送站内通知。", "success")
    if activity_id:
        return redirect(
            url_for("admin.activity_registrations", activity_id=activity_id)
        )
    return redirect(url_for("admin.dashboard"))


@bp.post("/registrations/<int:registration_id>/reject")
@role_required(Role.ADMIN)
def reject(registration_id: int):
    activity_id = request.form.get("activity_id", type=int)
    try:
        _services().approvals.reject(registration_id)
    except AppError as exc:
        flash(str(exc), "error")
    else:
        flash("已拒绝该报名，并发送站内通知。", "success")
    if activity_id:
        return redirect(
            url_for("admin.activity_registrations", activity_id=activity_id)
        )
    return redirect(url_for("admin.dashboard"))
