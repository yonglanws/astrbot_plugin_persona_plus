"""Tests for Persona+ switch cleanup extras and lazy reset history isolation."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _install_astrbot_stubs(monkeypatch_dict: dict | None = None) -> None:
    if str(PLUGIN_ROOT.parent) not in sys.path:
        sys.path.insert(0, str(PLUGIN_ROOT.parent))

    pkg = sys.modules.get("astrbot_plugin_persona_plus")
    if pkg is None:
        pkg = types.ModuleType("astrbot_plugin_persona_plus")
        pkg.__path__ = [str(PLUGIN_ROOT)]
        pkg.__file__ = str(PLUGIN_ROOT / "__init__.py")
        sys.modules["astrbot_plugin_persona_plus"] = pkg

    def _ensure_mod(name: str):
        mod = sys.modules.get(name)
        if mod is None:
            mod = types.ModuleType(name)
            sys.modules[name] = mod
        return mod

    astrbot = _ensure_mod("astrbot")
    api = _ensure_mod("astrbot.api")
    api_event = _ensure_mod("astrbot.api.event")
    api_star = _ensure_mod("astrbot.api.star")
    core = _ensure_mod("astrbot.core")
    core_utils = _ensure_mod("astrbot.core.utils")
    registry_mod = _ensure_mod("astrbot.core.utils.active_event_registry")
    overrides_mod = _ensure_mod("astrbot.core.session_overrides")

    api.logger = types.SimpleNamespace(
        info=lambda *a, **kw: None,
        warning=lambda *a, **kw: None,
        error=lambda *a, **kw: None,
        debug=lambda *a, **kw: None,
        exception=lambda *a, **kw: None,
    )
    api_event.AstrMessageEvent = object
    api_event.MessageEventResult = object
    api_star.Context = object

    class _Registry:
        def __init__(self):
            self.stopped = []

        def stop_all(self, umo, exclude=None):
            self.stopped.append((umo, exclude))

    registry_mod.active_event_registry = _Registry()

    async def _update_overrides(umo, data):
        overrides_mod.calls.append((umo, dict(data)))

    overrides_mod.calls = []
    overrides_mod.update_overrides = _update_overrides
    astrbot.api = api
    core.session_overrides = overrides_mod
    core_utils.active_event_registry = registry_mod


class _DummyEvent:
    def __init__(self, umo: str) -> None:
        self.unified_msg_origin = umo
        self.extras: dict[str, object] = {}

    def set_extra(self, key: str, value) -> None:
        self.extras[key] = value

    def get_extra(self, key: str, default=None):
        return self.extras.get(key, default)

    def plain_result(self, text: str):
        return SimpleNamespace(text=text)


def test_switch_persona_marks_cleanup_extras_and_discards_pending(tmp_path: Path) -> None:
    _install_astrbot_stubs()
    from astrbot_plugin_persona_plus.core.switching import switch_persona
    from astrbot_plugin_persona_plus.core.user_persona_store import (
        GroupPersonaStore,
        PendingHistoryResetStore,
    )

    umo = "aiocqhttp:FriendMessage:1001"
    user_store = GroupPersonaStore(tmp_path / "group_personas.json")
    pending_store = PendingHistoryResetStore(tmp_path / "pending.json")
    pending_store.add_many([umo])

    conv_mgr = SimpleNamespace(
        get_curr_conversation_id=AsyncMock(return_value="cid-1"),
        update_conversation=AsyncMock(),
        new_conversation=AsyncMock(),
    )
    context = SimpleNamespace(conversation_manager=conv_mgr)
    persona_mgr = SimpleNamespace(get_persona=AsyncMock(return_value={"name": "东云彰人"}))
    ev = _DummyEvent(umo)

    res = asyncio.run(
        switch_persona(
            context=context,
            persona_mgr=persona_mgr,
            user_store=user_store,
            event=ev,
            persona_id="东云彰人",
            announce="已切换",
            pending_reset_store=pending_store,
        )
    )

    assert res.text == "已切换"
    assert ev.get_extra("_clean_ltm_session") is True
    assert ev.get_extra("_clean_group_context_session") is True
    assert not pending_store.contains(umo)
    conv_mgr.update_conversation.assert_awaited_once_with(
        unified_msg_origin=umo,
        conversation_id="cid-1",
        persona_id="东云彰人",
        history=[],
    )


def test_reset_all_personas_clears_origin_and_queues_other_changed_umos_without_oom(
    tmp_path: Path,
) -> None:
    _install_astrbot_stubs()
    import astrbot.core.session_overrides as so_mod
    from astrbot_plugin_persona_plus.core.switching import (
        DEFAULT_PERSONA_ID,
        clear_session_conversation_history,
        mark_session_cleanup_extras,
        reset_all_personas,
    )
    from astrbot_plugin_persona_plus.core.user_persona_store import (
        GroupPersonaStore,
        PendingHistoryResetStore,
    )

    so_mod.calls.clear()
    umo_admin = "aiocqhttp:FriendMessage:admin"
    umo_other = "aiocqhttp:GroupMessage:888"
    umo_already_default = "aiocqhttp:FriendMessage:already"

    user_store = GroupPersonaStore(tmp_path / "group_personas.json")
    user_store.set(umo_admin, "东云彰人")
    user_store.set(umo_other, "宵崎奏")
    user_store.set(umo_already_default, DEFAULT_PERSONA_ID)
    pending_store = PendingHistoryResetStore(tmp_path / "pending.json")

    get_conversations = Mock(side_effect=AssertionError("must never call get_conversations"))
    conv_mgr = SimpleNamespace(
        get_conversations=get_conversations,
        get_curr_conversation_id=AsyncMock(return_value="cid-target"),
        update_conversation=AsyncMock(),
    )
    context = SimpleNamespace(
        conversation_manager=conv_mgr,
        get_config=lambda umo=None: {
            "agent": {"runtime": "astrbot", "config": {"persona": {"persona_id": "东云彰人"}}}
        },
    )
    admin_ev = _DummyEvent(umo_admin)

    count = asyncio.run(
        reset_all_personas(
            context=context,
            persona_mgr=SimpleNamespace(),
            user_store=user_store,
            exclude_event=admin_ev,
            pending_reset_store=pending_store,
        )
    )

    assert count == 3
    get_conversations.assert_not_called()
    # 发起会话立即清历史并置清理 extra
    assert admin_ev.get_extra("_clean_ltm_session") is True
    assert admin_ev.get_extra("_clean_group_context_session") is True
    conv_mgr.update_conversation.assert_awaited_once_with(
        unified_msg_origin=umo_admin,
        conversation_id="cid-target",
        persona_id=DEFAULT_PERSONA_ID,
        history=[],
    )
    # 其它曾切换过人格的会话进入持久化待清理队列；已在默认人格的会话不误加入
    assert pending_store.contains(umo_other)
    assert not pending_store.contains(umo_admin)
    assert not pending_store.contains(umo_already_default)

    # 重启后重新加载 pending_store，模拟另一会话下次发消息前懒清理
    reloaded_pending = PendingHistoryResetStore(tmp_path / "pending.json")
    assert reloaded_pending.contains(umo_other)
    next_ev = _DummyEvent(umo_other)
    ok = asyncio.run(
        clear_session_conversation_history(context, umo_other, DEFAULT_PERSONA_ID)
    )
    assert ok is True
    reloaded_pending.discard(umo_other)
    mark_session_cleanup_extras(next_ev)
    assert not reloaded_pending.contains(umo_other)
    assert next_ev.get_extra("_clean_ltm_session") is True
    assert next_ev.get_extra("_clean_group_context_session") is True
