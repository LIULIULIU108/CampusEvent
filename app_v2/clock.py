"""可注入的时钟，保证业务时间判断可测试。"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo


class Clock:
    def now(self) -> datetime:  # pragma: no cover - 接口
        raise NotImplementedError


class SystemClock(Clock):
    def __init__(self, tz: ZoneInfo) -> None:
        self.tz = tz

    def now(self) -> datetime:
        return datetime.now(self.tz)
