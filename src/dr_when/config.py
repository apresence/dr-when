"""Config loading for drwhen.

Lookup order:
  1. $DRWHEN_CONFIG (explicit override)
  2. $XDG_CONFIG_HOME/drwhen/config.json
  3. ~/.config/drwhen/config.json

A missing config file is fine — defaults are used.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DEFAULT_CONFIG: dict[str, Any] = {
    "separator": " | ",
    "plugins": ["context", "cost", "model", "effort", "session", "time"],
    "on_error": "mark",  # "mark" => "[name:error]", "omit" => skip
    "plugin_config": {
        "time": {
            "format": "%Y-%m-%dT%H:%M:%S",
            "tz": "America/New_York",
            "with_weekday": True,
        },
        "context": {
            "show": "used",  # "used" | "left" | "both"
            "format_used": "{pct}% used",
            "format_left": "{pct}% left",
            "format_both": "{used}%/{left}%",
        },
        "model": {"format": "{display_name}"},
        "cost": {"format": "${cost:.2f}"},
        "effort": {"format": "{level}"},
        "session": {"length": 6},
        "wakeup": {"source": "~/.claude/wakeups.json"},
        "budget_oauth": {
            "creds_path": "~/.claude/.credentials.json",
            "cache_path": "~/.cache/drwhen/budget_oauth.json",
            "cache_ttl_sec": 60,
        },
        "budget_api": {
            "api_key_env": "ANTHROPIC_API_KEY",
            "cache_path": "~/.cache/drwhen/budget_api.json",
            "cache_ttl_sec": 60,
        },
    },
}


def _candidate_paths() -> list[Path]:
    override = os.environ.get("DRWHEN_CONFIG")
    paths = []
    if override:
        paths.append(Path(override).expanduser())
    xdg = os.environ.get("XDG_CONFIG_HOME")
    if xdg:
        paths.append(Path(xdg).expanduser() / "drwhen" / "config.json")
    paths.append(Path.home() / ".config" / "drwhen" / "config.json")
    return paths


def config_path() -> Path:
    """Return the active config path (may not exist)."""
    for p in _candidate_paths():
        if p.exists():
            return p
    return _candidate_paths()[-1]


def _deep_merge(base: dict, override: dict) -> dict:
    out = dict(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_config(path: Path | None = None) -> dict[str, Any]:
    """Load config, falling back to defaults. Merges over DEFAULT_CONFIG."""
    if path is None:
        for p in _candidate_paths():
            if p.exists():
                path = p
                break
    if path is None or not path.exists():
        return json.loads(json.dumps(DEFAULT_CONFIG))  # deep copy
    try:
        with open(path, "r") as f:
            user = json.load(f)
    except (OSError, json.JSONDecodeError):
        return json.loads(json.dumps(DEFAULT_CONFIG))
    return _deep_merge(DEFAULT_CONFIG, user)
