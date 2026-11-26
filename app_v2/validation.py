"""表单与输入校验。"""

from __future__ import annotations

from datetime import datetime
from typing import Mapping
from zoneinfo import ZoneInfo

from .domain.enums import PolicyType
from .domain.errors import ValidationError
from .domain.models import Activity


def parse_datetime_local(value: str, tz: ZoneInfo) -> datetime:
    text = (value or "").strip()
    if not text:
        raise ValueError("请填写开始时间")
    try:
        parsed = datetime.fromisoformat(text)
    except ValueError as exc:
        raise ValueError("开始时间格式不正确") from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=tz)
    else:
        parsed = parsed.astimezone(tz)
    return parsed


def format_datetime_local(value: datetime) -> str:
    return value.strftime("%Y-%m-%dT%H:%M")


def format_datetime_cn(value: datetime | None) -> str:
    if value is None:
        return ""
    return value.strftime("%Y-%m-%d %H:%M")


def validate_activity_form(
    form: Mapping[str, str],
    *,
    now: datetime,
    tz: ZoneInfo,
    existing: Activity | None = None,
) -> dict[str, object]:
    errors: dict[str, str] = {}

    title = (form.get("title") or "").strip()
    category = (form.get("category") or "").strip()
    location = (form.get("location") or "").strip()
    capacity_text = (form.get("capacity") or "").strip()
    policy_text = (form.get("policy_type") or "").strip()
    start_text = (form.get("start_at") or "").strip()

    if not title:
        errors["title"] = "请填写活动名称"
    elif len(title) > 100:
        errors["title"] = "活动名称不能超过 100 字"

    if not category:
        errors["category"] = "请填写活动类型"
    elif len(category) > 40:
        errors["category"] = "活动类型不能超过 40 字"

    if not location:
        errors["location"] = "请填写活动地点"
    elif len(location) > 100:
        errors["location"] = "活动地点不能超过 100 字"

    capacity: int | None = None
    try:
        capacity = int(capacity_text)
    except (TypeError, ValueError):
        errors["capacity"] = "人数上限必须是整数"
    else:
        if capacity <= 0:
            errors["capacity"] = "人数上限必须大于 0"
        elif capacity > 10000:
            errors["capacity"] = "人数上限不能超过 10000"

    policy: PolicyType | None = None
    try:
        policy = PolicyType(policy_text)
    except ValueError:
        errors["policy_type"] = "请选择报名方式"

    start_at: datetime | None = None
    try:
        start_at = parse_datetime_local(start_text, tz)
    except ValueError as exc:
        errors["start_at"] = str(exc)
    else:
        unchanged = existing is not None and start_at == existing.start_at
        if start_at <= now and not unchanged:
            errors["start_at"] = "开始时间必须晚于当前时间"

    if errors:
        raise ValidationError(errors)

    assert capacity is not None and policy is not None and start_at is not None
    return {
        "title": title,
        "category": category,
        "location": location,
        "capacity": capacity,
        "policy_type": policy,
        "start_at": start_at,
    }


def validate_search(query: str | None) -> str:
    text = (query or "").strip()
    if len(text) > 100:
        raise ValidationError({"q": "搜索关键字不能超过 100 字"})
    return text


def validate_login(account_id: str | None, password: str | None) -> tuple[str, str]:
    account = (account_id or "").strip()
    pwd = password or ""
    errors: dict[str, str] = {}
    if not account:
        errors["account_id"] = "请填写账号"
    if not pwd:
        errors["password"] = "请填写密码"
    if errors:
        raise ValidationError(errors)
    return account, pwd
