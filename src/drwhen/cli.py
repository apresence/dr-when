"""drwhen CLI entry point."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import __version__
from .config import config_path, load_config, DEFAULT_CONFIG
from .engine import discover_plugins, render_line
from .install import install, uninstall, plan_install, plan_uninstall, settings_path


def _cmd_render(args) -> int:
    cfg = load_config(Path(args.config).expanduser() if args.config else None)
    try:
        if args.stdin:
            ctx = json.load(sys.stdin)
        else:
            ctx = {}
    except json.JSONDecodeError:
        ctx = {}
    line = render_line(ctx, cfg)
    print(line)
    return 0


def _cmd_list_plugins(args) -> int:
    plugins = discover_plugins()
    cfg = load_config()
    enabled = set(cfg.get("plugins") or [])
    for name, mod in sorted(plugins.items()):
        flag = "*" if name in enabled else " "
        doc = (mod.__doc__ or "").strip().splitlines()[0] if mod.__doc__ else ""
        print(f"{flag} {name:<16} {doc}")
    return 0


def _cmd_show_config(args) -> int:
    p = Path(args.config).expanduser() if args.config else config_path()
    cfg = load_config(p)
    print(f"# active path: {p}  (exists={p.exists()})")
    print(json.dumps(cfg, indent=2))
    return 0


def _cmd_install(args) -> int:
    sp = Path(args.settings).expanduser() if args.settings else settings_path()
    if args.dry_run:
        new_data = plan_install(sp, args.command)
        out = {
            "path": str(sp),
            "dry_run": True,
            "would_write_statusLine": new_data["statusLine"],
        }
        print(json.dumps(out, indent=2))
        return 0
    result = install(sp, command=args.command, dry_run=False)
    print(json.dumps(result, indent=2))
    return 0


def _cmd_uninstall(args) -> int:
    sp = Path(args.settings).expanduser() if args.settings else settings_path()
    if args.dry_run:
        # Determine whether we own the current statusLine
        from .install import _load, MARKER, STATUSLINE_KEY
        before = _load(sp)
        cur = before.get(STATUSLINE_KEY)
        owned = (
            isinstance(cur, dict)
            and isinstance(cur.get("command"), str)
            and MARKER in cur["command"]
        )
        out = {
            "path": str(sp),
            "dry_run": True,
            "would_remove_statusLine": owned,
            "current_statusLine": cur,
        }
        print(json.dumps(out, indent=2))
        return 0
    result = uninstall(sp, dry_run=False)
    print(json.dumps(result, indent=2))
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="drwhen",
        description="Dr. When — pluggable Claude Code status-line renderer.",
    )
    p.add_argument("--version", action="version", version=f"drwhen {__version__}")
    sub = p.add_subparsers(dest="cmd", required=True)

    pr = sub.add_parser("render", help="Render the status line from stdin JSON.")
    pr.add_argument("--config", help="Path to drwhen config.json.")
    pr.add_argument(
        "--no-stdin",
        dest="stdin",
        action="store_false",
        help="Don't read stdin (use empty ctx).",
    )
    pr.set_defaults(stdin=True, func=_cmd_render)

    pl = sub.add_parser("list-plugins", help="List discovered plugins.")
    pl.set_defaults(func=_cmd_list_plugins)

    pc = sub.add_parser("show-config", help="Print effective config.")
    pc.add_argument("--config", help="Path to drwhen config.json.")
    pc.set_defaults(func=_cmd_show_config)

    pi = sub.add_parser("install", help="Install drwhen into settings.json.")
    pi.add_argument("--settings", help="Override path to settings.json.")
    pi.add_argument("--command", help="Override the statusLine command string.")
    pi.add_argument("--dry-run", action="store_true", help="Show plan, don't write.")
    pi.set_defaults(func=_cmd_install)

    pu = sub.add_parser("uninstall", help="Remove drwhen from settings.json.")
    pu.add_argument("--settings", help="Override path to settings.json.")
    pu.add_argument("--dry-run", action="store_true", help="Show plan, don't write.")
    pu.set_defaults(func=_cmd_uninstall)

    return p


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
