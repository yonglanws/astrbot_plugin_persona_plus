from __future__ import annotations

import base64
import html as html_lib
import os
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

try:
    from astrbot.api import logger
except ImportError:  # 脱离 AstrBot 独立渲染预览时使用
    import logging

    logger = logging.getLogger("persona_plus.renderer")

PLUGIN_ROOT = Path(__file__).resolve().parent.parent
FONT_PATH = PLUGIN_ROOT / "MiSans-Medium.ttf"
LOGO_DIR = PLUGIN_ROOT / "asset" / "logo"
ICON_DIR = PLUGIN_ROOT / "asset" / "board_icon"

SCALE = 2

SECTION_COLS = 3
CARD_COLS = 2
CANVAS_WIDTH = 1152 * SCALE
CONTENT_PADDING = 30 * SCALE
SECTION_GAP = 30 * SCALE
CARD_COL_GAP = 12 * SCALE
CARD_ROW_GAP = 12 * SCALE

COL_WIDTH = (
    CANVAS_WIDTH - CONTENT_PADDING * 2 - SECTION_GAP * (SECTION_COLS - 1)
) // SECTION_COLS
CARD_WIDTH = (COL_WIDTH - CARD_COL_GAP * (CARD_COLS - 1)) // CARD_COLS

CARD_RADIUS = 16 * SCALE
CARD_PADDING_X = 8 * SCALE
CARD_PADDING_Y = 11 * SCALE
AVATAR_SIZE = 38 * SCALE
AVATAR_RADIUS = 13 * SCALE
BADGE_SIZE = 18 * SCALE
BADGE_RADIUS = 7 * SCALE

SECTION_TOP_MARGIN = 20 * SCALE
SECTION_BOTTOM_MARGIN = 14 * SCALE
LOGO_HEIGHT = 58 * SCALE
TEXT_HEADER_HEIGHT = 24 * SCALE
TITLE_BOTTOM_MARGIN = 24 * SCALE
FOOTER_TOP_MARGIN = 18 * SCALE

# 不参与渲染的 persona_id（AstrBot 内置默认人格）
EXCLUDE_PERSONA_IDS = {"default"}

# 分组 → 组合 logo（asset/logo 下）：有 logo 的分组用大图替代文字标题。
# 没配 logo 的分组（含"未分组"）一律纯文字标题。
GROUP_LOGOS = {
    "25点，Nightcord见。": "25.png",
    "Wonderlands×Showtime": "ws.png",
    "Vivid BAD SQUAD": "vbs.png",
    "MORE MORE JUMP!": "mmj.png",
    "Leo/need": "ln.png",
    "MyGO!!!!!": "MyGO!!!!!.png",
    "Ave Mujica": "AveMujica.png",
    "millsage": "millsage.png",
    "梦限大MewType": "Mewtype.png",
    "一家Dumb Rock!": "Dumbrock.png",
}

# 分组主题色（用于序号徽章）
GROUP_COLORS = {
    "25点，Nightcord见。": "#5A6BD8",
    "Wonderlands×Showtime": "#F0A33C",
    "Vivid BAD SQUAD": "#E4605C",
    "MORE MORE JUMP!": "#3EB58C",
    "Leo/need": "#4C8DE8",
    "家长们": "#98959E",
    "MyGO!!!!!": "#5F94E8",
    "Ave Mujica": "#D65E9C",
    "millsage": "#7A63BD",
    "梦限大MewType": "#39BDB4",
    "一家Dumb Rock!": "#C88A3C",
}
DEFAULT_ACCENT = "#5B6CFF"

COLOR_TITLE = "#1D1D1F"
COLOR_TEXT = "#2C2C2E"
COLOR_HINT = "#8E8E93"
BG_TOP = (247, 248, 252)
BG_BOTTOM = (231, 235, 245)
CARD_COLOR = "#FFFFFF"
CARD_SHADOW = (90, 100, 140, 60)
AVATAR_BG = "#F2F3F8"
AVATAR_BORDER = "#E8EAF1"

_logo_cache: dict[str, Image.Image | None] = {}
_icon_cache: dict[str, Image.Image | None] = {}


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size * SCALE)


FONT_TITLE = _get_font(34)
FONT_SUBTITLE = _get_font(13)
FONT_SECTION = _get_font(17)
FONT_ITEM = _get_font(15)
FONT_BADGE = _get_font(11)
FONT_FOOTER = _get_font(13)
FONT_WATERMARK = _get_font(9)


