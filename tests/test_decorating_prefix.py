"""Tests for Persona+ on_decorating_result priority & non-Plain segment skipping."""

from __future__ import annotations

import asyncio
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch


PLUGIN_ROOT = Path(__file__).resolve().parents[1]


def _load_persona_plus_main(hook_recorder: dict):
    class _Plain:
        def __init__(self, text: str = ""):
            self.text = text

    class _Image:
        def __init__(self, file: str = ""):
            self.file = file

    class _Filter:
        class EventMessageType:
            ALL = "ALL"

        class PermissionType:
            ADMIN = "ADMIN"

        @staticmethod
        def _record(hook_name, kw):
            def deco(fn):
                hook_recorder[fn.__name__] = (hook_name, kw.get("priority", 0))
                return fn

            return deco

        @classmethod
        def on_astrbot_loaded(cls, **kw):
            return cls._record("on_astrbot_loaded", kw)

        @classmethod
        def on_waiting_llm_request(cls, **kw):
            return cls._record("on_waiting_llm_request", kw)

        @classmethod
        def on_llm_request(cls, **kw):
            return cls._record("on_llm_request", kw)

        @classmethod
        def event_message_type(cls, *args, **kw):
            return cls._record("event_message_type", kw)

        @classmethod
        def command(cls, *args, **kw):
            return cls._record("command", kw)

        @classmethod
        def permission_type(cls, *args, **kw):
            return lambda fn: fn

        @classmethod
        def on_decorating_result(cls, **kw):
            return cls._record("on_decorating_result", kw)

    class _Star:
        def __init__(self, context=None):
            self.context = context

    def _pkg(name):
        m = types.ModuleType(name)
        return m

    astrbot = _pkg("astrbot")
    api = _pkg("astrbot.api")
    api_event = _pkg("astrbot.api.event")
    api_star = _pkg("astrbot.api.star")
    api_comp = _pkg("astrbot.api.message_components")
    api_provider = _pkg("astrbot.api.provider")
    core = _pkg("astrbot.core")
    core_msg = _pkg("astrbot.core.message")
    core_msg_comp = _pkg("astrbot.core.message.components")
    core_msg_res = _pkg("astrbot.core.message.message_event_result")
    core_prov = _pkg("astrbot.core.provider")
    core_prov_ent = _pkg("astrbot.core.provider.entities")
    core_star = _pkg("astrbot.core.star")
    core_star_tools = _pkg("astrbot.core.star.star_tools")
    core_utils = _pkg("astrbot.core.utils")
    core_cfg = _pkg("astrbot.core.config")
    core_cfg_ab = _pkg("astrbot.core.config.astrbot_config")
    core_act = _pkg("astrbot.core.utils.active_event_registry")
    core_sw = _pkg("astrbot.core.utils.session_waiter")
    core_so = _pkg("astrbot.core.session_overrides")

    api.logger = SimpleNamespace(
        info=lambda *a, **k: None,
        warning=lambda *a, **k: None,
        error=lambda *a, **k: None,
        debug=lambda *a, **k: None,
        exception=lambda *a, **k: None,
    )
    api.AstrBotConfig = dict
    api_event.filter = _Filter()
    api_event.AstrMessageEvent = object
    api_event.MessageEventResult = object
    api_star.Context = object
    api_star.Star = _Star
    api_star.StarTools = SimpleNamespace(get_data_dir=lambda *a, **k: PLUGIN_ROOT)
    api_star.register = lambda *a, **kw: (lambda cls: cls)
    api_comp.Plain = _Plain
    api_comp.Image = _Image
    core_msg_comp.Plain = _Plain
    core_msg_comp.Image = _Image
    core_msg_res.ResultContentType = SimpleNamespace(LLM_RESULT="LLM_RESULT")
    api_provider.ProviderRequest = object
    core_prov_ent.ProviderRequest = object
    core_star_tools.StarTools = SimpleNamespace(get_data_dir=lambda *a, **k: PLUGIN_ROOT)
    core_cfg_ab.AstrBotConfig = dict
    core_act.active_event_registry = SimpleNamespace(stop_all=lambda *a, **k: None)
    core_sw.SessionController = object
    core_sw.SessionFilter = object
    core_sw.session_waiter = lambda *a, **k: (lambda fn: fn)
    core_so.update_overrides = lambda *a, **k: None

    pp_pkg = types.ModuleType("astrbot_plugin_persona_plus")
    pp_pkg.__path__ = [str(PLUGIN_ROOT)]

    mods = {
        "astrbot": astrbot,
        "astrbot.api": api,
        "astrbot.api.event": api_event,
        "astrbot.api.star": api_star,
        "astrbot.api.message_components": api_comp,
        "astrbot.api.provider": api_provider,
        "astrbot.core": core,
        "astrbot.core.config": core_cfg,
        "astrbot.core.config.astrbot_config": core_cfg_ab,
        "astrbot.core.message": core_msg,
        "astrbot.core.message.components": core_msg_comp,
        "astrbot.core.message.message_event_result": core_msg_res,
        "astrbot.core.provider": core_prov,
        "astrbot.core.provider.entities": core_prov_ent,
        "astrbot.core.star": core_star,
        "astrbot.core.star.star_tools": core_star_tools,
        "astrbot.core.utils": core_utils,
        "astrbot.core.utils.active_event_registry": core_act,
        "astrbot.core.utils.session_waiter": core_sw,
        "astrbot.core.session_overrides": core_so,
        "astrbot_plugin_persona_plus": pp_pkg,
    }

    with patch.dict(sys.modules, mods):
        spec = importlib.util.spec_from_file_location(
            "astrbot_plugin_persona_plus.main",
            PLUGIN_ROOT / "main.py",
        )
        mod = importlib.util.module_from_spec(spec)
        sys.modules["astrbot_plugin_persona_plus.main"] = mod
        spec.loader.exec_module(mod)
        return mod, _Plain, _Image


