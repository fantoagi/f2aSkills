#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
LAST_PREVIEW = DATA_DIR / "last_preview.html"

from style_settings import resolve_style_settings


def resolve_wenyan_command() -> str:
    return shutil.which("wenyan") or shutil.which("wenyan.cmd") or ""


def run_preview(markdown_file: Path, theme: str | None, highlight: str | None) -> dict:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    wenyan_command = resolve_wenyan_command()
    if not wenyan_command:
        raise RuntimeError("wenyan CLI is not installed. Run: npm install -g @wenyan-md/cli")

    style = resolve_style_settings(theme_override=theme, highlight_override=highlight)
    command = [
        wenyan_command, "render",
        "-f", str(markdown_file),
        "-t", style["theme"],
        "-h", style["highlight"],
    ]
    result = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if result.returncode != 0:
        raise RuntimeError(result.stderr.strip() or result.stdout.strip() or "wenyan render failed")

    LAST_PREVIEW.write_text(result.stdout, encoding="utf-8")
    return {
        "ok": True,
        "preview_path": str(LAST_PREVIEW),
        "bytes": LAST_PREVIEW.stat().st_size,
        "theme": style["theme"],
        "highlight": style["highlight"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Render WeChat preview HTML without publishing")
    parser.add_argument("--file", required=True)
    parser.add_argument("--theme")
    parser.add_argument("--highlight")
    args = parser.parse_args()

    payload = run_preview(Path(args.file).resolve(), args.theme, args.highlight)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
