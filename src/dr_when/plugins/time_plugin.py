"""Current time. Configurable strftime + timezone.

Module is named time_plugin to avoid shadowing stdlib `time`.
"""

from __future__ import annotations

from datetime import datetime, timezone, timedelta

NAME = "time"


def _tz_from_name(name: str):
    if not name or name.upper() == "UTC":
        return timezone.utc
    try:
        from zoneinfo import ZoneInfo  # py3.9+
        return ZoneInfo(name)
    except Exception:
        return timezone.utc


def render(ctx: dict, config: dict) -> str | None:
    fmt = config.get("format", "%Y-%m-%dT%H:%M:%S")
    tzname = config.get("tz", "UTC")
    with_weekday = config.get("with_weekday", False)
    tz = _tz_from_name(tzname)
    now = datetime.now(tz)
    s = now.strftime(fmt)
    if with_weekday:
        s += " " + now.strftime("%A")
    return s
