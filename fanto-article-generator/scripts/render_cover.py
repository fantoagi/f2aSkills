"""
SVG → PNG cover renderer via CDP browser canvas.

Battle-tested pipeline (Chrome 148+, May 2026):
  file:/// URL → Page.navigate → wait loadEventFired
  → Runtime.evaluate(toDataURL) → decode → save PNG

Depends on: Python stdlib + websocket-client (`pip install websocket-client`).
Chrome must be running with --remote-debugging-port=9222 --remote-allow-origins=*.

Usage:
  python render_cover.py /path/to/cover.svg [/path/to/cover.png] [--keep-chrome]
"""

import argparse
import base64
import json
import os
import sys
import tempfile
import time
import urllib.request

from cdp_utils import ensure_cdp, stop_chrome


def render(svg_path, png_path, keep_chrome=False, port=9222, width=940, height=400):
    """Render SVG to PNG via CDP browser canvas."""
    chrome_proc = None

    # Read SVG
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    svg_data_uri = f"data:image/svg+xml;base64,{svg_b64}"

    # Build render HTML
    html = f"""<!DOCTYPE html>
<html><head><title>LOADING</title></head>
<body style="margin:0;background:#fff;">
<canvas id="c" width="{width}" height="{height}"></canvas>
<script>
var img = new Image();
img.onload = function() {{
  var c = document.getElementById("c");
  c.width = {width};
  c.height = {height};
  var ctx = c.getContext("2d");
  ctx.drawImage(img, 0, 0, {width}, {height});
  document.title = "RENDERED";
}};
img.onerror = function() {{ document.title = "ERR"; }};
img.src = "{svg_data_uri}";
</script></body></html>"""

    # Write HTML to temp file (must be file:// for Chrome to execute inline scripts from data URIs)
    html_fd, html_path = tempfile.mkstemp(suffix=".html", prefix="cover_render_")
    os.close(html_fd)
    with open(html_path, "w", encoding="utf-8") as f:
        f.write(html)

    try:
        # Ensure CDP
        chrome_proc, cdp_host = ensure_cdp(port, window_size="1280,800")
        cdp_base = f"http://{cdp_host}:{port}"

        # Open about:blank tab
        req = urllib.request.Request(
            f"{cdp_base}/json/new?url=about:blank", method="PUT"
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            resp = json.loads(r.read())
        tab_id = resp["id"]
        ws_url = resp["webSocketDebuggerUrl"]

        # Connect WebSocket
        import websocket

        ws = websocket.create_connection(ws_url, timeout=10)

        # Enable Page domain
        ws.send(json.dumps({"id": 1, "method": "Page.enable"}))
        ws.recv()

        # Navigate to file:// URL
        file_url = "file:///" + html_path.replace("\\", "/")
        ws.send(
            json.dumps(
                {"id": 2, "method": "Page.navigate", "params": {"url": file_url}}
            )
        )
        ws.recv()

        # Drain events until loadEventFired, then drain remaining buffered events
        ws.settimeout(2)
        load_done = False
        for _ in range(20):
            try:
                msg = ws.recv()
                if "Page.loadEventFired" in msg:
                    load_done = True
                    # Drain any immediately following events
                    time.sleep(0.3)
                    for __ in range(5):
                        try:
                            ws.recv()
                        except Exception:
                            break
                    break
            except Exception:
                pass

        if not load_done:
            raise RuntimeError("Page load event did not fire within timeout")

        # Poll for RENDERED title
        ws.settimeout(10)
        for i in range(30):
            time.sleep(0.3)
            ws.send(
                json.dumps(
                    {
                        "id": 1000 + i,
                        "method": "Runtime.evaluate",
                        "params": {
                            "expression": "document.title",
                            "returnByValue": True,
                        },
                    }
                )
            )
            resp = json.loads(ws.recv())
            # Drain events that snuck in between
            while "id" not in resp:
                resp = json.loads(ws.recv())
            title = resp["result"]["result"]["value"]
            if title == "RENDERED":
                break
            elif title == "ERR":
                raise RuntimeError("SVG image failed to load (img.onerror fired)")
        else:
            raise RuntimeError(f"SVG render timed out (last title: {repr(title)})")

        # Get canvas PNG data
        ws.send(
            json.dumps(
                {
                    "id": 9999,
                    "method": "Runtime.evaluate",
                    "params": {
                        "expression": 'document.getElementById("c").toDataURL("image/png")',
                        "returnByValue": True,
                    },
                }
            )
        )
        resp = json.loads(ws.recv())
        while "id" not in resp:
            resp = json.loads(ws.recv())

        data_url = resp["result"]["result"]["value"]
        if not data_url or not data_url.startswith("data:image/png;base64,"):
            raise RuntimeError(f"toDataURL returned unexpected value: {str(data_url)[:200]}")

        # Save PNG
        b64_data = data_url.split(",", 1)[1]
        with open(png_path, "wb") as f:
            f.write(base64.b64decode(b64_data))

        # Close tab
        ws.close()
        with urllib.request.urlopen(f"{cdp_base}/json/close/{tab_id}", timeout=5):
            pass

        return os.path.getsize(png_path)

    finally:
        # Clean up temp HTML
        try:
            os.unlink(html_path)
        except OSError:
            pass

        # If this script started Chrome, close it unless the caller wants reuse.
        if chrome_proc is not None and not keep_chrome:
            stop_chrome(chrome_proc)


def main():
    parser = argparse.ArgumentParser(
        description="Render a 2.35:1 SVG cover to PNG through Chrome CDP."
    )
    parser.add_argument("svg_path", help="source SVG path")
    parser.add_argument(
        "png_path",
        nargs="?",
        help="output PNG path; defaults to source path with .png extension",
    )
    parser.add_argument("--port", type=int, default=9222, help="Chrome CDP port")
    parser.add_argument("--width", type=int, default=940, help="output canvas width")
    parser.add_argument("--height", type=int, default=400, help="output canvas height")
    parser.add_argument(
        "--keep-chrome",
        action="store_true",
        help="keep Chrome running if this script starts it",
    )
    args = parser.parse_args()

    svg_path = args.svg_path
    if not os.path.exists(svg_path):
        print(f"Error: SVG file not found: {svg_path}")
        sys.exit(1)

    if args.png_path:
        png_path = args.png_path
    else:
        base = os.path.splitext(svg_path)[0]
        png_path = f"{base}.png"

    try:
        size = render(
            svg_path,
            png_path,
            keep_chrome=args.keep_chrome,
            port=args.port,
            width=args.width,
            height=args.height,
        )
        print(f"Cover rendered: {png_path} ({size:,} bytes)")
    except Exception as e:
        print(f"Render failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
