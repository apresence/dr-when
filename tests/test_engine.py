"""Engine + plugin discovery tests."""

import json
from pathlib import Path

import pytest

from dr_when.engine import discover_plugins, render_line
from dr_when.config import DEFAULT_CONFIG


SAMPLE_CTX = {
    "session_id": "abcdef-1234567890",
    "model": {"id": "claude-opus-4-6", "display_name": "Opus 4.6"},
    "effort": {"level": "medium"},
    "cost": {"total_cost_usd": 0.42},
    "context_window": {
        "used_percentage": 13,
        "remaining_percentage": 87,
        "context_window_size": 200000,
    },
}


def test_discover_finds_builtins():
    plugins = discover_plugins()
    for name in ("time", "context", "model", "cost", "effort", "session"):
        assert name in plugins, f"missing builtin {name}"


def test_render_minimal_line():
    cfg = {
        "separator": " | ",
        "plugins": ["context", "cost", "model", "effort", "session"],
        "plugin_config": {},
    }
    line = render_line(SAMPLE_CTX, cfg)
    assert "13% used" in line
    assert "$0.42" in line
    assert "Opus 4.6" in line
    assert "medium" in line
    assert line.endswith("567890")  # last 6 of session id


def test_render_with_time_in_utc():
    cfg = {
        "separator": " | ",
        "plugins": ["context", "time"],
        "plugin_config": {
            "time": {"format": "%Y", "tz": "UTC", "with_weekday": False},
        },
    }
    line = render_line(SAMPLE_CTX, cfg)
    assert "13% used" in line
    # The year should be a 4-digit number
    parts = line.split(" | ")
    assert parts[-1].isdigit() and len(parts[-1]) == 4


def test_missing_plugin_marked():
    cfg = {
        "separator": " | ",
        "plugins": ["context", "doesnotexist"],
        "on_error": "mark",
        "plugin_config": {},
    }
    line = render_line(SAMPLE_CTX, cfg)
    assert "[doesnotexist:missing]" in line


def test_missing_plugin_omitted():
    cfg = {
        "separator": " | ",
        "plugins": ["context", "doesnotexist"],
        "on_error": "omit",
        "plugin_config": {},
    }
    line = render_line(SAMPLE_CTX, cfg)
    assert "doesnotexist" not in line


def test_plugin_returns_none_skipped():
    # context plugin with no ctx_window -> None -> omitted
    cfg = {
        "separator": " | ",
        "plugins": ["context", "model"],
        "plugin_config": {},
    }
    line = render_line({"model": {"display_name": "X"}}, cfg)
    assert line == "X"


def test_external_plugin_discovery(tmp_path: Path):
    ext = tmp_path / "myplug.py"
    ext.write_text(
        "NAME = 'myplug'\n"
        "def render(ctx, config):\n"
        "    return 'HELLO-' + (ctx.get('session_id') or 'none')[:4]\n"
    )
    cfg = {
        "separator": " | ",
        "plugins": ["myplug"],
        "plugin_config": {},
    }
    line = render_line({"session_id": "xyzwzz"}, cfg, extra_plugin_dirs=[tmp_path])
    assert line == "HELLO-xyzw"


def test_plugin_exception_doesnt_crash(tmp_path: Path):
    ext = tmp_path / "boom.py"
    ext.write_text(
        "NAME = 'boom'\n"
        "def render(ctx, config):\n"
        "    raise RuntimeError('nope')\n"
    )
    cfg = {
        "separator": " | ",
        "plugins": ["boom", "model"],
        "on_error": "mark",
        "plugin_config": {},
    }
    line = render_line(SAMPLE_CTX, cfg, extra_plugin_dirs=[tmp_path])
    assert "[boom:err]" in line
    assert "Opus 4.6" in line
