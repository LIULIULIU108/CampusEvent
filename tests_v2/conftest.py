"""pytest 公共夹具。"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app_v2 import create_app_v2  # noqa: E402
from tests_v2.helpers import (  # noqa: E402
    NOW,
    FixedClock,
    login,
    seed_students,
)


@pytest.fixture()
def clock() -> FixedClock:
    return FixedClock(NOW)


@pytest.fixture()
def app(tmp_path, clock):
    application = create_app_v2(
        {
            "DATABASE": str(tmp_path / "test.db"),
            "TESTING": True,
            "SECRET_KEY": "test-secret",
            "ADMIN_ID": "admin",
            "ADMIN_PASSWORD": "admin123",
            "ADMIN_NAME": "校园管理员",
            "PASSWORD_HASH_METHOD": "pbkdf2:sha256:1000",
        },
        clock=clock,
    )
    seed_students(application)
    yield application


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def student_client(app):
    client = app.test_client()
    response = login(client, "2024001")
    assert response.status_code == 302
    return client


@pytest.fixture()
def admin_client(app):
    client = app.test_client()
    response = login(client, "admin", "admin123")
    assert response.status_code == 302
    return client