def _load_group_logo(group_name: str) -> Image.Image | None:
    filename = GROUP_LOGOS.get(group_name)
    if not filename:
        return None
    if filename not in _logo_cache:
        path = LOGO_DIR / filename
        logo = None
        try:
            logo = Image.open(path).convert("RGBA")
            ratio = LOGO_HEIGHT / logo.height
            if logo.width * ratio > COL_WIDTH:
                ratio = COL_WIDTH / logo.width
            logo = logo.resize(
                (int(logo.width * ratio), int(logo.height * ratio)), Image.LANCZOS
            )
        except OSError:
            logger.warning("Persona+ 分组 logo 缺失: %s", path)
            logo = None
        _logo_cache[filename] = logo
    return _logo_cache[filename]


def _load_persona_icon(persona_id: str) -> Image.Image | None:
    if persona_id not in _icon_cache:
        path = ICON_DIR / f"{persona_id}.png"
        icon = None
        if path.exists():
            try:
                icon = Image.open(path).convert("RGBA")
            except OSError:
                icon = None
        _icon_cache[persona_id] = icon
    return _icon_cache[persona_id]


def _rounded_avatar(icon: Image.Image) -> Image.Image:
    """把角色图标等比缩放放进圆角方形底板（不裁切）。"""
    size = AVATAR_SIZE
    box = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    inner = size - 2 * SCALE
    scaled = icon.copy()
    scaled.thumbnail((inner, inner), Image.LANCZOS)
    draw = ImageDraw.Draw(box)
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1], radius=AVATAR_RADIUS, fill=AVATAR_BG
    )
    box.paste(scaled, ((size - scaled.width) // 2, (size - scaled.height) // 2), scaled)
    draw.rounded_rectangle(
        [0, 0, size - 1, size - 1],
        radius=AVATAR_RADIUS,
        outline=AVATAR_BORDER,
        width=SCALE,
    )
    return box


def _section_height(count: int, card_h: int) -> int:
    rows = (count + CARD_COLS - 1) // CARD_COLS
    return rows * card_h + max(0, rows - 1) * CARD_ROW_GAP


def _section_header_overhead(label: str) -> int:
    if not label:
        return 0
    has_logo = _load_group_logo(label) is not None
    return SECTION_TOP_MARGIN + SECTION_BOTTOM_MARGIN + (
        LOGO_HEIGHT if has_logo else TEXT_HEADER_HEIGHT
    )


def _visible_personas(personas: list) -> list:
    """剔除不渲染的 persona（如内置 default）。"""
    return [p for p in personas if getattr(p, "persona_id", "") not in EXCLUDE_PERSONA_IDS]


def build_sections(
    personas: list,
    groups: dict[str, list[str]] | None = None,
) -> list[list[tuple[str, list]]]:
    """按分组构建多列布局，返回每个分组的 section 列表（按列组织）。

    返回 [ [ (分组名, [persona]), ... ]（第一列）, ... ]（第二、三列）。
    分组按配置顺序依次放入当前最矮的列（按估算高度均衡三列）。
    """
    personas = _visible_personas(personas)
    section_labels: list[tuple[str, list]] = []
    assigned = set()
    if groups:
        for gname in groups:
            gids = groups[gname]
            stripped = [x.strip() for x in gids]
            matched = [
                p
                for p in personas
                if p.persona_id in gids or p.persona_id.strip() in stripped
            ]
            if matched:
                section_labels.append((gname, matched))
                for p in matched:
                    assigned.add(p.persona_id)
        unassigned = [p for p in personas if p.persona_id not in assigned]
        if unassigned:
            section_labels.append(("未分组", unassigned))
    else:
        section_labels = [("", personas)]

    card_h = CARD_PADDING_Y * 2 + max(AVATAR_SIZE, BADGE_SIZE)
    columns: list[list[tuple[str, list]]] = [[] for _ in range(SECTION_COLS)]
    heights = [0] * SECTION_COLS
    for name, sec in section_labels:
        weight = _section_height(len(sec), card_h) + _section_header_overhead(name)
        idx = heights.index(min(heights))
        columns[idx].append((name, sec))
        heights[idx] += weight
    return columns


def compute_display_order(
    personas: list,
    groups: dict[str, list[str]] | None = None,
) -> list:
    """返回按图片渲染顺序（即显示编号顺序）排列的 persona 列表。

    图片编号规则：按列从左到右，列内各分组自上而下。
    """
    ordered: list = []
    for col in build_sections(personas, groups):
        for _, sec_personas in col:
            ordered.extend(sec_personas)
    return ordered


def _gradient_background(width: int, height: int) -> Image.Image:
    strip = Image.new("RGB", (1, height))
    for y in range(height):
        t = y / max(1, height - 1)
        strip.putpixel(
            (0, y),
            tuple(int(BG_TOP[i] + (BG_BOTTOM[i] - BG_TOP[i]) * t) for i in range(3)),
        )
    return strip.resize((width, height))


def _draw_text_truncated(draw, x, y, text, font, max_width, fill) -> None:
    if draw.textlength(text, font=font) <= max_width:
        draw.text((x, y), text, fill=fill, font=font)
        return
    while text and draw.textlength(text + "…", font=font) > max_width:
        text = text[:-1]
    draw.text((x, y), text + "…", fill=fill, font=font)


def render_persona_switch_list(
    personas: list,
    output_dir: str | Path,
    groups: dict[str, list[str]] | None = None,
) -> str:
    card_h = CARD_PADDING_Y * 2 + max(AVATAR_SIZE, BADGE_SIZE)

    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))
    columns = build_sections(personas, groups)

    def _col_height(col) -> int:
        h = 0
        for sec_label, sec_personas in col:
            h += _section_header_overhead(sec_label)
            h += _section_height(len(sec_personas), card_h)
        return h

    columns_body_h = max((_col_height(col) for col in columns), default=0)

    # ---- 页眉：标题 + 副标题 ----
    title_text = "人格切换"
    subtitle_text = "· Persona Switch ·"
    title_bbox = probe.textbbox((0, 0), title_text, font=FONT_TITLE)
    title_h = title_bbox[3] - title_bbox[1]
    sub_bbox = probe.textbbox((0, 0), subtitle_text, font=FONT_SUBTITLE)
    subtitle_h = sub_bbox[3] - sub_bbox[1]

    header_h = title_h + 8 * SCALE + subtitle_h + TITLE_BOTTOM_MARGIN

    footer_h = 20 * SCALE
    total_h = int(
        CONTENT_PADDING
        + header_h
        + columns_body_h
        + FOOTER_TOP_MARGIN
        + footer_h
        + CONTENT_PADDING
    )

    # ---- 第一阶段：纯布局，收集卡片/分组头位置 ----
    body_y = CONTENT_PADDING + header_h

    cards: list[dict] = []  # {x, y, idx, persona, accent}
    headers: list[dict] = []  # {x, y, label, logo}

    for col_i, col in enumerate(columns):
        col_x = CONTENT_PADDING + col_i * (COL_WIDTH + SECTION_GAP)
        cur_y = body_y
        for sec_label, sec_personas in col:
            accent = GROUP_COLORS.get(sec_label, DEFAULT_ACCENT)
            if sec_label:
                cur_y += SECTION_TOP_MARGIN
                headers.append(
                    {
                        "x": col_x,
                        "y": cur_y,
                        "label": sec_label,
                        "logo": _load_group_logo(sec_label),
                    }
                )
                cur_y += _section_header_overhead(sec_label) - SECTION_TOP_MARGIN
            for i, persona in enumerate(sec_personas):
                ccol = i % CARD_COLS
                crow = i // CARD_COLS
                cards.append(
                    {
                        "x": col_x + ccol * (CARD_WIDTH + CARD_COL_GAP),
                        "y": cur_y + crow * (card_h + CARD_ROW_GAP),
                        "idx": len(cards) + 1,
                        "persona": persona,
                        "accent": accent,
                    }
                )
            rows = (len(sec_personas) + CARD_COLS - 1) // CARD_COLS
            cur_y += rows * card_h + max(0, rows - 1) * CARD_ROW_GAP

    # ---- 第二阶段：背景 + 阴影 + 内容 ----
    img = _gradient_background(CANVAS_WIDTH, total_h).convert("RGBA")

    shadow_layer = Image.new("RGBA", img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    for c in cards:
        shadow_draw.rounded_rectangle(
            [c["x"] + SCALE, c["y"] + 3 * SCALE, c["x"] + CARD_WIDTH, c["y"] + card_h + SCALE],
            radius=CARD_RADIUS,
            fill=CARD_SHADOW,
        )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(4 * SCALE))
    img = Image.alpha_composite(img, shadow_layer)
    draw = ImageDraw.Draw(img)

    # 页眉
    y = CONTENT_PADDING
    tw = title_bbox[2] - title_bbox[0]
    draw.text(((CANVAS_WIDTH - tw) / 2, y - title_bbox[1]), title_text, fill=COLOR_TITLE, font=FONT_TITLE)
    y += title_h + 8 * SCALE
    sw = sub_bbox[2] - sub_bbox[0]
    draw.text(
        ((CANVAS_WIDTH - sw) / 2, y - sub_bbox[1]), subtitle_text, fill=COLOR_HINT, font=FONT_SUBTITLE
    )

    # 分组头：有 logo 用 logo，否则纯文字
    for h in headers:
        if h["logo"] is not None:
            img.paste(h["logo"], (h["x"], h["y"]), h["logo"])
        else:
            draw.text((h["x"], h["y"] - 2 * SCALE), h["label"], fill=COLOR_TEXT, font=FONT_SECTION)

    # 卡片
    for c in cards:
        cx, cy = c["x"], c["y"]
        draw.rounded_rectangle(
            [cx, cy, cx + CARD_WIDTH, cy + card_h], radius=CARD_RADIUS, fill=CARD_COLOR
        )

        badge_x = cx + CARD_PADDING_X
        badge_y = cy + (card_h - BADGE_SIZE) / 2
        draw.rounded_rectangle(
            [badge_x, badge_y, badge_x + BADGE_SIZE, badge_y + BADGE_SIZE],
            radius=BADGE_RADIUS,
            fill=c["accent"],
        )
        idx_text = str(c["idx"])
        ib = probe.textbbox((0, 0), idx_text, font=FONT_BADGE)
        draw.text(
            (
                badge_x + (BADGE_SIZE - (ib[2] - ib[0])) / 2 - ib[0],
                badge_y + (BADGE_SIZE - (ib[3] - ib[1])) / 2 - ib[1],
            ),
            idx_text,
            fill="#FFFFFF",
            font=FONT_BADGE,
        )

        cursor_x = badge_x + BADGE_SIZE + 7 * SCALE
        icon = _load_persona_icon(c["persona"].persona_id)
        if icon is not None:
            avatar_box = _rounded_avatar(icon)
            img.paste(
                avatar_box,
                (int(cursor_x), int(cy + (card_h - AVATAR_SIZE) / 2)),
                avatar_box,
            )
            cursor_x += AVATAR_SIZE + 8 * SCALE

        name_max_w = cx + CARD_WIDTH - CARD_PADDING_X - cursor_x
        nb = probe.textbbox((0, 0), "测", font=FONT_ITEM)
        _draw_text_truncated(
            draw,
            int(cursor_x),
            int(cy + (card_h - (nb[3] - nb[1])) / 2 - nb[1]),
            c["persona"].persona_id,
            FONT_ITEM,
            name_max_w,
            COLOR_TEXT,
        )

    # 页脚
    foot_y = body_y + columns_body_h + FOOTER_TOP_MARGIN
    hint_text = "回复序号即可切换 · 回复「取消」退出"
    hb = probe.textbbox((0, 0), hint_text, font=FONT_FOOTER)
    draw.text(
        ((CANVAS_WIDTH - (hb[2] - hb[0])) / 2, foot_y - hb[1]),
        hint_text,
        fill=COLOR_HINT,
        font=FONT_FOOTER,
    )

    watermark_text = "Designed by 慵懒午睡  Generated by mzkbot"
    wb = probe.textbbox((0, 0), watermark_text, font=FONT_WATERMARK)
    draw.text(
        (CANVAS_WIDTH - (wb[2] - wb[0]) - 4 * SCALE, total_h - (wb[3] - wb[1]) - 2 * SCALE),
        watermark_text,
        fill=COLOR_HINT,
        font=FONT_WATERMARK,
    )

    os.makedirs(output_dir, exist_ok=True)
    filename = f"persona_switch_{uuid.uuid4().hex[:8]}.png"
    out_path = os.path.join(output_dir, filename)
    img.convert("RGB").save(out_path, "PNG")
    logger.info("Persona+ 已渲染人格切换列表图片: %s", out_path)
    return out_path