def _make_event(chain, extras=None):
    store = dict(extras or {})
    res = SimpleNamespace(
        chain=list(chain),
        is_llm_result=lambda: True,
        result_content_type=SimpleNamespace(name="LLM_RESULT"),
    )
    return SimpleNamespace(
        unified_msg_origin="aiocqhttp:GroupMessage:100",
        get_extra=lambda k, d=None: store.get(k, d),
        set_extra=lambda k, v: store.__setitem__(k, v),
        get_result=lambda: res,
    )


def test_decorating_priority_and_skips_leading_image_and_blank_plain():
    hooks = {}
    mod, Plain, Image = _load_persona_plus_main(hooks)
    assert hooks["on_decorating_result"] == ("on_decorating_result", 80)

    plugin = mod.PersonaPlus.__new__(mod.PersonaPlus)
    ev = _make_event(
        [Image("happy.png"), Plain("   "), Plain("哈喽呀")],
        extras={"_persona_plus_llm": True, "_persona_plus_request_pid": "宵崎奏"},
    )
    asyncio.run(plugin.on_decorating_result(ev))

    chain = ev.get_result().chain
    assert isinstance(chain[0], Image)
    assert chain[1].text == "   "
    assert chain[2].text == "[宵崎奏]哈喽呀"
    assert ev.get_extra("_persona_plus_prefixed") is True


def test_image_only_chain_does_not_create_empty_persona_shell():
    hooks = {}
    mod, Plain, Image = _load_persona_plus_main(hooks)
    plugin = mod.PersonaPlus.__new__(mod.PersonaPlus)

    ev = _make_event(
        [Image("sticker.png")],
        extras={"_persona_plus_llm": True, "_persona_plus_request_pid": "宵崎奏"},
    )
    asyncio.run(plugin.on_decorating_result(ev))

    chain = ev.get_result().chain
    assert len(chain) == 1
    assert isinstance(chain[0], Image)
    assert not ev.get_extra("_persona_plus_prefixed", False)
