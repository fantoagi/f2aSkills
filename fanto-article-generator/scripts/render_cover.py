"""
SVG → PNG cover renderer via CDP browser canvas.

Battle-tested pipeline (Chrome 148+, May 2026):
  file:/// URL → Page.navigate → wait loadEventFired
  → Runtime.evaluate(toDataURL) → decode → save PNG

Depends on: Python stdlib + websocket-client (`pip install websocket-client`).
Chrome must be running with --remote-debugging-port=9222 --remote-allow-origins=*.

Usage:
  python render_cover.py /path/to/cover.svg [/path/to/cover.png]
"""

import json, urllib.request, base64, time, os, sys, tempfile, subprocess, socket


def find_chrome():
    """Find a usable Chrome/Chromium executable."""
    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome", "chromium", "chromium-browser",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    # Try which
    for name in ["google-chrome", "chromium", "chromium-browser"]:
        try:
            result = subprocess.run(["which", name], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    return None


def cdp_is_running(host="[::1]", port=9222):
    """Check if Chrome DevTools Protocol is available."""
    try:
        req = urllib.request.Request(f"http://{host}:{port}/json/version")
        urllib.request.urlopen(req, timeout=3)
        return True
    except Exception:
        return False


def start_chrome(chrome_path, port=9222):
    """Start Chrome in headless CDP mode with required flags."""
    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--remote-allow-origins=*",
        "--window-size=1280,800",
    ]
    proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    # Wait for CDP to become available
    for _ in range(15):
        time.sleep(0.5)
        if cdp_is_running():
            return proc
    proc.kill()
    raise RuntimeError("Chrome started but CDP is not responding")


def ensure_cdp(port=9222):
    """Ensure CDP is running; start Chrome if needed. Returns (process_or_None, host)."""
    # Try IPv6 first (Chrome 148+ default), then IPv4
    for host in ["[::1]", "127.0.0.1"]:
        if cdp_is_running(host, port):
            return None, host

    chrome = find_chrome()
    if not chrome:
        raise RuntimeError(
            "Cannot find Chrome. Install Chrome or set CHROME_PATH environment variable."
        )
    proc = start_chrome(chrome, port)
    # Re-detect which host it bound to
    for host in ["[::1]", "127.0.0.1"]:
        if cdp_is_running(host, port):
            return proc, host
    proc.kill()
    raise RuntimeError("Chrome started but CDP not reachable on any host")


def render(svg_path, png_path):
    """Render SVG to PNG via CDP browser canvas."""

    # Read SVG
    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    svg_b64 = base64.b64encode(svg_content.encode("utf-8")).decode("utf-8")
    svg_data_uri = f"data:image/svg+xml;base64,{svg_b64}"

    # Build render HTML
    html = f"""<!DOCTYPE html>
<html><head><title>LOADING</title></head>
<body style="margin:0;background:#fff;">
<canvas id="c" width="940" height="400"></canvas>
<script>
var img = new Image();
img.onload = function() {{
  var c = document.getElementById("c");
  c.width = 940;
  c.height = 400;
  var ctx = c.getContext("2d");
  ctx.drawImage(img, 0, 0, 940, 400);
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
        chrome_proc, cdp_host = ensure_cdp()
        cdp_base = f"http://{cdp_host}:9222"

        # Open about:blank tab
        req = urllib.request.Request(
            f"{cdp_base}/json/new?url=about:blank", method="PUT"
        )
        resp = json.loads(urllib.request.urlopen(req, timeout=15).read())
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
        urllib.request.urlopen(f"{cdp_base}/json/close/{tab_id}", timeout=5)

        return os.path.getsize(png_path)

    finally:
        # Clean up temp HTML
        try:
            os.unlink(html_path)
        except OSError:
            pass


def main():
    if len(sys.argv) < 2:
        print(f"Usage: python {os.path.basename(__file__)} <cover.svg> [cover.png]")
        sys.exit(1)

    svg_path = sys.argv[1]
    if not os.path.exists(svg_path):
        print(f"Error: SVG file not found: {svg_path}")
        sys.exit(1)

    if len(sys.argv) >= 3:
        png_path = sys.argv[2]
    else:
        base = os.path.splitext(svg_path)[0]
        png_path = f"{base}.png"

    try:
        size = render(svg_path, png_path)
        print(f"Cover rendered: {png_path} ({size:,} bytes)")
    except Exception as e:
        print(f"Render failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