_HTML_THEME_COLORS: dict[str, tuple[str, str]] = {
    "25点，Nightcord见。": ("#4F46E5", "#EEF2FF"),
    "Wonderlands×Showtime": ("#D97706", "#FEF3C7"),
    "Vivid BAD SQUAD": ("#DC2626", "#FEE2E2"),
    "MORE MORE JUMP!": ("#059669", "#D1FAE5"),
    "Leo/need": ("#2563EB", "#DBEAFE"),
    "家长们": ("#52525B", "#F4F4F5"),
    "25时的家长们": ("#52525B", "#F4F4F5"),
    "MyGO!!!!!": ("#0284C7", "#E0F2FE"),
    "Ave Mujica": ("#C026D3", "#FAE8FF"),
    "millsage": ("#7C3AED", "#EDE9FE"),
    "梦限大MewType": ("#0D9488", "#CCFBF1"),
    "一家Dumb Rock!": ("#B45309", "#FFEDD5"),
}
_DEFAULT_HTML_THEME = ("#4F46E5", "#EEF2FF")
_data_uri_cache: dict[str, str | None] = {}


def _file_to_data_uri(path: Path) -> str | None:
    key = str(path)
    if key not in _data_uri_cache:
        uri = None
        if path.exists():
            try:
                b64 = base64.b64encode(path.read_bytes()).decode("ascii")
                uri = f"data:image/png;base64,{b64}"
            except OSError:
                uri = None
        _data_uri_cache[key] = uri
    return _data_uri_cache[key]


