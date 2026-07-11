"""Claude.ai (Max plan) OAuth budget — STUB.

Real implementation model: burnbar/burnbar/oauth.py + api_client.py
(/global/crew/projects/current/burnbar).

It would:
  1. Read ~/.claude/.credentials.json (Claude Code OAuth tokens).
  2. Refresh via https://platform.claude.com/v1/oauth/token if expired
     (CLIENT_ID 9d1c250a-e61b-44d9-88ed-5944d1962f5e).
  3. Make a minimal POST to /v1/messages with the access token.
  4. Parse anthropic-ratelimit-unified-{5h,7d,7d_sonnet}-{status,reset,...}
     response headers into UnifiedUsageInfo.
  5. CACHE the result (TTL configurable, default 60s) at
     ~/.cache/drwhen/budget_oauth.json — statusLine fires on every turn,
     we must NOT hit the API per call.

Status today: returns the cached value if a cache file exists and is
fresh; otherwise None (skipped). Cache writing is the API caller's job
and not implemented here yet.
"""

from __future__ import annotations

import json
import os
import time
from pathlib import Path

NAME = "budget_oauth"


def render(ctx: dict, config: dict) -> str | None:
    cache_path = config.get("cache_path", "~/.cache/drwhen/budget_oauth.json")
    ttl = int(config.get("cache_ttl_sec", 60))
    p = Path(os.path.expanduser(cache_path))
    if not p.exists():
        return None
    try:
        st = p.stat()
        if time.time() - st.st_mtime > ttl:
            # Cache stale but still better than nothing — show with star
            stale = True
        else:
            stale = False
        with open(p, "r") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None

    pct = data.get("remaining_percentage")
    if pct is None:
        return None
    label = "max"
    suffix = "*" if stale else ""
    return f"{label}:{int(pct)}%{suffix}"
