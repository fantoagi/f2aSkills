#!/usr/bin/env python3
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict

SCRIPT_DIR = Path(__file__).resolve().parent
SKILL_DIR = SCRIPT_DIR.parent
DATA_DIR = SKILL_DIR / "data"
SETTINGS_FILE = DATA_DIR / "settings.json"

DEFAULT_STYLE_SETTINGS = {
    "theme": "lapis",
    "highlight": "solarized-light",
}


def ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_style_settings() -> Dict[str, str]:
    settings = DEFAULT_STYLE_SETTINGS.copy()
    if not SETTINGS_FILE.exists():
        return settings

    try:
        payload = json.loads(SETTINGS_FILE.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return settings

    for key in ("theme", "highlight"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            settings[key] = value.strip()
    return settings


def save_style_settings(theme: str | None = None, highlight: str | None = None) -> Dict[str, str]:
    settings = load_style_settings()
    if theme:
        settings["theme"] = theme
    if highlight:
        settings["highlight"] = highlight
    ensure_data_dir()
    SETTINGS_FILE.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")
    return settings


def clear_style_settings() -> Dict[str, str]:
    if SETTINGS_FILE.exists():
        SETTINGS_FILE.unlink()
    return DEFAULT_STYLE_SETTINGS.copy()


def resolve_style_settings(theme_override: str | None = None, highlight_override: str | None = None) -> Dict[str, str]:
    settings = load_style_settings()
    if theme_override:
        settings["theme"] = theme_override
    if highlight_override:
        settings["highlight"] = highlight_override
    return settings
