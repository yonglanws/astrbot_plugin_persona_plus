from __future__ import annotations

import json
from pathlib import Path

from astrbot.api import logger


class CharacterStore:
    """加载 characters.json，提供别名 → 人格ID 的精确与模糊匹配。

    按文件 mtime 检测外部变化：characters.json 在插件启动后新增、
    修改或恢复时，无需重载插件即可生效。
    """

    def __init__(self, json_path: str | Path):
        self._json_path = Path(json_path)
        self._alias_map: dict[str, list[str]] = {}
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
                    targets = self._alias_map.setdefault(name, [])
                    if fullname not in targets:
                        targets.append(fullname)
            logger.info("Persona+ 已加载 %d 个别名/名称", len(self._alias_map))
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Persona+ 加载 characters.json 失败: %s", exc)

    def resolve(self, text: str) -> str | None:
        """精确匹配别名 → 唯一人格ID（多目标时返回 None 交由候选流程）。"""
        targets = self.resolve_all(text)
        return targets[0] if len(targets) == 1 else None

    def resolve_all(self, text: str) -> list[str]:
        """精确匹配别名 → 所有命中的人格ID 列表。"""
        self._ensure_loaded()
        key = text.strip().lower()
        return list(self._alias_map.get(key, ()))

    def alias_targets(self) -> dict[str, list[str]]:
        """返回 别名(小写) → 人格ID列表 的映射副本，供近似匹配使用。"""
        self._ensure_loaded()
        return {k: list(v) for k, v in self._alias_map.items()}

    def search(self, text: str, valid_ids: set[str] | None = None) -> list[str]:
        """搜索别名中含 text 的人格ID；精确命中别名时直接返回对应目标。"""
        self._ensure_loaded()
        text_lower = text.strip().lower()
        if not text_lower:
            return []

        exact = self._alias_map.get(text_lower)
        if exact:
            if valid_ids is None:
                return list(exact)
            filtered = [t for t in exact if t in valid_ids]
            if filtered:
                return filtered

        # 单字母 ASCII 仅允许精确别名命中，避免子串匹配产生大量无关噪声
        if len(text_lower) == 1 and text_lower.isascii():
            return []

        matched: list[str] = []
        seen: set[str] = set()
        for alias, targets in self._alias_map.items():
            if text_lower in alias:
                for fullname in targets:
                    if valid_ids is not None and fullname not in valid_ids:
                        continue
                    if fullname not in seen:
                        seen.add(fullname)
                        matched.append(fullname)
        return matched
