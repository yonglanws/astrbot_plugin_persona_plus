from __future__ import annotations

from dataclasses import dataclass

from astrbot.api import logger
from astrbot.core.config.astrbot_config import AstrBotConfig


def _normalize_str_set(values) -> set[str]:
    return {str(item).lower().strip() for item in values if str(item).strip()}


@dataclass(slots=True)
class PersonaPlusSettings:
    manage_wait_timeout: int
    admin_commands: set[str]
    auto_switch_announce: bool
    persona_groups: dict[str, list[str]]
    persona_order: list[str]


def load_settings(config: AstrBotConfig | None) -> PersonaPlusSettings:
    if not config:
        logger.warning("Persona+ 未载入专用配置，将使用默认值。")
        return PersonaPlusSettings(
            manage_wait_timeout=60,
            admin_commands={"delete"},
            auto_switch_announce=True,
            persona_groups={},
            persona_order=[],
        )

    admin_commands_raw = config.get("admin_commands", ["delete"])
    if isinstance(admin_commands_raw, list):
        admin_commands = _normalize_str_set(admin_commands_raw)
    elif isinstance(admin_commands_raw, dict):
        admin_commands = _normalize_str_set(
            c for c, v in admin_commands_raw.items() if bool(v)
        )
    else:
        logger.warning("Persona+ admin_commands 配置格式异常")
        admin_commands = {"delete"}

    raw_timeout = config.get("manage_wait_timeout_seconds", 60)
    try:
        timeout = int(raw_timeout)
    except (TypeError, ValueError):
        timeout = 60

    auto_switch_announce = bool(config.get("enable_auto_switch_announce", True))

    raw_groups = config.get("persona_groups", [])
    persona_groups: dict[str, list[str]] = {}
    if isinstance(raw_groups, list):
        for entry in raw_groups:
            entry = str(entry).strip()
            if not entry or ":" not in entry:
                continue
            group_name, _, ids_part = entry.partition(":")
            group_name = group_name.strip()
            if not group_name:
                continue
            ids = [pid.strip() for pid in ids_part.split(",") if pid.strip()]
            if ids:
                persona_groups[group_name] = ids
    elif isinstance(raw_groups, dict):
        for group_name, group_val in raw_groups.items():
            if isinstance(group_val, dict):
                personas = group_val.get("personas", [])
                if isinstance(personas, list):
                    valid = [str(p).strip() for p in personas if p and str(p).strip()]
                else:
                    continue
            elif isinstance(group_val, list):
                valid = [str(p).strip() for p in group_val if p and str(p).strip()]
            else:
                continue
            if valid:
                persona_groups[str(group_name).strip()] = valid

    raw_order = config.get("persona_order", [])
    if isinstance(raw_order, list):
        persona_order = [str(p).strip() for p in raw_order if p and str(p).strip()]
    else:
        persona_order = []

    return PersonaPlusSettings(
        manage_wait_timeout=timeout,
        admin_commands=admin_commands,
        auto_switch_announce=auto_switch_announce,
        persona_groups=persona_groups,
        persona_order=persona_order,
    )
