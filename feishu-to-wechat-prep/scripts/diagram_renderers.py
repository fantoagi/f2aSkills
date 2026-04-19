from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
from typing import List, Tuple, Optional

# default font fallback path
import os
import sys

def _get_system_font_path() -> Path:
    if sys.platform == "win32":
        return Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts" / "msyh.ttc"
    elif sys.platform == "darwin":
        return Path("/System/Library/Fonts/PingFang.ttc")
    else:
        # Simple fallback for linux
        return Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc")

DEFAULT_FONT_PATH = _get_system_font_path()

def _get_font(size: int, font_path: Optional[str] = None) -> ImageFont.FreeTypeFont:
    path = Path(font_path) if font_path else DEFAULT_FONT_PATH
    try:
        return ImageFont.truetype(str(path), size)
    except IOError:
        # Fallback to default load if not found
        return ImageFont.load_default()

def wrap_text(draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    lines = []
    current = ""
    for ch in text:
        trial = current + ch
        if draw.textbbox((0, 0), trial, font=font)[2] <= max_width:
            current = trial
        else:
            if current:
                lines.append(current)
            current = ch
    if current:
        lines.append(current)
    return lines

def draw_centered_text(draw: ImageDraw.ImageDraw, box: Tuple[int, int, int, int], text: str, font: ImageFont.FreeTypeFont, fill: str = "#1f2937") -> None:
    x1, y1, x2, y2 = box
    max_width = x2 - x1 - 24
    lines = wrap_text(draw, text, font, max_width)
    line_heights = [draw.textbbox((0, 0), line, font=font)[3] for line in lines]
    total_h = sum(line_heights) + (len(lines) - 1) * 8
    y = y1 + ((y2 - y1) - total_h) / 2
    for i, line in enumerate(lines):
        bbox = draw.textbbox((0, 0), line, font=font)
        w = bbox[2] - bbox[0]
        draw.text((x1 + ((x2 - x1) - w) / 2, y), line, font=font, fill=fill)
        y += line_heights[i] + 8

def draw_arrow(draw: ImageDraw.ImageDraw, start: Tuple[float, float], end: Tuple[float, float], fill: str = "#2563eb", width: int = 5) -> None:
    draw.line([start, end], fill=fill, width=width)
    ex, ey = end
    sx, sy = start
    if abs(ex - sx) >= abs(ey - sy):
        direction = 1 if ex > sx else -1
        pts = [(ex, ey), (ex - 16 * direction, ey - 9), (ex - 16 * direction, ey + 9)]
    else:
        direction = 1 if ey > sy else -1
        pts = [(ex, ey), (ex - 9, ey - 16 * direction), (ex + 9, ey - 16 * direction)]
    draw.polygon(pts, fill=fill)

def render_vertical_flow(path: Path, title: str, nodes: List[str], font_path: Optional[str] = None) -> None:
    """Render a vertical step-by-step flow diagram."""
    title_font = _get_font(34, font_path)
    text_font = _get_font(24, font_path)

    # Calculate dynamic height
    box_w, box_h = 320, 88
    gap = 26
    top = 170
    bottom_padding = 60
    h = top + len(nodes) * (box_h + gap) - gap + bottom_padding
    w = 1200

    img = Image.new("RGB", (w, h), "#f8fbff")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((30, 30, w - 30, h - 30), radius=28, outline="#c7d2fe", width=3, fill="#eef4ff")
    draw_centered_text(draw, (80, 60, w - 80, 130), title, title_font, fill="#0f172a")

    x = (w - box_w) / 2
    centers = []
    for i, node in enumerate(nodes):
        y = top + i * (box_h + gap)
        draw.rounded_rectangle((x, y, x + box_w, y + box_h), radius=22, fill="#ffffff", outline="#60a5fa", width=3)
        draw_centered_text(draw, (x + 18, y + 10, x + box_w - 18, y + box_h - 10), node, text_font)
        centers.append((x + box_w / 2, y + box_h / 2))

    for i in range(len(centers) - 1):
        start = (centers[i][0], centers[i][1] + box_h / 2 - 12)
        end = (centers[i + 1][0], centers[i + 1][1] - box_h / 2 + 12)
        draw_arrow(draw, start, end)

    img.save(path)

def render_three_stage_relation(path: Path, title: str, left_title: str, left_desc: str, right_title: str, right_desc: str, center_desc: str, font_path: Optional[str] = None) -> None:
    """Render a left-center-right relationship diagram."""
    title_font = _get_font(34, font_path)
    text_font = _get_font(24, font_path)
    small_font = _get_font(20, font_path)

    w, h = 1200, 700
    img = Image.new("RGB", (w, h), "#f8fbff")
    draw = ImageDraw.Draw(img)
    draw.rounded_rectangle((30, 30, w - 30, h - 30), radius=28, outline="#bfdbfe", width=3, fill="#eff6ff")
    draw_centered_text(draw, (80, 55, w - 80, 115), title, title_font, fill="#0f172a")

    left = (110, 190, 500, 520)
    right = (700, 190, 1090, 520)
    center = (500, 315, 700, 395)

    draw.rounded_rectangle(left, radius=28, fill="#ffffff", outline="#60a5fa", width=3)
    draw.rounded_rectangle(right, radius=28, fill="#ffffff", outline="#34d399", width=3)
    draw.rounded_rectangle(center, radius=22, fill="#dbeafe", outline="#2563eb", width=3)

    draw_centered_text(draw, (left[0] + 24, left[1] + 18, left[2] - 24, left[1] + 88), left_title, title_font, fill="#1d4ed8")
    draw_centered_text(draw, (left[0] + 28, left[1] + 100, left[2] - 28, left[3] - 24), left_desc, text_font)

    draw_centered_text(draw, (right[0] + 24, right[1] + 18, right[2] - 24, right[1] + 88), right_title, title_font, fill="#047857")
    draw_centered_text(draw, (right[0] + 28, right[1] + 100, right[2] - 28, right[3] - 24), right_desc, text_font)

    draw_centered_text(draw, (center[0] + 10, center[1] + 5, center[2] - 10, center[3] - 5), center_desc, text_font, fill="#1e3a8a")

    draw_arrow(draw, (left[2], (left[1] + left[3]) / 2), (center[0], (center[1] + center[3]) / 2), fill="#2563eb")
    draw_arrow(draw, (center[2], (center[1] + center[3]) / 2), (right[0], (right[1] + right[3]) / 2), fill="#10b981")

    img.save(path)
