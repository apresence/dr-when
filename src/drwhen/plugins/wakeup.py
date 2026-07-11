"""Next scheduled wakeup pulse (from a JSON file written by Cortex)."""

from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path

NAME = "wakeup"


def render(ctx: dict, config: dict) -> str | None:
    src = config.get("source", "~/.claude/wakeups.json")
    p = Path(os.path.expanduser(src))
    if not p.exists():
        return None
    try:
        with open(p, "r") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    # Accept either {"next": <iso8601>} or a list of {"fire_at": iso, ...}.
    candidates: list[str] = []
    if isinstance(data, dict):
        if "next" in data and isinstance(data["next"], str):
            candidates.append(data["next"])
        if "wakes" in data and isinstance(data["wakes"], list):
            for w in data["wakes"]:
                if isinstance(w, dict) and isinstance(w.get("fire_at"), str):
                    candidates.append(w["fire_at"])
    elif isinstance(data, list):
        for w in data:
            if isinstance(w, dict) and isinstance(w.get("fire_at"), str):
                candidates.append(w["fire_at"])

    if not candidates:
        return None

    now = datetime.now(timezone.utc)
    soonest = None
    for s in candidates:
        try:
            dt = datetime.fromisoformat(s.replace("Z", "+00:00"))
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
        except ValueError:
            continue
        if dt < now:
            continue
        if soonest is None or dt < soonest:
            soonest = dt

    if soonest is None:
        return None
    delta = soonest - now
    secs = int(delta.total_seconds())
    if secs < 60:
        rel = f"{secs}s"
    elif secs < 3600:
        rel = f"{secs // 60}m"
    elif secs < 86400:
        rel = f"{secs // 3600}h{(secs % 3600) // 60:02d}m"
    else:
        rel = f"{secs // 86400}d{(secs % 86400) // 3600}h"
    fmt = config.get("format", "wake:{rel}")
    return fmt.format(rel=rel)
