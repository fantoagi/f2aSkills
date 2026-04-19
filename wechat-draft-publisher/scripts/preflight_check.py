#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
import urllib.request
from pathlib import Path
from typing import Dict, List, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
sys.path.insert(0, str(SCRIPT_DIR))

from auth_manager import resolve_credentials

IMG_MD = re.compile(r'!\[[^\]]*\]\(([^)]+)\)')
IMG_HTML = re.compile(r'<img[^>]+src=["\']([^"\']+)["\']', re.IGNORECASE)


def resolve_wenyan_command() -> str:
    return shutil.which("wenyan") or shutil.which("wenyan.cmd") or ""


def parse_frontmatter(text: str) -> Tuple[Dict[str, str], str]:
    if not text.startswith("---\n"):
        return {}, text
    end = text.find("\n---\n", 4)
    if end == -1:
        return {}, text
    block = text[4:end]
    body = text[end + 5:]
    data: Dict[str, str] = {}
    for line in block.splitlines():
        if not line.strip() or line.strip().startswith("#") or ":" not in line:
            continue
        key, value = line.split(":", 1)
        data[key.strip()] = value.strip()
    return data, body


def collect_images(body: str) -> List[str]:
    images = IMG_MD.findall(body)
    images.extend(IMG_HTML.findall(body))
    return images


def is_remote(path: str) -> bool:
    return path.startswith("http://") or path.startswith("https://")


def resolve_local(path_value: str, base_dir: Path) -> Path:
    candidate = Path(path_value)
    if candidate.is_absolute():
        return candidate
    return (base_dir / candidate).resolve()


def check_remote(url: str) -> bool:
    try:
        request = urllib.request.Request(url, method="HEAD")
        with urllib.request.urlopen(request, timeout=10) as resp:
            return 200 <= getattr(resp, "status", 200) < 400
    except Exception:
        return False


def run_preflight(markdown_file: Path, env_file: Path | None = None, app_id: str | None = None, app_secret: str | None = None) -> Dict[str, object]:
    report: Dict[str, object] = {
        "ok": False,
        "mode": "local_only",
        "checks": [],
        "errors": [],
        "warnings": [],
        "article": {},
    }

    wenyan_command = resolve_wenyan_command()
    if not wenyan_command:
        report["errors"].append("wenyan CLI is not installed. Run: npm install -g @wenyan-md/cli")
    else:
        report["checks"].append(f"wenyan CLI found: {Path(wenyan_command).name}")

    if not markdown_file.exists() or not markdown_file.is_file():
        report["errors"].append(f"Markdown file not found: {markdown_file}")
        return report

    text = markdown_file.read_text(encoding="utf-8")
    frontmatter, body = parse_frontmatter(text)
    title = frontmatter.get("title", "")
    cover = frontmatter.get("cover", "")
    images = collect_images(body)

    creds = resolve_credentials(app_id=app_id, app_secret=app_secret, env_file=env_file)
    if not creds["app_id"] or not creds["app_secret"]:
        report["warnings"].append("WeChat credentials not configured; publish is unavailable but local validation and preview still work")
    else:
        report["checks"].append("WeChat credentials resolved")
        report["mode"] = "publish_ready"

    if not title:
        report["errors"].append("Frontmatter title is required")
    else:
        report["checks"].append("Frontmatter title found")

    if not cover and not images:
        report["errors"].append("A cover or at least one body image is required")

    missing_local_images: List[str] = []
    unreachable_remote_images: List[str] = []
    for image in ([cover] if cover else []) + images:
        if not image:
            continue
        if is_remote(image):
            if not check_remote(image):
                unreachable_remote_images.append(image)
        else:
            resolved = resolve_local(image, markdown_file.parent)
            if not resolved.exists():
                missing_local_images.append(f"{image} -> {resolved}")

    if missing_local_images:
        report["errors"].append("Broken local image paths detected")
        report["missing_local_images"] = missing_local_images
    if unreachable_remote_images:
        report["warnings"].append("Some remote images may be unreachable during publish")
        report["unreachable_remote_images"] = unreachable_remote_images

    report["warnings"].append("Ensure current public IP is in WeChat Official Account IP whitelist")
    report["article"] = {
        "path": str(markdown_file),
        "title": title,
        "cover": cover,
        "body_image_count": len(images),
    }
    report["ok"] = len(report["errors"]) == 0
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Preflight validator for wechat-draft-publisher")
    parser.add_argument("--file", required=True)
    parser.add_argument("--env-file")
    parser.add_argument("--app-id")
    parser.add_argument("--app-secret")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report = run_preflight(
        Path(args.file).resolve(),
        Path(args.env_file).resolve() if args.env_file else None,
        args.app_id,
        args.app_secret,
    )

    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False, indent=2))

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
