"""Anthropic API-key budget — STUB.

Real implementation model: burnbar/burnbar/api_client.py
_check_usage_api_key() + _parse_headers().

It would:
  1. Read ANTHROPIC_API_KEY from env (configurable var name).
  2. Call /v1/messages/count_tokens (or minimal /v1/messages) with the key.
  3. Parse anthropic-ratelimit-{tokens,requests}-{remaining,limit,reset}
     response headers into UsageInfo.
  4. CACHE at ~/.cache/drwhen/budget_api.json with configurable TTL
     (default 60s). statusLine fires every turn — never hit the API per
     call.

Status today: returns the cached value if a cache file exists; otherwise
returns None (skipped). Real cache writing is a follow-up task.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

NAME = "budget_api"


def render(ctx: dict, config: dict) -> str | None:
    cache_path = config.get("cache_path", "~/.cache/drwhen/budget_api.json")
    ttl = int(config.get("cache_ttl_sec", 60))
    p = Path(os.path.expanduser(cache_path))
    if not p.exists():
        return None
    try:
        st = p.stat()
        stale = (time.time() - st.st_mtime) > ttl
        with open(p, "r") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    pct = data.get("percentage")
    if pct is None:
        rem = data.get("tokens_remaining")
        lim = data.get("tokens_limit")
        if rem is None or not lim:
            return None
        pct = round(rem * 100.0 / lim)
    suffix = "*" if stale else ""
    return f"api:{int(pct)}%{suffix}"
