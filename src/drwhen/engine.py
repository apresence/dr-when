"""Plugin discovery + rendering engine."""

from __future__ import annotations

import importlib
import importlib.util
import os
import sys
from pathlib import Path
from typing import Any, Callable

# Plugin contract: module must expose
#   NAME: str
#   def render(ctx: dict, config: dict) -> str | None
# Returning None => skipped (e.g. budget plugin not configured).

BUILTIN_NAMES = [
    "time_plugin",
    "context",
    "model",
    "cost",
    "effort",
    "session",
    "wakeup",
    "budget_oauth",
    "budget_api",
]


def _load_builtin(modname: str):
    return importlib.import_module(f"drwhen.plugins.{modname}")


def _load_external(path: Path):
    spec = importlib.util.spec_from_file_location(
        f"drwhen_ext_{path.stem}", str(path)
    )
    if spec is None or spec.loader is None:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    return mod


def discover_plugins(extra_dirs: list[Path] | None = None) -> dict[str, Any]:
    """Discover plugins by NAME. External dirs override builtins."""
    plugins: dict[str, Any] = {}
    for name in BUILTIN_NAMES:
        try:
            mod = _load_builtin(name)
        except ImportError:
            continue
        pname = getattr(mod, "NAME", None)
        if pname and callable(getattr(mod, "render", None)):
            plugins[pname] = mod

    dirs = list(extra_dirs or [])
    # Also support XDG external plugin dir
    xdg = os.environ.get("XDG_CONFIG_HOME")
    xdg_dir = Path(xdg).expanduser() if xdg else Path.home() / ".config"
    dirs.append(xdg_dir / "drwhen" / "plugins")

    for d in dirs:
        if not d.exists() or not d.is_dir():
            continue
        for f in sorted(d.glob("*.py")):
            if f.name.startswith("_"):
                continue
            try:
                mod = _load_external(f)
            except Exception:
                continue
            if mod is None:
                continue
            pname = getattr(mod, "NAME", None)
            if pname and callable(getattr(mod, "render", None)):
                plugins[pname] = mod
    return plugins


def render_line(
    ctx: dict,
    config: dict,
    extra_plugin_dirs: list[Path] | None = None,
) -> str:
    plugins = discover_plugins(extra_plugin_dirs)
    order = config.get("plugins") or []
    separator = config.get("separator", " | ")
    on_error = config.get("on_error", "mark")
    plugin_config = config.get("plugin_config", {}) or {}

    parts: list[str] = []
    for name in order:
        mod = plugins.get(name)
        if mod is None:
            if on_error == "mark":
                parts.append(f"[{name}:missing]")
            continue
        cfg = plugin_config.get(name, {}) or {}
        try:
            result = mod.render(ctx, cfg)
        except Exception as exc:  # never let a plugin break the bar
            if on_error == "mark":
                parts.append(f"[{name}:err]")
            continue
        if result is None or result == "":
            continue
        parts.append(str(result))
    return separator.join(parts)
