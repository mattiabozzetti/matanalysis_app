from __future__ import annotations

from io import BytesIO
from pathlib import Path
from typing import Any

import math
import pandas as pd
from PIL import Image, ImageDraw, ImageFont


BG = "#070A18"
PANEL = "#10162B"
PANEL2 = "#151B35"
TEXT = "#F6F7FB"
MUTED = "#AFC3E8"
CYAN = "#5FFFE0"
GREEN = "#7CFF8A"
YELLOW = "#FFE66D"
ORANGE = "#FF9F43"
RED = "#FF4F6D"
PURPLE = "#A855F7"
LINE = "#25304E"


def _font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf" if bold else "/System/Library/Fonts/Supplemental/Arial.ttf",
    ]
    for path in candidates:
        if Path(path).exists():
            return ImageFont.truetype(path, size=size)
    return ImageFont.load_default()


F_TITLE = _font(46, True)
F_H1 = _font(34, True)
F_H2 = _font(24, True)
F_BODY = _font(18, False)
F_BODY_B = _font(18, True)
F_SMALL = _font(14, False)
F_SMALL_B = _font(14, True)
F_TINY = _font(12, True)


def _safe(value: Any, fallback: str = "—") -> str:
    if value is None:
        return fallback
    try:
        if pd.isna(value):
            return fallback
    except Exception:
        pass
    return str(value)


def _intish(value: Any, suffix: str = "") -> str:
    try:
        if pd.isna(value):
            return "—"
        return f"{float(value):,.0f}{suffix}".replace(",", ".")
    except Exception:
        return f"{_safe(value)}{suffix}"


def _pct_color(pct: float) -> str:
    try:
        if pd.isna(pct) or math.isnan(float(pct)):
            return "#2E3A59"
        pct = float(pct)
    except Exception:
        return "#2E3A59"
    if pct >= 90:
        return CYAN
    if pct >= 75:
        return GREEN
    if pct >= 50:
        return YELLOW
    if pct >= 25:
        return ORANGE
    return RED


def _score_text(value: float) -> str:
    try:
        if pd.isna(value) or math.isnan(float(value)):
            return "—"
        return f"{float(value):.0f}"
    except Exception:
        return "—"


def _round_rect(draw: ImageDraw.ImageDraw, xy, radius: int, fill: str, outline: str | None = None, width: int = 1):
    draw.rounded_rectangle(xy, radius=radius, fill=fill, outline=outline, width=width)


def _text(draw: ImageDraw.ImageDraw, xy, text: str, font, fill: str = TEXT, anchor: str | None = None):
    draw.text(xy, text, font=font, fill=fill, anchor=anchor)


def _fit_text(draw: ImageDraw.ImageDraw, text: str, font, max_width: int) -> str:
    text = _safe(text)
    if draw.textlength(text, font=font) <= max_width:
        return text
    ell = "…"
    while len(text) > 1 and draw.textlength(text + ell, font=font) > max_width:
        text = text[:-1]
    return text + ell


