"""站内通知观察者。"""

from __future__ import annotations

import sqlite3

from ..domain.events import NotificationObserver
from ..domain.models import DomainEvent
from ..domain.notifications import build_message
from ..repositories import MessageRepository


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
