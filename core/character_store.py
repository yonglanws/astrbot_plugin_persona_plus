from __future__ import annotations

import json
from pathlib import Path

from astrbot.api import logger


class CharacterStore:
    """加载 characters.json，提供别名 → 人格ID 的模糊匹配。

    按文件 mtime 检测外部变化：characters.json 在插件启动后新增、
    修改或恢复时，无需重载插件即可生效。
    """

    def __init__(self, json_path: str | Path):
        self._json_path = Path(json_path)
        self._alias_map: dict[str, str] = {}
        self._loaded_mtime: float | None = None
        self._ensure_loaded()

    def _ensure_loaded(self) -> None:
        """文件 mtime 变化时重新加载；文件暂时不可用时沿用已加载内容。"""
        try:
            mtime = self._json_path.stat().st_mtime
        except OSError:
            return
        if mtime == self._loaded_mtime:
            return
        self._alias_map = {}
        self._loaded_mtime = mtime
        self._load()

    def _load(self) -> None:
        try:
            data = json.loads(self._json_path.read_text(encoding="utf-8"))
            for entry in data:
                fullname = entry.get("fullNameChinese", "")
                if not fullname:
                    continue
                names = set()
                for field in ("name", "fullName", "fullNameChinese"):
                    val = entry.get(field, "")
                    if val and val != fullname:
                        names.add(val.strip().lower())
                for alias in entry.get("aliases", []):
                    key = alias.strip().lower()
                    if key:
                        names.add(key)
                for name in names:
                    if name not in self._alias_map:
                        self._alias_map[name] = fullname
            logger.info("Persona+ 已加载 %d 个别名/名称", len(self._alias_map))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Persona+ 加载 characters.json 失败: %s", exc)

    def resolve(self, text: str) -> str | None:
        """精确匹配别名 → 人格ID"""
        self._ensure_loaded()
        key = text.strip().lower()
        return self._alias_map.get(key)

    def alias_targets(self) -> dict[str, str]:
        """返回 别名(小写) → 人格ID 的映射副本，供近似匹配使用。"""
        self._ensure_loaded()
        return dict(self._alias_map)

    def search(self, text: str) -> list[str]:
        """搜索所有别名中含 text 的人格ID，精确匹配别名时直接返回。"""
        self._ensure_loaded()
        text_lower = text.strip().lower()
        if not text_lower:
            return []

        exact = self._alias_map.get(text_lower)
        if exact:
            return [exact]

        matched = set()
        for alias, fullname in self._alias_map.items():
            if text_lower in alias:
                matched.add(fullname)
        return list(matched)
