"""Install/uninstall drwhen into Claude Code's settings.json."""

from __future__ import annotations

import json
import os
import shutil
import sys
import time
from pathlib import Path

DEFAULT_SETTINGS_PATH = Path.home() / ".claude" / "settings.json"
STATUSLINE_KEY = "statusLine"
MARKER = "drwhen"  # presence in command string => owned by us


def settings_path(override: str | None = None) -> Path:
    if override:
        return Path(override).expanduser()
    env = os.environ.get("DRWHEN_SETTINGS_PATH")
    if env:
        return Path(env).expanduser()
    return DEFAULT_SETTINGS_PATH


def _load(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f) or {}
    except (OSError, json.JSONDecodeError):
        return {}


def _atomic_write(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + f".tmp.{os.getpid()}")
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2)
        f.write("\n")
    os.replace(tmp, path)


def _backup(path: Path) -> Path | None:
    if not path.exists():
        return None
    ts = time.strftime("%Y%m%d-%H%M%S")
    bak = path.with_suffix(path.suffix + f".drwhen.bak.{ts}")
    shutil.copy2(path, bak)
    return bak


def _resolve_drwhen_command() -> str:
    # Prefer the installed entry point if on PATH, else python -m dr_when.cli
    found = shutil.which("drwhen")
    if found:
        return f"{found} render"
    # Fall back to python -m form (works from source checkout)
    py = sys.executable or "python3"
    return f"{py} -m dr_when.cli render"


def plan_install(path: Path, command: str | None = None) -> dict:
    """Return the settings dict that would be written by install()."""
    data = _load(path)
    cmd = command or _resolve_drwhen_command()
    data[STATUSLINE_KEY] = {
        "type": "command",
        "command": cmd,
        "padding": 0,
    }
    return data


def install(
    path: Path | None = None,
    *,
    command: str | None = None,
    dry_run: bool = False,
) -> dict:
    """Install drwhen as the statusLine. Returns a result dict."""
    p = path if path is not None else settings_path()
    new_data = plan_install(p, command)
    result = {
        "path": str(p),
        "dry_run": dry_run,
        "statusLine": new_data[STATUSLINE_KEY],
        "backup": None,
    }
    if dry_run:
        return result
    bak = _backup(p)
    if bak is not None:
        result["backup"] = str(bak)
    _atomic_write(p, new_data)
    return result


def plan_uninstall(path: Path) -> dict:
    data = _load(path)
    current = data.get(STATUSLINE_KEY)
    owned = (
        isinstance(current, dict)
        and isinstance(current.get("command"), str)
        and MARKER in current["command"]
    )
    if owned:
        data.pop(STATUSLINE_KEY, None)
    return data


def uninstall(
    path: Path | None = None,
    *,
    dry_run: bool = False,
) -> dict:
    p = path if path is not None else settings_path()
    new_data = plan_uninstall(p)
    result = {
        "path": str(p),
        "dry_run": dry_run,
        "removed": STATUSLINE_KEY not in new_data,
    }
    if dry_run:
        return result
    bak = _backup(p)
    if bak is not None:
        result["backup"] = str(bak)
    _atomic_write(p, new_data)
    return result
