"""站内消息与 Mock 邮件观察者。"""

from __future__ import annotations

import sqlite3

from ..domain.enums import EventType
from ..domain.events import NotificationObserver
from ..domain.models import DomainEvent
from ..domain.notifications import build_message
from ..repositories import EmailOutboxRepository, MessageRepository
from .email import MockEmailSender


class InAppNotificationObserver(NotificationObserver):
    channel = "in_app"

    def __init__(self, messages: MessageRepository) -> None:
        self.messages = messages

    def handle(self, event: DomainEvent, conn: sqlite3.Connection) -> None:
        self.messages.create(
            conn,
            student_id=event.student_id,
            activity_id=event.activity_id,
            content=build_message(event),
            now=event.occurred_at,
        )


class EmailNotificationObserver(NotificationObserver):
    """CR-02：为报名通过、审核通过/拒绝事件增加 Mock 邮件通知。"""

    channel = "email"
    event_types = frozenset(
        {
            EventType.REGISTRATION_AUTO_APPROVED,
            EventType.REGISTRATION_ADMIN_APPROVED,
            EventType.REGISTRATION_ADMIN_REJECTED,
        }
    )
    subject_labels = {
        EventType.REGISTRATION_AUTO_APPROVED: "报名成功",
        EventType.REGISTRATION_ADMIN_APPROVED: "审核通过",
        EventType.REGISTRATION_ADMIN_REJECTED: "审核未通过",
    }

    def __init__(
        self, outbox: EmailOutboxRepository, sender: MockEmailSender
    ) -> None:
        self.outbox = outbox
        self.sender = sender

    def supports(self, event: DomainEvent) -> bool:
        return EventType(event.event_type) in self.event_types

    def _fields(self, event: DomainEvent) -> dict[str, str]:
        title = event.payload.get("title") or "该活动"
        label = self.subject_labels[EventType(event.event_type)]
        return {
            "recipient": f"{event.student_id}@mock.campus.local",
            "subject": f"[CampusEvent] {label}：{title}",
            "content": build_message(event) + "\n\n（本邮件由 MockEmailSender 模拟发送）",
        }

    def handle(self, event: DomainEvent, conn: sqlite3.Connection) -> None:
        fields = self._fields(event)
        created = self.outbox.create_pending(
            conn,
            event_id=event.event_id,
            student_id=event.student_id,
            activity_id=event.activity_id,
            recipient=fields["recipient"],
            subject=fields["subject"],
            content=fields["content"],
            now=event.occurred_at,
        )
        if created is None:
            return
        self.sender.send(
            fields["recipient"], fields["subject"], fields["content"]
        )
        self.outbox.mark_sent(conn, event.event_id, event.occurred_at)

    def on_error(
        self, event: DomainEvent, conn: sqlite3.Connection, error: str
    ) -> None:
        fields = self._fields(event)
        self.outbox.record_failure(
            conn,
            event_id=event.event_id,
            student_id=event.student_id,
            activity_id=event.activity_id,
            recipient=fields["recipient"],
            subject=fields["subject"],
            content=fields["content"],
            error=error,
            now=event.occurred_at,
        )
