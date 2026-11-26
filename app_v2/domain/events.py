"""领域事件、观察者与事件发布器。

通知在业务事务提交后发布。单个观察者失败只记录 notification_attempt，
不会回滚已经提交的报名/审批。
"""

from __future__ import annotations

import logging
import sqlite3
from datetime import datetime
from typing import Protocol

from .models import DomainEvent


class NotificationObserver(Protocol):
    channel: str

    def handle(self, event: DomainEvent, conn: sqlite3.Connection) -> None:
        ...


class AttemptStore(Protocol):
    def claim(
        self, conn: sqlite3.Connection, event_id: str, channel: str, now: datetime
    ) -> bool:
        ...

    def mark_sent(
        self, conn: sqlite3.Connection, event_id: str, channel: str, now: datetime
    ) -> None:
        ...

    def mark_failed(
        self,
        conn: sqlite3.Connection,
        event_id: str,
        channel: str,
        error: str,
        now: datetime,
    ) -> None:
        ...


class EventPublisher:
    def __init__(
        self,
        observers: list[NotificationObserver],
        attempts: AttemptStore,
        clock,
        logger: logging.Logger | None = None,
    ) -> None:
        self.observers = observers
        self.attempts = attempts
        self.clock = clock
        self.logger = logger or logging.getLogger(__name__)

    def publish(self, event: DomainEvent, conn: sqlite3.Connection) -> None:
        for observer in self.observers:
            supports = getattr(observer, "supports", None)
            if callable(supports) and not supports(event):
                continue
            self._publish_one(event, observer, conn)

    def _publish_one(
        self, event: DomainEvent, observer: NotificationObserver, conn: sqlite3.Connection
    ) -> None:
        now = self.clock.now()
        try:
            conn.execute("BEGIN IMMEDIATE")
            claimed = self.attempts.claim(conn, event.event_id, observer.channel, now)
            if not claimed:
                conn.rollback()
                return
            observer.handle(event, conn)
            self.attempts.mark_sent(conn, event.event_id, observer.channel, now)
            conn.commit()
        except Exception as exc:  # noqa: BLE001 - 通知失败必须被隔离
            try:
                conn.rollback()
            except sqlite3.Error:
                pass
            self.logger.exception(
                "通知失败 event_id=%s channel=%s", event.event_id, observer.channel
            )
            on_error = getattr(observer, "on_error", None)
            if callable(on_error):
                try:
                    conn.execute("BEGIN IMMEDIATE")
                    on_error(event, conn, str(exc)[:500])
                    conn.commit()
                except Exception:  # noqa: BLE001
                    try:
                        conn.rollback()
                    except sqlite3.Error:
                        pass
                    self.logger.exception(
                        "通知失败详情记录失败 event_id=%s channel=%s",
                        event.event_id,
                        observer.channel,
                    )
            try:
                conn.execute("BEGIN IMMEDIATE")
                self.attempts.mark_failed(
                    conn, event.event_id, observer.channel, str(exc)[:500], now
                )
                conn.commit()
            except Exception:  # noqa: BLE001
                try:
                    conn.rollback()
                except sqlite3.Error:
                    pass
                self.logger.exception(
                    "通知失败留痕失败 event_id=%s channel=%s",
                    event.event_id,
                    observer.channel,
                )
