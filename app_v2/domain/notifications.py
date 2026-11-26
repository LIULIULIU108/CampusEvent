"""站内消息文案。"""

from __future__ import annotations

from .enums import EventType
from .models import DomainEvent


def build_message(event: DomainEvent) -> str:
    title = event.payload.get("title") or "该活动"
    start = event.payload.get("start_at_display") or ""
    location = event.payload.get("location") or ""
    suffix = ""
    if start:
        suffix = f"（时间：{start}"
        if location:
            suffix += f"，地点：{location}"
        suffix += "）"

    event_type = EventType(event.event_type)
    if event_type is EventType.REGISTRATION_AUTO_APPROVED:
        return f"报名成功：您报名的《{title}》已通过{suffix}。"
    if event_type is EventType.REGISTRATION_PENDING:
        return f"报名已提交：您报名的《{title}》正在等待管理员审核。"
    if event_type is EventType.REGISTRATION_ADMIN_APPROVED:
        return f"审核通过：您报名的《{title}》已通过审核{suffix}。"
    if event_type is EventType.REGISTRATION_ADMIN_REJECTED:
        return f"审核未通过：您报名的《{title}》未通过审核。"
    return f"报名状态更新：《{title}》。"