def render_persona_switch_html(
    personas: list,
    groups: dict[str, list[str]] | None = None,
) -> str:
    """生成用于 AstrBot t2i（html_render）的高可读性人格切换 HTML 页面。

    与 build_sections / compute_display_order 保持完全一致的列序与编号。
    无头像的角色不渲染头像框或占位文字。
    """
    columns = build_sections(personas, groups)
    font_uri = FONT_PATH.resolve().as_uri() if FONT_PATH.exists() else ""

    idx_counter = 1
    total_groups = 0
    columns_html: list[str] = []

    for col in columns:
        sec_blocks: list[str] = []
        for gname, sec_personas in col:
            total_groups += 1
            display_group = gname or "全部人格"
            accent, soft_bg = _HTML_THEME_COLORS.get(gname, _DEFAULT_HTML_THEME)

            logo_file = GROUP_LOGOS.get(gname)
            logo_uri = _file_to_data_uri(LOGO_DIR / logo_file) if logo_file else None
            if logo_uri:
                header_inner = (
                    f'<img class="group-logo" src="{logo_uri}" '
                    f'alt="{html_lib.escape(display_group)}">'
                )
            else:
                header_inner = (
                    f'<span class="group-title-text">{html_lib.escape(display_group)}</span>'
                )

            rows_html: list[str] = []
            for persona in sec_personas:
                pid = getattr(persona, "persona_id", "")
                cur_idx = idx_counter
                idx_counter += 1
                icon_uri = _file_to_data_uri(ICON_DIR / f"{pid}.png")
                if icon_uri:
                    avatar_html = (
                        f'<div class="avatar-wrap">'
                        f'<img class="avatar-img" src="{icon_uri}" alt="{html_lib.escape(pid)}">'
                        f'</div>'
                    )
                else:
                    avatar_html = ""

                rows_html.append(
                    f'<div class="persona-item">'
                    f'<span class="idx-pill" style="color: {accent}; background: {soft_bg};">{cur_idx}</span>'
                    f'{avatar_html}'
                    f'<span class="persona-name">{html_lib.escape(pid)}</span>'
                    f'</div>'
                )

            sec_blocks.append(
                f'<section class="group-card">'
                f'<header class="group-header" style="border-left-color: {accent};">'
                f'<div class="group-brand">{header_inner}</div>'
                f'<span class="group-count">{len(sec_personas)}</span>'
                f'</header>'
                f'<div class="persona-grid">{"".join(rows_html)}</div>'
                f'</section>'
            )
        columns_html.append(f'<div class="col-stack">{"".join(sec_blocks)}</div>')

    total_personas = idx_counter - 1
    font_face = (
        f'@font-face {{ font-family: "MiSansCustom"; src: url("{font_uri}") format("truetype"); font-weight: 400 700; }}'
        if font_uri
        else ""
    )

    return f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<style>
  {font_face}
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{
    font-family: "MiSansCustom", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif;
    background: #F4F5F7;
    color: #111827;
    width: 1320px;
    margin: 0 auto;
    padding: 26px 28px 22px;
    -webkit-font-smoothing: antialiased;
  }}
  .topbar {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 18px;
    padding: 0 2px;
  }}
  .topbar-left {{ display: flex; align-items: baseline; gap: 12px; }}
  .page-title {{ font-size: 30px; font-weight: 700; letter-spacing: -0.02em; color: #111827; }}
  .page-sub {{ font-size: 14px; color: #6B7280; font-weight: 500; }}
  .topbar-right {{
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 13px;
    color: #4B5563;
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    padding: 7px 14px;
    border-radius: 10px;
  }}
  .kbd {{
    display: inline-block;
    padding: 1px 6px;
    border-radius: 5px;
    background: #F3F4F6;
    border: 1px solid #D1D5DB;
    font-size: 12px;
    font-weight: 700;
    color: #111827;
  }}
  .board {{
    display: grid;
    grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 18px;
    align-items: start;
  }}
  .col-stack {{ display: flex; flex-direction: column; gap: 18px; }}
  .group-card {{
    background: #FFFFFF;
    border: 1px solid #E5E7EB;
    border-radius: 16px;
    padding: 14px 14px 16px;
    box-shadow: 0 1px 3px rgba(17, 24, 39, 0.04);
  }}
  .group-header {{
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 2px 2px 10px 10px;
    margin-bottom: 10px;
    border-bottom: 1px solid #F3F4F6;
    border-left: 4px solid #4F46E5;
    min-height: 44px;
  }}
  .group-brand {{ display: flex; align-items: center; max-width: 310px; }}
  .group-logo {{ max-height: 38px; max-width: 240px; width: auto; height: auto; object-fit: contain; display: block; }}
  .group-title-text {{ font-size: 17px; font-weight: 700; color: #111827; }}
  .group-count {{
    font-size: 12px;
    font-weight: 600;
    color: #6B7280;
    background: #F3F4F6;
    padding: 2px 8px;
    border-radius: 999px;
  }}
  .persona-grid {{ display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 8px; }}
  .persona-item {{
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 6px 10px;
    border-radius: 10px;
    background: #F9FAFB;
    border: 1px solid #F1F3F5;
    min-height: 48px;
  }}
  .idx-pill {{
    flex-shrink: 0;
    min-width: 26px;
    height: 24px;
    padding: 0 5px;
    border-radius: 7px;
    font-size: 12px;
    font-weight: 700;
    font-variant-numeric: tabular-nums;
    display: inline-flex;
    align-items: center;
    justify-content: center;
  }}
  .avatar-wrap {{
    flex-shrink: 0;
    width: 36px;
    height: 36px;
    display: flex;
    align-items: center;
    justify-content: center;
  }}
  .avatar-img {{ max-width: 36px; max-height: 36px; width: auto; height: auto; object-fit: contain; display: block; }}
  .persona-name {{
    font-size: 15px;
    font-weight: 600;
    color: #111827;
    line-height: 1.25;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }}
  .footer {{
    margin-top: 18px;
    padding: 0 2px;
    display: flex;
    align-items: center;
    justify-content: space-between;
    font-size: 12px;
    color: #6B7280;
  }}
</style>
</head>
<body>
  <header class="topbar">
    <div class="topbar-left">
      <h1 class="page-title">人格切换</h1>
      <span class="page-sub">共 {total_personas} 位角色 · {total_groups} 个团体</span>
    </div>
    <div class="topbar-right">
      <span>回复 <span class="kbd">序号</span> 切换</span>
      <span>·</span>
      <span>快捷 <span class="kbd">pp 角色名</span></span>
      <span>·</span>
      <span>回复 <span class="kbd">取消</span> 退出</span>
    </div>
  </header>
  <main class="board">{"".join(columns_html)}</main>
  <footer class="footer">
    <span>Persona Plus</span>
    <span>Designed by 慵懒午睡 · Generated by mzkbot</span>
  </footer>
</body>
</html>"""
