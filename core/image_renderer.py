from __future__ import annotations

import os
import uuid
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

from astrbot.api import logger

FONT_PATH = Path(__file__).resolve().parent.parent / "MiSans-Medium.ttf"

SCALE = 2

CANVAS_WIDTH = 600 * SCALE
SECTION_COLS = 2
SECTION_GAP = 20 * SCALE
CARD_COLS = 2
CARD_COL_GAP = 12 * SCALE
CARD_ROW_GAP = 10 * SCALE

COLOR_BG = "#F2F2F7"
COLOR_CARD = "#FFFFFF"
COLOR_PRIMARY = "#1D1D1F"
COLOR_SECONDARY = "#8E8E93"
COLOR_ACCENT = "#007AFF"
COLOR_SECTION = "#636366"
COLOR_SEPARATOR = "#E5E5EA"

CARD_RADIUS = 10 * SCALE
CARD_PADDING_X = 10 * SCALE
CARD_PADDING_Y = 10 * SCALE
CONTENT_PADDING = 32 * SCALE
BADGE_SIZE = 22 * SCALE
BADGE_RADIUS = 6 * SCALE
SECTION_TOP_MARGIN = 12 * SCALE
SECTION_BOTTOM_MARGIN = 6 * SCALE
TITLE_BOTTOM_MARGIN = 16 * SCALE
FOOTER_TOP_MARGIN = 14 * SCALE


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(str(FONT_PATH), size=size * SCALE)


FONT_TITLE = _get_font(22)
FONT_SECTION = _get_font(13)
FONT_ITEM = _get_font(14)
FONT_BADGE = _get_font(11)
FONT_FOOTER = _get_font(11)
FONT_WATERMARK = _get_font(9)


def _rounded_rect(draw: ImageDraw.ImageDraw, xy, radius, fill, outline=None, width=1):
    x1, y1, x2, y2 = xy
    diameter = radius * 2
    draw.pieslice([x1, y1, x1 + diameter, y1 + diameter], 180, 270, fill=fill)
    draw.pieslice([x2 - diameter, y1, x2, y1 + diameter], 270, 360, fill=fill)
    draw.pieslice([x1, y2 - diameter, x1 + diameter, y2], 90, 180, fill=fill)
    draw.pieslice([x2 - diameter, y2 - diameter, x2, y2], 0, 90, fill=fill)
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    if outline:
        draw.arc([x1, y1, x1 + diameter, y1 + diameter], 180, 270, fill=outline, width=width)
        draw.arc([x2 - diameter, y1, x2, y1 + diameter], 270, 360, fill=outline, width=width)
        draw.arc([x1, y2 - diameter, x1 + diameter, y2], 90, 180, fill=outline, width=width)
        draw.arc([x2 - diameter, y2 - diameter, x2, y2], 0, 90, fill=outline, width=width)
        draw.line([x1 + radius, y1, x2 - radius, y1], fill=outline, width=width)
        draw.line([x1 + radius, y2, x2 - radius, y2], fill=outline, width=width)
        draw.line([x1, y1 + radius, x1, y2 - radius], fill=outline, width=width)
        draw.line([x2, y1 + radius, x2, y2 - radius], fill=outline, width=width)


def _draw_card(draw, x, y, w, h, fill=COLOR_CARD):
    _rounded_rect(draw, [x, y, x + w, y + h], CARD_RADIUS, fill=fill)


def _draw_badge(draw, x, y, size, text, fill=COLOR_ACCENT):
    _rounded_rect(draw, [x, y, x + size, y + size], BADGE_RADIUS, fill=fill)
    bbox = draw.textbbox((0, 0), text, font=FONT_BADGE)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    tx = x + (size - tw) / 2
    ty = y + (size - th) / 2 - bbox[1]
    draw.text((tx, ty), text, fill="#FFFFFF", font=FONT_BADGE)


