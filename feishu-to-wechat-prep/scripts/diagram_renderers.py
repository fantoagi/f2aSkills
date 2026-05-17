from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import re
import base64
import os
import subprocess
import sys
import tempfile
import urllib.error
import urllib.request
import zlib
from typing import List, Tuple, Optional

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


def _kroki_svg(code: str) -> Optional[bytes]:
    """Send Mermaid code to Kroki API and return raw SVG bytes, or None."""
    code = re.sub(
        r'^(\s*)subgraph (.+)',
        lambda m: f'{m.group(1)}subgraph "{m.group(2)}"' if not m.group(2).startswith('"') else m.group(0),
        code, flags=re.MULTILINE,
    )
    def _quote_label(m):
        inner = m.group(1)
        if '(' in inner or ')' in inner:
            if inner.startswith('"') and inner.endswith('"'):
                return m.group(0)
            return f'["{inner}"]'
        return m.group(0)
    code = re.sub(r'\[([^\]]+)\]', _quote_label, code)

    cobj = zlib.compressobj(level=9, wbits=zlib.MAX_WBITS)
    compressed = cobj.compress(code.encode('utf-8')) + cobj.flush()
    b64 = base64.urlsafe_b64encode(compressed).decode('ascii').rstrip('=')

    url = f'https://kroki.io/mermaid/svg/{b64}'
    try:
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=30) as r:
            return r.read()
    except (urllib.error.URLError, OSError, ValueError) as e:
        print(f"  [WARN] Kroki API failed: {e}", file=sys.stderr)
        return None


def _svg_to_png_via_chrome(svg_bytes: bytes, output_path: Path) -> bool:
    """Convert SVG bytes to PNG via Chrome headless screenshot.

    Handles <foreignObject> text that cairosvg cannot render.
    Falls back to saving raw SVG if Chrome is unavailable or fails.
    """
    svg_text = svg_bytes.decode("utf-8")

    # Extract viewBox for sizing
    vb_match = re.search(r'viewBox="([^"]+)"', svg_text)
    if vb_match:
        parts = vb_match.group(1).split()
        svg_w, svg_h = int(float(parts[2])), int(float(parts[3]))
    else:
        svg_w, svg_h = 1200, 800

    # Wrap SVG in HTML with fixed dimensions
    html = (
        '<!DOCTYPE html>\n'
        '<html><head><meta charset="utf-8"><style>\n'
        f'  * {{ margin: 0; padding: 0; }}\n'
        f'  body {{ background: white; width: {svg_w}px; height: {svg_h}px; overflow: hidden; }}\n'
        f'  svg {{ width: {svg_w}px; height: {svg_h}px; }}\n'
        '</style></head><body>\n'
        f'{svg_text}\n'
        '</body></html>'
    )

    # Find Chrome
    chrome_candidates = [
        os.environ.get("CHROME_PATH", ""),
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    chrome = next((p for p in chrome_candidates if p and os.path.isfile(p)), None)
    if not chrome:
        # No Chrome — save as SVG instead
        output_path.write_bytes(svg_bytes)
        return True

    try:
        with tempfile.TemporaryDirectory() as tmp:
            html_path = Path(tmp) / "diagram.html"
            html_path.write_text(html, encoding="utf-8")
            url = html_path.resolve().as_uri()

            # Chrome headless screenshot
            screenshot = Path(tmp) / "screenshot.png"
            subprocess.run(
                [chrome, "--headless", "--disable-gpu",
                 f"--window-size={svg_w + 40},{svg_h + 140}",
                 f"--screenshot={screenshot}",
                 "--default-background-color=ffffffff",
                 "--virtual-time-budget=8000",
                 url],
                capture_output=True, text=True, timeout=30,
            )

            if not screenshot.exists() or screenshot.stat().st_size < 500:
                raise RuntimeError("Screenshot too small or missing")

            # Fast content-aware crop using PIL built-ins
            img = Image.open(str(screenshot)).convert("RGB")
            gray = img.convert("L")
            mask = gray.point(lambda x: 255 if x < 235 else 0)
            bbox = mask.getbbox()
            if bbox:
                pad = 2
                x1 = max(0, bbox[0] - pad)
                y1 = max(0, bbox[1] - pad)
                x2 = min(img.width, bbox[2] + pad)
                y2 = min(img.height, bbox[3] + pad)
                img = img.crop((x1, y1, x2, y2))

            img.save(str(output_path), "PNG")
            return True

    except Exception as e:
        print(f"  [WARN] Chrome PNG conversion failed: {e}, falling back to SVG", file=sys.stderr)
        output_path.write_bytes(svg_bytes)
        return True  # saved as SVG fallback


def render_mermaid_diagram(code: str, output_path: Path) -> bool:
    """Render Mermaid code to PNG (preferred) or SVG.

    Pipeline: Kroki API → SVG → Chrome headless → PNG (with text).
    Falls back to SVG if Chrome is unavailable.

    Returns True on success, False on failure.
    """
    svg_data = _kroki_svg(code)
    if svg_data is None:
        return False
    return _svg_to_png_via_chrome(svg_data, output_path)
