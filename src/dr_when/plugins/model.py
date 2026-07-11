"""Current model display name / id."""

from __future__ import annotations

NAME = "model"


def render(ctx: dict, config: dict) -> str | None:
    m = ctx.get("model") or {}
    if not m:
        return None
    fmt = config.get("format", "{display_name}")
    try:
        return fmt.format(
            display_name=m.get("display_name", m.get("id", "?")),
            id=m.get("id", "?"),
        )
    except KeyError:
        return m.get("display_name") or m.get("id")