def _draw_section_header(draw, x, label, y):
    line_w = 3 * SCALE
    line_h = 12 * SCALE
    draw.rounded_rectangle([x, y, x + line_w, y + line_h], radius=line_w // 2, fill=COLOR_ACCENT)
    text_x = x + line_w + 6 * SCALE
    draw.text((text_x, y - 4 * SCALE), label, fill=COLOR_SECTION, font=FONT_SECTION)
    bbox = draw.textbbox((0, 0), label, font=FONT_SECTION)
    return bbox[3] - bbox[1]


def _section_height(count, card_h) -> float:
    rows = (count + CARD_COLS - 1) // CARD_COLS
    return rows * card_h + max(0, rows - 1) * CARD_ROW_GAP


def build_sections(
    personas: list,
    groups: dict[str, list[str]] | None = None,
) -> tuple[list[tuple[str, list]], list[tuple[str, list]]]:
    """按分组构建左/右两列的 section 列表，顺序与图片渲染一致。

    返回 (left_sections, right_sections)，每个元素为 (分组名, [persona])。
    """
    section_labels: list[tuple[str, list]] = []
    assigned = set()
    if groups:
        for gname in groups:
            gids = groups[gname]
            matched = [p for p in personas if p.persona_id in gids or p.persona_id.strip() in [x.strip() for x in gids]]
            if matched:
                section_labels.append((gname, matched))
                for p in matched:
                    assigned.add(p.persona_id)
        unassigned = [p for p in personas if p.persona_id not in assigned]
        if unassigned:
            section_labels.append(("未分组", unassigned))
            for p in unassigned:
                assigned.add(p.persona_id)
    else:
        section_labels = [("", personas)]

    num_sections = len(section_labels)
    left_count = (num_sections + 1) // 2
    return section_labels[:left_count], section_labels[left_count:]


def compute_display_order(
    personas: list,
    groups: dict[str, list[str]] | None = None,
) -> list:
    """返回按图片渲染顺序（即显示编号顺序）排列的 persona 列表。

    图片编号规则：先左列各分组自上而下，再右列各分组自上而下。
    """
    left_sections, right_sections = build_sections(personas, groups)
    ordered: list = []
    for _, sec_personas in left_sections:
        ordered.extend(sec_personas)
    for _, sec_personas in right_sections:
        ordered.extend(sec_personas)
    return ordered


def render_persona_switch_list(
    personas: list,
    output_dir: str | Path,
    groups: dict[str, list[str]] | None = None,
) -> str:
    content_w = CANVAS_WIDTH - CONTENT_PADDING * 2
    col_w = (content_w - SECTION_GAP * (SECTION_COLS - 1)) // SECTION_COLS
    card_w = (col_w - CARD_COL_GAP * (CARD_COLS - 1)) // CARD_COLS
    card_h = CARD_PADDING_Y * 2 + BADGE_SIZE

    draw = ImageDraw.Draw(Image.new("RGBA", (1, 1), (0, 0, 0, 0)))

    left_sections, right_sections = build_sections(personas, groups)

    sec_header_overhead = SECTION_TOP_MARGIN + SECTION_BOTTOM_MARGIN + 16 * SCALE

    def _col_height(sections):
        h = 0
        for sec_label, sec_personas in sections:
            if sec_label:
                h += sec_header_overhead
            h += _section_height(len(sec_personas), card_h)
        return h

    left_col_h = _col_height(left_sections)
    right_col_h = _col_height(right_sections)
    columns_body_h = max(left_col_h, right_col_h)

    title_h = 32 * SCALE
    footer_h = 20 * SCALE
    total_h = CONTENT_PADDING + title_h + TITLE_BOTTOM_MARGIN + columns_body_h + FOOTER_TOP_MARGIN + footer_h + CONTENT_PADDING

    img = Image.new("RGB", (CANVAS_WIDTH, int(total_h)), COLOR_BG)
    draw = ImageDraw.Draw(img)

    y = CONTENT_PADDING
    title_text = "人格切换"
    bbox = draw.textbbox((0, 0), title_text, font=FONT_TITLE)
    tw = bbox[2] - bbox[0]
    tx = (CANVAS_WIDTH - tw) / 2
    draw.text((tx, y), title_text, fill=COLOR_PRIMARY, font=FONT_TITLE)
    y += title_h + TITLE_BOTTOM_MARGIN
    body_y = y

    left_x = CONTENT_PADDING
    right_x = CONTENT_PADDING + col_w + SECTION_GAP

    divider_x = CONTENT_PADDING + col_w + SECTION_GAP // 2
    draw.line(
        [divider_x, body_y, divider_x, body_y + columns_body_h],
        fill=COLOR_SEPARATOR,
        width=1 * SCALE,
    )

    global_idx = 0

    def _draw_section_column(sections, col_x):
        nonlocal global_idx
        cur_y = body_y
        for sec_label, sec_personas in sections:
            if sec_label:
                cur_y += SECTION_TOP_MARGIN
                sh = _draw_section_header(draw, col_x, sec_label, cur_y)
                cur_y += sh + SECTION_BOTTOM_MARGIN

            for i, persona in enumerate(sec_personas):
                global_idx += 1
                ccol = i % CARD_COLS
                crow = i // CARD_COLS
                card_x = col_x + ccol * (card_w + CARD_COL_GAP)
                card_y = cur_y + crow * (card_h + CARD_ROW_GAP)

                _draw_card(draw, card_x, card_y, card_w, card_h)

                badge_x = card_x + CARD_PADDING_X
                badge_y = card_y + (card_h - BADGE_SIZE) / 2
                _draw_badge(draw, badge_x, badge_y, BADGE_SIZE, str(global_idx))

                name_x = badge_x + BADGE_SIZE + 10 * SCALE
                persona_name = persona.persona_id[:5]
                nb = draw.textbbox((0, 0), persona_name, font=FONT_ITEM)
                nh = nb[3] - nb[1]
                name_y = card_y + (card_h - nh) / 2 - nb[1]
                draw.text((name_x, name_y), persona_name, fill=COLOR_PRIMARY, font=FONT_ITEM)

            rows = (len(sec_personas) + CARD_COLS - 1) // CARD_COLS
            cur_y += rows * card_h + max(0, rows - 1) * CARD_ROW_GAP

    _draw_section_column(left_sections, left_x)
    _draw_section_column(right_sections, right_x)

    y = body_y + columns_body_h + FOOTER_TOP_MARGIN

    hint_text = "回复序号即可切换，回复「取消」即可退出"
    bbox = draw.textbbox((0, 0), hint_text, font=FONT_FOOTER)
    tw = bbox[2] - bbox[0]
    tx = (CANVAS_WIDTH - tw) / 2
    draw.text((tx, y), hint_text, fill=COLOR_SECONDARY, font=FONT_FOOTER)

    watermark_text = "Designed by 慵懒午睡  Generated by mzkbot"
    wb = draw.textbbox((0, 0), watermark_text, font=FONT_WATERMARK)
    ww = wb[2] - wb[0]
    wh = wb[3] - wb[1]
    wm_x = CANVAS_WIDTH - ww - 4 * SCALE
    wm_y = int(total_h) - wh - 2 * SCALE
    draw.text((wm_x, wm_y), watermark_text, fill=COLOR_SECONDARY, font=FONT_WATERMARK)

    os.makedirs(output_dir, exist_ok=True)
    filename = f"persona_switch_{uuid.uuid4().hex[:8]}.png"
    out_path = os.path.join(output_dir, filename)
    img.save(out_path, "PNG")
    logger.info("Persona+ 已渲染人格切换列表图片: %s", out_path)
    return out_path