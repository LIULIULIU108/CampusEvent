"""应用配置。"""

from __future__ import annotations

import os
from datetime import timedelta


class Config:
    """默认配置；敏感值通过环境变量覆盖。"""

    SECRET_KEY = os.environ.get("CAMPUSEVENT_SECRET_KEY", "dev-only-change-me")
    DATABASE = os.environ.get("CAMPUSEVENT_DATABASE") or None
    ADMIN_ID = os.environ.get("CAMPUSEVENT_ADMIN_ID", "admin")
    ADMIN_PASSWORD = os.environ.get("CAMPUSEVENT_ADMIN_PASSWORD", "admin123")
    ADMIN_NAME = os.environ.get("CAMPUSEVENT_ADMIN_NAME", "校园管理员")
    TIMEZONE = os.environ.get("CAMPUSEVENT_TIMEZONE", "Asia/Shanghai")

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    PERMANENT_SESSION_LIFETIME = timedelta(hours=8)
    MAX_CONTENT_LENGTH = 1 * 1024 * 1024


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "test-secret"
    DATABASE = None