def _bar(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, h: int, pct: float, reverse: bool = False):
    _round_rect(draw, (x, y, x + w, y + h), radius=h // 2, fill="#27304A")
    try:
        pct_val = 0 if pd.isna(pct) else max(0, min(100, float(pct)))
    except Exception:
        pct_val = 0
    fill_w = int(w * pct_val / 100)
    color = _pct_color(pct_val)
    if reverse:
        _round_rect(draw, (x + w - fill_w, y, x + w, y + h), radius=h // 2, fill=color)
    else:
        _round_rect(draw, (x, y, x + fill_w, y + h), radius=h // 2, fill=color)


def _score_ring(draw: ImageDraw.ImageDraw, cx: int, cy: int, score: float, label: str):
    try:
        s = 0 if pd.isna(score) else max(0, min(100, float(score)))
    except Exception:
        s = 0
    color = _pct_color(s)
    bbox = (cx - 56, cy - 56, cx + 56, cy + 56)
    draw.ellipse(bbox, outline="#27304A", width=10)
    draw.arc(bbox, start=-90, end=-90 + 360 * s / 100, fill=color, width=10)
    _text(draw, (cx, cy - 12), _score_text(score), F_H1, TEXT, anchor="mm")
    _text(draw, (cx, cy + 22), label.upper(), F_TINY, MUTED, anchor="mm")


def _draw_player_block(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, player: pd.Series, overall: float, align: str = "left", is_gk: bool = False):
    name = _fit_text(draw, _safe(player.get("Player")), F_H1, w - 140)
    age = _intish(player.get("Age"), "y")
    mins = _intish(player.get("Minutes played"), " min")
    pos = "GK" if is_gk else _safe(player.get("Position"))
    meta1 = f"{_safe(player.get('Season'))} · {mins} · {age}"
    meta2 = f"{_safe(player.get('Team'))} · {_safe(player.get('League'))} · {pos}"

    if align == "right":
        _text(draw, (x + w, y), name, F_H1, TEXT, anchor="ra")
        _text(draw, (x + w, y + 44), meta1, F_BODY, MUTED, anchor="ra")
        _text(draw, (x + w, y + 70), meta2, F_BODY, MUTED, anchor="ra")
        _score_ring(draw, x + w - 58, y + 136, overall, "overall")
    else:
        _text(draw, (x, y), name, F_H1, TEXT)
        _text(draw, (x, y + 44), meta1, F_BODY, MUTED)
        _text(draw, (x, y + 70), meta2, F_BODY, MUTED)
        _score_ring(draw, x + 58, y + 136, overall, "overall")


def _metric_row(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, row: dict[str, Any]):
    # columns: left value/pct/bar | label | right bar/pct/value
    left_val_w = 70
    pct_w = 42
    bar_w = 205
    label_w = w - (left_val_w + pct_w + bar_w) * 2 - 70
    mid_x = x + left_val_w + pct_w + bar_w + 35

    label = _fit_text(draw, _safe(row.get("label")), F_SMALL_B, label_w)
    sel_value = _safe(row.get("sel_value"))
    cmp_value = _safe(row.get("cmp_value"))
    sel_pct = row.get("sel_pct", float("nan"))
    cmp_pct = row.get("cmp_pct", float("nan"))

    _text(draw, (x + left_val_w, y + 12), sel_value, F_SMALL_B, TEXT, anchor="ra")
    _text(draw, (x + left_val_w + pct_w, y + 12), _score_text(sel_pct), F_SMALL_B, _pct_color(sel_pct), anchor="ra")
    _bar(draw, x + left_val_w + pct_w + 8, y + 7, bar_w, 10, sel_pct, reverse=True)

    _round_rect(draw, (mid_x, y, mid_x + label_w, y + 24), 4, "#1B2342")
    _text(draw, (mid_x + label_w // 2, y + 12), label.upper(), F_TINY, TEXT, anchor="mm")

    right_bar_x = mid_x + label_w + 35
    _bar(draw, right_bar_x, y + 7, bar_w, 10, cmp_pct, reverse=False)
    _text(draw, (right_bar_x + bar_w + pct_w, y + 12), _score_text(cmp_pct), F_SMALL_B, _pct_color(cmp_pct), anchor="ra")
    _text(draw, (right_bar_x + bar_w + pct_w + 10, y + 12), cmp_value, F_SMALL_B, TEXT)


def _group_panel(draw: ImageDraw.ImageDraw, x: int, y: int, w: int, group: dict[str, Any]) -> int:
    rows = group.get("rows", [])
    panel_h = 72 + len(rows) * 32
    color = group.get("color", CYAN)
    _round_rect(draw, (x, y, x + w, y + panel_h), 18, PANEL, outline=color, width=1)
    _text(draw, (x + 22, y + 33), _score_text(group.get("sel_score")), F_BODY_B, _pct_color(group.get("sel_score")), anchor="lm")
    title = f"{group.get('icon','•')} {group.get('name','Group')}"
    _text(draw, (x + w // 2, y + 33), _fit_text(draw, title.upper(), F_BODY_B, w - 220), F_BODY_B, color, anchor="mm")
    _text(draw, (x + w - 22, y + 33), _score_text(group.get("cmp_score")), F_BODY_B, _pct_color(group.get("cmp_score")), anchor="rm")
    draw.line((x + 18, y + 58, x + w - 18, y + 58), fill=LINE, width=1)

    yy = y + 72
    for row in rows:
        _metric_row(draw, x + 18, yy, w - 36, row)
        yy += 32
    return panel_h


def create_comparison_png(
    *,
    selected_player: pd.Series,
    comparison_player: pd.Series,
    selected_overall: float,
    comparison_overall: float,
    compare_role: str,
    reference_scope: str,
    mode: str,
    min_minutes: int,
    is_gk: bool,
    groups: list[dict[str, Any]],
) -> bytes:
    width = 1800
    panel_w = 820
    gap = 48
    x1 = 80
    x2 = x1 + panel_w + gap

    col_heights = [0, 0]
    for i, group in enumerate(groups):
        col_heights[i % 2] += 72 + len(group.get("rows", [])) * 32 + 26

    content_h = max(col_heights) + 470
    height = max(1100, content_h + 90)

    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    # Background gradient-ish overlays.
    draw.ellipse((-420, -300, 900, 760), fill="#092129")
    draw.ellipse((820, -360, 2100, 760), fill="#21143C")
    draw.rectangle((0, 0, width, height), outline=None)

    # Title.
    _text(draw, (80, 70), "PLAYER COMPARISON", F_TITLE, TEXT)
    subtitle = f"{'GOALKEEPERS' if is_gk else 'OUTFIELD'} · {compare_role} · {reference_scope} · {mode} · min {min_minutes} minutes"
    _text(draw, (82, 130), subtitle, F_BODY, MUTED)

    # Hero.
    hero_y = 185
    _round_rect(draw, (80, hero_y, width - 80, hero_y + 245), 26, "#111833", outline="#24485A", width=2)
    _draw_player_block(draw, 120, hero_y + 45, 660, selected_player, selected_overall, "left", is_gk)
    _score_ring(draw, width // 2, hero_y + 122, 50, "VS")
    # overwrite ring inner text for VS
    draw.ellipse((width//2 - 45, hero_y + 122 - 45, width//2 + 45, hero_y + 122 + 45), fill="#0A1024", outline="#24485A", width=2)
    _text(draw, (width//2, hero_y + 122), "VS", F_BODY_B, CYAN, anchor="mm")
    _draw_player_block(draw, width - 120 - 660, hero_y + 45, 660, comparison_player, comparison_overall, "right", is_gk)

    # Context.
    _text(draw, (80, hero_y + 300), "METRIC FAMILIES", F_H1, TEXT)

    # Group panels.
    y_positions = [hero_y + 355, hero_y + 355]
    for idx, group in enumerate(groups):
        col = idx % 2
        x = x1 if col == 0 else x2
        ph = _group_panel(draw, x, y_positions[col], panel_w, group)
        y_positions[col] += ph + 26

    bio = BytesIO()
    img.save(bio, format="PNG", optimize=True)
    return bio.getvalue()
