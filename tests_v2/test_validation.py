"""输入校验测试。"""

from __future__ import annotations

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import pytest

from app_v2.domain.enums import PolicyType
from app_v2.domain.errors import ValidationError
from app_v2.validation import (
    format_datetime_cn,
    format_datetime_local,
    parse_datetime_local,
    validate_activity_form,
    validate_login,
    validate_search,
)
from tests_v2.helpers import NOW

TZ = ZoneInfo("Asia/Shanghai")


def form(**overrides):
    data = {
        "title": "测试活动",
        "category": "学术讲座",
        "start_at": (NOW + timedelta(days=3)).strftime("%Y-%m-%dT%H:%M"),
        "location": "A101",
        "capacity": "2",
        "policy_type": "DIRECT",
    }
    data.update({key: str(value) for key, value in overrides.items()})
    return data


def test_parse_datetime_local_attaches_timezone():
    parsed = parse_datetime_local("2026-11-28T14:00", TZ)
    assert parsed.tzinfo is not None
    assert parsed.hour == 14


def test_parse_datetime_local_rejects_empty():
    with pytest.raises(ValueError):
        parse_datetime_local("", TZ)


def test_format_helpers():
    value = datetime(2026, 11, 28, 14, 0, tzinfo=TZ)
    assert format_datetime_local(value) == "2026-11-28T14:00"
    assert format_datetime_cn(value) == "2026-11-28 14:00"


def test_validate_activity_form_valid():
    data = validate_activity_form(form(), now=NOW, tz=TZ)
    assert data["title"] == "测试活动"
    assert data["capacity"] == 2
    assert data["policy_type"] is PolicyType.DIRECT
    assert data["start_at"] > NOW


def test_validate_activity_form_errors():
    with pytest.raises(ValidationError) as exc:
        validate_activity_form(
            form(title="", category="", location="", capacity="0", policy_type="X"),
            now=NOW,
            tz=TZ,
        )
    errors = exc.value.errors
    assert "title" in errors
    assert "category" in errors
    assert "location" in errors
    assert "capacity" in errors
    assert "policy_type" in errors


def test_validate_activity_form_rejects_past_start():
    with pytest.raises(ValidationError) as exc:
        validate_activity_form(
            form(start_at=(NOW - timedelta(hours=1)).strftime("%Y-%m-%dT%H:%M")),
            now=NOW,
            tz=TZ,
        )
    assert "start_at" in exc.value.errors


def test_validate_activity_form_allows_unchanged_past_start():
    from app_v2.domain.models import Activity

    existing = Activity(
        activity_id=1,
        title="历史活动",
        category="测试",
        start_at=NOW - timedelta(days=1),
        location="A101",
        capacity=2,
        policy_type=PolicyType.DIRECT,
    )
    data = validate_activity_form(
        form(start_at=existing.start_at.strftime("%Y-%m-%dT%H:%M")),
        now=NOW,
        tz=TZ,
        existing=existing,
    )
    assert data["start_at"] == existing.start_at


def test_validate_search_and_login():
    assert validate_search("  讲座  ") == "讲座"
    with pytest.raises(ValidationError):
        validate_search("x" * 101)
    assert validate_login("admin", "admin123") == ("admin", "admin123")
    with pytest.raises(ValidationError) as exc:
        validate_login("", "")
    assert "account_id" in exc.value.errors
    assert "password" in exc.value.errors
