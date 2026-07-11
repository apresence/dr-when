"""Thinking-effort level (medium/high/...)."""

from __future__ import annotations

NAME = "effort"


def render(ctx: dict, config: dict) -> str | None:
    e = ctx.get("effort") or {}
    level = e.get("level")
    if not level:
        return None
    fmt = config.get("format", "{level}")
    return fmt.format(level=level)
