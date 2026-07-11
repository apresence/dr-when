"""Context window utilisation."""

from __future__ import annotations

NAME = "context"


def render(ctx: dict, config: dict) -> str | None:
    cw = ctx.get("context_window") or {}
    used = cw.get("used_percentage")
    left = cw.get("remaining_percentage")
    if used is None and left is None:
        return None
    if used is None and left is not None:
        used = 100 - left
    if left is None and used is not None:
        left = 100 - used

    show = config.get("show", "used")
    if show == "left":
        fmt = config.get("format_left", "{pct}% left")
        return fmt.format(pct=left)
    if show == "both":
        fmt = config.get("format_both", "{used}%/{left}%")
        return fmt.format(used=used, left=left)
    fmt = config.get("format_used", "{pct}% used")
    return fmt.format(pct=used)
