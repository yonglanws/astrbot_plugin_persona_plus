from __future__ import annotations

import json
import threading
from pathlib import Path

from astrbot.api import logger


class GroupPersonaStore:
    """按群聊持久化存储人格选择，同一群聊内所有用户共享一个人格，私聊按用户独立。"""

    def __init__(self, store_path: Path):
        self._store_path = store_path
        self._data: dict[str, str] = {}
        self._lock = threading.Lock()
        self._load()

    def _load(self) -> None:
        if not self._store_path.exists():
            return
        try:
            raw = self._store_path.read_text(encoding="utf-8")
            loaded = json.loads(raw)
            if isinstance(loaded, dict):
                self._data = {k: str(v) for k, v in loaded.items() if v}
            else:
                logger.warning("Persona+ 群聊人格存储格式异常，已重置")
                self._data = {}
        except (json.JSONDecodeError, OSError) as exc:
            logger.warning("Persona+ 读取群聊人格存储失败：%s", exc)
            self._data = {}

    def _save(self) -> None:
        try:
            self._store_path.parent.mkdir(parents=True, exist_ok=True)
            self._store_path.write_text(
                json.dumps(self._data, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.error("Persona+ 写入群聊人格存储失败：%s", exc)

    def get(self, key: str) -> str | None:
        with self._lock:
            return self._data.get(key)

    def set(self, key: str, persona_id: str) -> None:
        with self._lock:
            old = self._data.get(key)
            if old == persona_id:
                return
            self._data[key] = persona_id
            self._save()

    def delete(self, key: str) -> bool:
        with self._lock:
            if key in self._data:
                del self._data[key]
                self._save()
                return True
            return False

    def reset_all(self) -> int:
        with self._lock:
            count = len(self._data)
            self._data.clear()
            self._save()
            return count

    def get_all(self) -> dict[str, str]:
        with self._lock:
            return dict(self._data)

    def get_persona_ids(self) -> set[str]:
        with self._lock:
            return set(self._data.values())
