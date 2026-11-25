"""CampusEvent Flask 应用工厂。"""

from __future__ import annotations

import os
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from flask import Flask, render_template
from werkzeug.security import generate_password_hash

from . import db
from .clock import SystemClock
from .config import Config
from .domain.capacity import CapacityChecker
from .domain.enums import (
    POLICY_LABELS,
    STATUS_CLASSES,
    STATUS_LABELS,
    PolicyType,
    Role,
)
from .domain.events import EventPublisher
from .domain.policies import (
    ApprovalRegistrationPolicy,
    DirectRegistrationPolicy,
    PolicyRegistry,
)
from .repositories import (
    ActivityRepository,
    MessageRepository,
    NotificationAttemptRepository,
    RegistrationRepository,
    StudentRepository,
)
from .services.activities import ActivityService
from .services.approvals import ApprovalService
from .services.auth import AuthService
from .services.messages import MessageService
from .services.notifications import InAppNotificationObserver
from .services.registrations import RegistrationService
from .services.statistics import StatisticsService
from .validation import format_datetime_cn
from .web.admin import bp as admin_bp
from .web.auth import bp as auth_bp
from .web.decorators import get_current_user
from .web.student import bp as student_bp


def create_app(test_config: dict | None = None, clock=None) -> Flask:
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(Config)
    if test_config:
        app.config.update(test_config)

    if not app.config.get("DATABASE"):
        os.makedirs(app.instance_path, exist_ok=True)
        app.config["DATABASE"] = os.path.join(app.instance_path, "campus_event.db")
    else:
        database_dir = os.path.dirname(os.path.abspath(app.config["DATABASE"]))
        os.makedirs(database_dir, exist_ok=True)

    app.config["ADMIN_PASSWORD_HASH"] = generate_password_hash(
        app.config["ADMIN_PASSWORD"],
        method=app.config.get("PASSWORD_HASH_METHOD", "scrypt"),
    )

    tz = ZoneInfo(app.config["TIMEZONE"])
    clock = clock or SystemClock(tz)

    db.init_app(app)

    students = StudentRepository()
    activities = ActivityRepository()
    registrations = RegistrationRepository()
    messages = MessageRepository()
    attempts = NotificationAttemptRepository()

    capacity = CapacityChecker()
    registry = PolicyRegistry(
        [
            DirectRegistrationPolicy(capacity),
            ApprovalRegistrationPolicy(),
        ]
    )
    publisher = EventPublisher(
        [InAppNotificationObserver(messages)], attempts, clock
    )

    services = SimpleNamespace(
        clock=clock,
        auth=AuthService(
            students,
            admin_id=app.config["ADMIN_ID"],
            admin_name=app.config["ADMIN_NAME"],
            admin_password_hash=app.config["ADMIN_PASSWORD_HASH"],
        ),
        activities=ActivityService(activities, registrations, clock, tz),
        registrations=RegistrationService(
            activities, students, registrations, registry, publisher, clock
        ),
        approvals=ApprovalService(
            activities, registrations, capacity, publisher, clock
        ),
        messages=MessageService(messages),
        statistics=StatisticsService(activities, registrations),
    )
    app.extensions["services"] = services
    app.extensions["clock"] = clock

    app.register_blueprint(auth_bp)
    app.register_blueprint(student_bp)
    app.register_blueprint(admin_bp)

    @app.get("/healthz")
    def healthz():
        return {"status": "ok"}

    @app.errorhandler(404)
    def not_found(error):
        return render_template("errors/404.html", error=error), 404

    @app.errorhandler(403)
    def forbidden(error):
        return render_template("errors/403.html", error=error), 403

    @app.errorhandler(500)
    def server_error(error):
        return render_template("errors/500.html", error=error), 500

    @app.context_processor
    def inject_globals():
        user = get_current_user()
        unread = 0
        if user is not None and user.role is Role.STUDENT:
            try:
                unread = services.messages.unread_count(user.user_id)
            except Exception:  # noqa: BLE001 - 上下文注入不应阻断页面
                unread = 0
        return {
            "current_user": user,
            "unread_count": unread,
            "now": clock.now(),
            "POLICY_LABELS": POLICY_LABELS,
            "STATUS_LABELS": STATUS_LABELS,
            "STATUS_CLASSES": STATUS_CLASSES,
        }

    @app.template_filter("dt")
    def datetime_filter(value):
        return format_datetime_cn(value)

    @app.template_filter("status_class")
    def status_class(value):
        return STATUS_CLASSES.get(value, "")

    @app.template_filter("status_label")
    def status_label(value):
        return STATUS_LABELS.get(value, str(value))

    @app.template_filter("policy_label")
    def policy_label(value):
        return POLICY_LABELS.get(value, str(value))

    with app.app_context():
        db.init_db()

    return app
