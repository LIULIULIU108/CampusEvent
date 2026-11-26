"""CR-02：Mock 邮件发送器与邮件记录查询。"""

from __future__ import annotations

from .. import db
from ..domain.models import EmailRecord
from ..repositories import EmailOutboxRepository


class EmailDeliveryError(RuntimeError):
    """模拟邮件发送失败。"""


class MockEmailSender:
    """不连接真实 SMTP；记录由 EmailNotificationObserver 写入 email_outbox。"""

    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.sent: list[dict[str, str]] = []

    def send(self, recipient: str, subject: str, content: str) -> None:
        if self.fail:
            raise EmailDeliveryError("模拟邮件发送失败")
        self.sent.append(
            {"recipient": recipient, "subject": subject, "content": content}
        )


class EmailLogService:
    def __init__(self, outbox: EmailOutboxRepository) -> None:
        self.outbox = outbox

    def list_all(self) -> list[EmailRecord]:
        return self.outbox.list_all(db.get_db())

    def count(self) -> int:
        return self.outbox.count(db.get_db())
