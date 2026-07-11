"""Per-plugin smoke tests."""

import json
import time
from pathlib import Path

import pytest

from drwhen.plugins import (
    time_plugin, context, model, cost, effort, session,
    wakeup, budget_oauth, budget_api,
)


def test_time_plugin_utc():
    out = time_plugin.render({}, {"format": "%Y", "tz": "UTC"})
    assert out.isdigit()
    assert 2020 <= int(out) <= 2100


def test_time_plugin_with_weekday():
    out = time_plugin.render({}, {"format": "%H", "tz": "UTC", "with_weekday": True})
    assert " " in out


def test_context_used():
    out = context.render(
        {"context_window": {"used_percentage": 42, "remaining_percentage": 58}}, {}
    )
    assert out == "42% used"


def test_context_left():
    out = context.render(
        {"context_window": {"used_percentage": 42, "remaining_percentage": 58}},
        {"show": "left"},
    )
    assert out == "58% left"


def test_context_both():
    out = context.render(
        {"context_window": {"used_percentage": 42, "remaining_percentage": 58}},
        {"show": "both"},
    )
    assert out == "42%/58%"


def test_context_derives_missing():
    out = context.render({"context_window": {"used_percentage": 30}}, {"show": "left"})
    assert out == "70% left"


def test_context_no_data():
    assert context.render({}, {}) is None


def test_model_default():
    out = model.render({"model": {"id": "x", "display_name": "X-Display"}}, {})
    assert out == "X-Display"


def test_model_missing():
    assert model.render({}, {}) is None


def test_cost():
    assert cost.render({"cost": {"total_cost_usd": 1.234}}, {}) == "$1.23"


def test_cost_missing():
    assert cost.render({}, {}) is None


def test_effort():
    assert effort.render({"effort": {"level": "high"}}, {}) == "high"


def test_session_trim():
    out = session.render({"session_id": "abcdef-1234567890"}, {"length": 4})
    assert out == "7890"


def test_wakeup_future(tmp_path):
    p = tmp_path / "wakeups.json"
    from datetime import datetime, timezone, timedelta
    fire = (datetime.now(timezone.utc) + timedelta(minutes=42)).isoformat()
    p.write_text(json.dumps({"next": fire}))
    out = wakeup.render({}, {"source": str(p)})
    assert out is not None
    assert "wake:" in out


def test_wakeup_no_file(tmp_path):
    assert wakeup.render({}, {"source": str(tmp_path / "missing.json")}) is None


def test_wakeup_past_ignored(tmp_path):
    p = tmp_path / "wakeups.json"
    p.write_text(json.dumps({"next": "2000-01-01T00:00:00+00:00"}))
    assert wakeup.render({}, {"source": str(p)}) is None


def test_budget_oauth_no_cache(tmp_path):
    cfg = {"cache_path": str(tmp_path / "nope.json"), "cache_ttl_sec": 60}
    assert budget_oauth.render({}, cfg) is None


def test_budget_oauth_with_cache(tmp_path):
    p = tmp_path / "cache.json"
    p.write_text(json.dumps({"remaining_percentage": 73}))
    cfg = {"cache_path": str(p), "cache_ttl_sec": 60}
    out = budget_oauth.render({}, cfg)
    assert out == "max:73%"


def test_budget_oauth_stale(tmp_path):
    p = tmp_path / "cache.json"
    p.write_text(json.dumps({"remaining_percentage": 50}))
    # Make file old
    old = time.time() - 3600
    import os
    os.utime(p, (old, old))
    cfg = {"cache_path": str(p), "cache_ttl_sec": 60}
    out = budget_oauth.render({}, cfg)
    assert out is not None and out.endswith("*")


def test_budget_api_no_cache(tmp_path):
    cfg = {"cache_path": str(tmp_path / "nope.json"), "cache_ttl_sec": 60}
    assert budget_api.render({}, cfg) is None


def test_budget_api_with_cache(tmp_path):
    p = tmp_path / "cache.json"
    p.write_text(json.dumps({"percentage": 85}))
    cfg = {"cache_path": str(p), "cache_ttl_sec": 60}
    out = budget_api.render({}, cfg)
    assert out == "api:85%"


def test_budget_api_derives_pct(tmp_path):
    p = tmp_path / "cache.json"
    p.write_text(json.dumps({"tokens_remaining": 300, "tokens_limit": 1000}))
    cfg = {"cache_path": str(p), "cache_ttl_sec": 60}
    out = budget_api.render({}, cfg)
    assert out == "api:30%"
