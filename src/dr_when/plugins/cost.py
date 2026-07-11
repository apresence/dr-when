"""Session-to-date cost (from CC's cost.total_cost_usd)."""

from __future__ import annotations

NAME = "cost"


def render(ctx: dict, config: dict) -> str | None:
    c = ctx.get("cost") or {}
    if not c:
        return None
    cost = c.get("total_cost_usd")
    if cost is None:
        return None
    fmt = config.get("format", "${cost:.2f}")
    try:
        return fmt.format(cost=cost)
    except (KeyError, ValueError):
        return f"${cost:.2f}"
