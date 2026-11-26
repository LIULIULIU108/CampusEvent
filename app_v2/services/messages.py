"""站内消息查询与已读。"""

from __future__ import annotations

from .. import db
from ..domain.models import Message
from ..repositories import MessageRepository


class MessageService:
    def __init__(self, messages: MessageRepository) -> None:
        self.messages = messages

    def list_for_student(self, student_id: str) -> list[Message]:
        return self.messages.list_for_student(db.get_db(), student_id)

    def unread_count(self, student_id: str) -> int:
        return self.messages.unread_count(db.get_db(), student_id)

    def mark_read(self, student_id: str, message_id: int) -> bool:
        return self.messages.mark_read(db.get_db(), message_id, student_id)

    def mark_all_read(self, student_id: str) -> int:
        return self.messages.mark_all_read(db.get_db(), student_id)
