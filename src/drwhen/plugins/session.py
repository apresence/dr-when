"""Truncated session id."""

from __future__ import annotations

NAME = "session"


def render(ctx: dict, config: dict) -> str | None:
    sid = ctx.get("session_id")
    if not sid:
        return None
    length = int(config.get("length", 6))
    return sid[-length:]
