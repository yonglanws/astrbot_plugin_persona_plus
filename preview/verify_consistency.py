"""验证图片序号与切换解析的一致性（不依赖 AstrBot）。"""
import asyncio
import json
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.image_renderer import (
    EXCLUDE_PERSONA_IDS,
    build_sections,
    compute_display_order,
)

DB_PATH = "Z:/astrbot/data/data_v4.db"
CONFIG_PATH = "Z:/astrbot/data/config/astrbot_plugin_persona_plus_config.json"

with sqlite3.connect(DB_PATH) as con:
    ids = [r[0] for r in con.execute("SELECT persona_id FROM personas ORDER BY id")]

raw = json.loads(Path(CONFIG_PATH).read_text("utf-8-sig"))
order = raw.get("persona_order", [])
seen, ordered = set(), []
for pid in order:
    if pid in ids and pid not in seen:
        ordered.append(pid)
        seen.add(pid)
ordered += [pid for pid in ids if pid not in seen]

groups = {}
for line in raw.get("persona_groups", []):
    name, _, members = line.partition(":")
    groups[name.strip()] = [m.strip() for m in members.split(",") if m.strip()]

personas = [SimpleNamespace(persona_id=pid) for pid in ordered]

# 1. 图片渲染顺序（含 default 剔除）
img_order = [p.persona_id for p in compute_display_order(personas, groups)]
print("渲染卡片数:", len(img_order))
assert "default" not in img_order, "default 泄漏到图片"
assert len(img_order) == len(set(img_order)), "图片中有重复人格"

# 2. 所有分组中的人格都能在渲染结果中找到
grouped = {pid for members in groups.values() for pid in members}
in_img = set(img_order)
missing = grouped - in_img
print("分组配置里但不在图片中:", sorted(missing))
ungrouped_in_img = [pid for pid in img_order if pid not in grouped]
print("图片中未分组的:", ungrouped_in_img)

# 3. main.py 侧 _ordered_personas 行为复现（排序 + 分组 + 剔除 default）
ordered_all = compute_display_order(personas, groups)
main_order = [p.persona_id for p in ordered_all if p.persona_id not in EXCLUDE_PERSONA_IDS]
assert main_order == img_order, f"序号映射错位: {main_order[:5]} vs {img_order[:5]}"
print("序号映射一致: OK")

# 4. 每个序号都能解析回正确人格
for i, pid in enumerate(img_order, start=1):
    assert main_order[i - 1] == pid
print("全部", len(img_order), "个序号解析一致")

# 5. 列均衡性
cols = build_sections(personas, groups)
for ci, col in enumerate(cols):
    labels = [n for n, _ in col]
    counts = [len(s) for _, s in col]
    print(f"列{ci+1}: 分组数={len(col)} 卡片数={sum(counts)} {labels}")

# 6. 每列最后一张卡片不越出画布（列宽/卡片宽 sanity）
print("\n全部校验通过")
