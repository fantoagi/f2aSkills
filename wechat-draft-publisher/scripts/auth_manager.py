#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Optional

from style_settings import SETTINGS_FILE, clear_style_settings, load_style_settings, save_style_settings

SKILL_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = SKILL_DIR / "data"
ENV_FILE = SKILL_DIR / ".env"
ACTIVE_CONFIG = DATA_DIR / "active_config.json"


def ensure_dirs() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def load_env_file(path: Path) -> Dict[str, str]:
    values: Dict[str, str] = {}
    if not path.exists():
        return values
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def save_active_config(app_id: str, app_secret: str, env_file: Optional[Path]) -> None:
    ensure_dirs()
    payload = {
        "app_id": app_id,
        "app_secret": app_secret,
        "source": str(env_file) if env_file else "direct",
    }
    ACTIVE_CONFIG.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_active_config() -> None:
    if ACTIVE_CONFIG.exists():
        ACTIVE_CONFIG.unlink()


def resolve_credentials(app_id: Optional[str] = None, app_secret: Optional[str] = None, env_file: Optional[Path] = None) -> Dict[str, str]:
    file_values: Dict[str, str] = {}
    if env_file:
        file_values.update(load_env_file(env_file))
    if ENV_FILE.exists():
        file_values.update({k: v for k, v in load_env_file(ENV_FILE).items() if k not in file_values})

    resolved_app_id = app_id or os.environ.get("WECHAT_APP_ID") or file_values.get("WECHAT_APP_ID")
    resolved_app_secret = app_secret or os.environ.get("WECHAT_APP_SECRET") or file_values.get("WECHAT_APP_SECRET")

    return {
        "app_id": resolved_app_id or "",
        "app_secret": resolved_app_secret or "",
        "env_file": str(env_file or (ENV_FILE if ENV_FILE.exists() else "")),
    }


def masked(value: str) -> str:
    if not value:
        return ""
    if len(value) <= 8:
        return value[:2] + "***"
    return value[:4] + "***" + value[-4:]


def cmd_status(args: argparse.Namespace) -> int:
    creds = resolve_credentials(env_file=Path(args.env_file) if args.env_file else None)
    payload = {
        "skill_dir": str(SKILL_DIR),
        "env_file_default": str(ENV_FILE),
        "active_config": str(ACTIVE_CONFIG),
        "has_app_id": bool(creds["app_id"]),
        "has_app_secret": bool(creds["app_secret"]),
        "app_id_preview": masked(creds["app_id"]),
        "env_file_used": creds["env_file"],
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if payload["has_app_id"] and payload["has_app_secret"] else 1


def cmd_validate(args: argparse.Namespace) -> int:
    creds = resolve_credentials(env_file=Path(args.env_file) if args.env_file else None)
    if not creds["app_id"] or not creds["app_secret"]:
        print("Missing WECHAT_APP_ID or WECHAT_APP_SECRET")
        print(f"  Put them in: {ENV_FILE}")
        return 1
    print("Credential fields are present")
    print(f"  WECHAT_APP_ID={masked(creds['app_id'])}")
    return 0


def cmd_set_active(args: argparse.Namespace) -> int:
    env_file = Path(args.env_file) if args.env_file else None
    creds = resolve_credentials(args.app_id, args.app_secret, env_file)
    if not creds["app_id"] or not creds["app_secret"]:
        print("Cannot save active config without both app_id and app_secret")
        return 1
    save_active_config(creds["app_id"], creds["app_secret"], env_file)
    print("Active WeChat config saved")
    return 0


def cmd_show_location(_: argparse.Namespace) -> int:
    print(json.dumps({
        "skill_dir": str(SKILL_DIR),
        "default_env_file": str(ENV_FILE),
        "active_config": str(ACTIVE_CONFIG),
        "style_settings": str(SETTINGS_FILE),
    }, ensure_ascii=False, indent=2))
    return 0


def cmd_clear(_: argparse.Namespace) -> int:
    clear_active_config()
    print("Active config cleared")
    return 0


def cmd_style_show(_: argparse.Namespace) -> int:
    payload = load_style_settings()
    payload["settings_file"] = str(SETTINGS_FILE)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_style_set(args: argparse.Namespace) -> int:
    settings = save_style_settings(theme=args.theme, highlight=args.highlight)
    payload = {
        **settings,
        "settings_file": str(SETTINGS_FILE),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def cmd_style_clear(_: argparse.Namespace) -> int:
    settings = clear_style_settings()
    payload = {
        **settings,
        "settings_file": str(SETTINGS_FILE),
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage wechat-draft-publisher credentials and style settings")
    sub = parser.add_subparsers(dest="command")

    status = sub.add_parser("status", help="Show resolved credential status")
    status.add_argument("--env-file")

    validate = sub.add_parser("validate", help="Validate resolved credential presence")
    validate.add_argument("--env-file")

    set_active = sub.add_parser("set-active", help="Persist an active config for this skill")
    set_active.add_argument("--app-id")
    set_active.add_argument("--app-secret")
    set_active.add_argument("--env-file")

    sub.add_parser("show-location", help="Show config file locations")
    sub.add_parser("clear", help="Clear persisted active config")

    sub.add_parser("style-show", help="Show effective style settings")
    style_set = sub.add_parser("style-set", help="Persist default style settings")
    style_set.add_argument("--theme")
    style_set.add_argument("--highlight")
    sub.add_parser("style-clear", help="Clear persisted style settings")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "status":
        return cmd_status(args)
    if args.command == "validate":
        return cmd_validate(args)
    if args.command == "set-active":
        return cmd_set_active(args)
    if args.command == "show-location":
        return cmd_show_location(args)
    if args.command == "clear":
        return cmd_clear(args)
    if args.command == "style-show":
        return cmd_style_show(args)
    if args.command == "style-set":
        return cmd_style_set(args)
    if args.command == "style-clear":
        return cmd_style_clear(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
