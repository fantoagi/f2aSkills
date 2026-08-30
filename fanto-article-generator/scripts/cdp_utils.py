"""Shared Chrome DevTools Protocol helpers for local article scripts."""

import json
import os
import shutil
import subprocess
import tempfile
import time
import urllib.request


CDP_HOSTS = ("[::1]", "127.0.0.1", "localhost")
CDP_PROBE_TIMEOUT = 0.25


def find_chrome():
    """Find a usable Chrome/Chromium executable."""
    env_chrome = os.environ.get("CHROME_PATH")
    if env_chrome and os.path.exists(env_chrome):
        return env_chrome

    candidates = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "google-chrome",
        "chromium",
        "chromium-browser",
    ]
    for path in candidates:
        if os.path.exists(path):
            return path

    for name in ["google-chrome", "chromium", "chromium-browser"]:
        try:
            result = subprocess.run(["which", name], capture_output=True, text=True)
            if result.returncode == 0 and result.stdout.strip():
                return result.stdout.strip()
        except Exception:
            pass
    return None


def cdp_is_running(host="[::1]", port=9222):
    """Check if Chrome DevTools Protocol is available on a host/port pair."""
    try:
        with urllib.request.urlopen(
            f"http://{host}:{port}/json/version",
            timeout=CDP_PROBE_TIMEOUT,
        ):
            return True
    except Exception:
        return False


def detect_cdp_host(port=9222):
    """Return the first reachable CDP host, preferring IPv6 then IPv4."""
    for host in CDP_HOSTS:
        if cdp_is_running(host, port):
            return host
    return None


def start_chrome(chrome_path, port=9222, window_size="1280,800"):
    """Start Chrome in headless CDP mode and wait for either IPv6 or IPv4."""
    user_data_dir = tempfile.mkdtemp(prefix="fanto_cdp_chrome_")
    args = [
        chrome_path,
        f"--remote-debugging-port={port}",
        "--remote-debugging-address=127.0.0.1",
        f"--user-data-dir={user_data_dir}",
        "--headless",
        "--disable-gpu",
        "--no-sandbox",
        "--remote-allow-origins=*",
        f"--window-size={window_size}",
    ]
    try:
        proc = subprocess.Popen(args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        proc._fanto_user_data_dir = user_data_dir
        for _ in range(30):
            time.sleep(0.5)
            if detect_cdp_host(port):
                return proc
        stop_chrome(proc)
        raise RuntimeError("Chrome started but CDP is not responding")
    except Exception:
        shutil.rmtree(user_data_dir, ignore_errors=True)
        raise


def ensure_cdp(port=9222, window_size="1280,800"):
    """Ensure CDP is running; returns (process_started_or_None, reachable_host)."""
    host = detect_cdp_host(port)
    if host:
        return None, host

    chrome = find_chrome()
    if not chrome:
        raise RuntimeError(
            "Cannot find Chrome. Install Chrome or set CHROME_PATH environment variable."
        )

    proc = start_chrome(chrome, port=port, window_size=window_size)
    host = detect_cdp_host(port)
    if host:
        return proc, host

    proc.kill()
    raise RuntimeError("Chrome started but CDP not reachable on any host")


def stop_chrome(proc):
    """Stop a Chrome process started by this module and remove its temp profile."""
    if proc is None:
        return

    user_data_dir = getattr(proc, "_fanto_user_data_dir", None)
    proc.terminate()
    try:
        proc.wait(timeout=5)
    except Exception:
        proc.kill()
        try:
            proc.wait(timeout=5)
        except Exception:
            pass

    if user_data_dir:
        shutil.rmtree(user_data_dir, ignore_errors=True)


class CDP:
    """Small request/response wrapper for a Chrome DevTools WebSocket."""

    def __init__(self, ws_url, timeout=20):
        import websocket

        self.ws = websocket.create_connection(ws_url, timeout=timeout)
        self.next_id = 1

    def call(self, method, params=None, timeout=20):
        call_id = self.next_id
        self.next_id += 1
        self.ws.settimeout(timeout)
        self.ws.send(json.dumps({"id": call_id, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == call_id:
                if "error" in msg:
                    raise RuntimeError(f"CDP {method} failed: {msg['error']}")
                return msg.get("result", {})

    def close(self):
        self.ws.close()
