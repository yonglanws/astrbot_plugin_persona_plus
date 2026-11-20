"""独立渲染人格切换页预览（不走 AstrBot）。"""
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.image_renderer import render_persona_switch_list

DB_PATH = "Z:/astrbot/data/data_v4.db"
CONFIG_PATH = "Z:/astrbot/data/config/astrbot_plugin_persona_plus_config.json"

with sqlite3.connect(DB_PATH) as con:
    ids = [r[0] for r in con.execute("SELECT persona_id FROM personas ORDER BY id")]

raw = json.loads(Path(CONFIG_PATH).read_text("utf-8-sig"))

# 与 main.py _sort_personas 一致：persona_order 优先，其余按库内顺序补后
order = raw.get("persona_order", [])
seen, ordered = set(), []
for pid in order:
    if pid in ids and pid not in seen:
        ordered.append(pid)
        seen.add(pid)
ordered += [pid for pid in ids if pid not in seen]

personas = [SimpleNamespace(persona_id=pid) for pid in ordered]
print(f"personas: {len(personas)}")

groups = {}
for line in raw.get("persona_groups", []):
    name, _, members = line.partition(":")
    groups[name.strip()] = [m.strip() for m in members.split(",") if m.strip()]
print(f"groups: {list(groups)}")

out = render_persona_switch_list(
    personas, Path(__file__).resolve().parent, groups=groups or None
)
print("rendered:", out)
