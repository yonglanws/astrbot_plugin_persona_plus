from __future__ import annotations

from astrbot.api.event import AstrMessageEvent
from astrbot.core.utils.session_waiter import SessionFilter


class GroupScopedSessionFilter(SessionFilter):
    """按消息来源（群/频道/私信）隔离等待中的会话，同一会话下所有人可触发。"""

    def filter(self, event: AstrMessageEvent) -> str:
        return event.unified_msg_origin
