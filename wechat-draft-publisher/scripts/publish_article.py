#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
RUNS_DIR = DATA_DIR / "runs"
LAST_SUCCESS = DATA_DIR / "last_success.json"

sys.path.insert(0, str(SCRIPT_DIR))

from auth_manager import resolve_credentials
from preflight_check import run_preflight
from style_settings import resolve_style_settings


def slugify(value: str) -> str:
    value = re.sub(r"[^a-zA-Z0-9\u4e00-\u9fff]+", "-", value).strip("-")
    return value[:60] or "article"


def normalize_error(text: str) -> str:
    lowered = text.lower()
    if "ip" in lowered and "whitelist" in lowered:
        return text + "\nHint: add the current machine IP to the WeChat Official Account whitelist."
    if "appid" in lowered or "secret" in lowered:
        return text + "\nHint: recheck WECHAT_APP_ID and WECHAT_APP_SECRET."
    if "封面" in text or "cover" in lowered:
        return text + "\nHint: provide frontmatter cover or at least one body image."
    return text


def save_run(payload: Dict[str, object], run_path: Path) -> None:
    RUNS_DIR.mkdir(parents=True, exist_ok=True)
    run_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def resolve_wenyan_command() -> str:
    return shutil.which("wenyan") or shutil.which("wenyan.cmd") or ""


def publish(markdown_file: Path, theme: str | None, highlight: str | None, env_file: Path | None, app_id: str | None, skip_preflight: bool) -> Dict[str, object]:
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RUNS_DIR.mkdir(parents=True, exist_ok=True)

    style = resolve_style_settings(theme_override=theme, highlight_override=highlight)
    timestamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    title_hint = markdown_file.stem
    run_id = f"{timestamp}-{slugify(title_hint)}"
    run_path = RUNS_DIR / f"{run_id}.json"

    payload: Dict[str, object] = {
        "run_id": run_id,
        "started_at": dt.datetime.now().isoformat(),
        "file": str(markdown_file),
        "theme": style["theme"],
        "highlight": style["highlight"],
        "draft_only": True,
        "ok": False,
    }

    wenyan_command = resolve_wenyan_command()
    if not wenyan_command:
        payload["error"] = "wenyan CLI is not installed. Run: npm install -g @wenyan-md/cli"
        save_run(payload, run_path)
        return payload

    creds = resolve_credentials(app_id=app_id, env_file=env_file)
    if not creds["app_id"] or not creds["app_secret"]:
        payload["error"] = "Missing WECHAT_APP_ID or WECHAT_APP_SECRET"
        save_run(payload, run_path)
        return payload

    if not skip_preflight:
        preflight = run_preflight(markdown_file, env_file=env_file, app_id=creds["app_id"], app_secret=creds["app_secret"])
        payload["preflight"] = preflight
        if not preflight["ok"]:
            payload["error"] = "Preflight failed"
            save_run(payload, run_path)
            return payload

    env = os.environ.copy()
    env["WECHAT_APP_ID"] = creds["app_id"]
    env["WECHAT_APP_SECRET"] = creds["app_secret"]

    command = [
        wenyan_command, "publish",
        "-f", str(markdown_file),
        "-t", style["theme"],
        "-h", style["highlight"],
    ]
    if app_id:
        command.extend(["--app-id", app_id])
    if env_file:
        command.extend(["--env-file", str(env_file)])

    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    payload["command"] = command
    payload["stdout"] = result.stdout
    payload["stderr"] = result.stderr
    payload["returncode"] = result.returncode
    payload["finished_at"] = dt.datetime.now().isoformat()

    output = (result.stdout or "") + "\n" + (result.stderr or "")
    media_match = re.search(r"Media ID[:：]\s*([A-Za-z0-9_\-]+)", output)
    if result.returncode == 0:
        payload["ok"] = True
        payload["media_id"] = media_match.group(1) if media_match else ""
        save_run(payload, run_path)
        LAST_SUCCESS.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
        return payload

    payload["error"] = normalize_error((result.stderr or result.stdout or "wenyan publish failed").strip())
    save_run(payload, run_path)
    return payload


def main() -> int:
    parser = argparse.ArgumentParser(description="Publish Markdown to WeChat Official Account draft box")
    parser.add_argument("--file", required=True)
    parser.add_argument("--theme")
    parser.add_argument("--highlight")
    parser.add_argument("--env-file")
    parser.add_argument("--app-id")
    parser.add_argument("--skip-preflight", action="store_true")
    args = parser.parse_args()

    payload = publish(
        Path(args.file).resolve(),
        args.theme,
        args.highlight,
        Path(args.env_file).resolve() if args.env_file else None,
        args.app_id,
        args.skip_preflight,
    )
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
