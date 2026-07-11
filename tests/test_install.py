"""Install / uninstall tests."""

import json
from pathlib import Path

import pytest

from drwhen import install as install_mod


def _read(p: Path) -> dict:
    with open(p, "r") as f:
        return json.load(f)


def test_install_into_empty(tmp_path: Path):
    p = tmp_path / "settings.json"
    res = install_mod.install(p, command="drwhen render")
    assert res["dry_run"] is False
    assert res["backup"] is None  # no existing file -> no backup
    data = _read(p)
    assert data["statusLine"]["command"] == "drwhen render"
    assert data["statusLine"]["type"] == "command"


def test_install_preserves_other_keys(tmp_path: Path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({
        "env": {"X": "1"},
        "permissions": {"allow": ["Bash"]},
        "statusLine": {"type": "command", "command": "old"},
    }))
    res = install_mod.install(p, command="drwhen render")
    assert res["backup"] is not None
    data = _read(p)
    assert data["env"] == {"X": "1"}
    assert data["permissions"] == {"allow": ["Bash"]}
    assert "drwhen" in data["statusLine"]["command"]


def test_dry_run_does_not_write(tmp_path: Path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"keep": "me"}))
    res = install_mod.install(p, command="drwhen render", dry_run=True)
    assert res["dry_run"] is True
    data = _read(p)
    assert data == {"keep": "me"}  # untouched


def test_uninstall_drwhen_only(tmp_path: Path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({
        "env": {"Y": "2"},
        "statusLine": {"type": "command", "command": "drwhen render"},
    }))
    res = install_mod.uninstall(p)
    assert res["removed"] is True
    data = _read(p)
    assert "statusLine" not in data
    assert data["env"] == {"Y": "2"}


def test_uninstall_leaves_foreign_statusline(tmp_path: Path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({
        "statusLine": {"type": "command", "command": "python3 /home/x/cc-hook.py"},
    }))
    res = install_mod.uninstall(p)
    assert res["removed"] is False
    data = _read(p)
    assert data["statusLine"]["command"] == "python3 /home/x/cc-hook.py"


def test_install_is_idempotent(tmp_path: Path):
    p = tmp_path / "settings.json"
    install_mod.install(p, command="drwhen render")
    first = _read(p)
    install_mod.install(p, command="drwhen render")
    second = _read(p)
    assert first["statusLine"] == second["statusLine"]


def test_plan_install_no_write(tmp_path: Path):
    p = tmp_path / "settings.json"
    p.write_text(json.dumps({"a": 1}))
    plan = install_mod.plan_install(p, "drwhen render")
    assert plan["statusLine"]["command"] == "drwhen render"
    # file must still equal pre-plan content
    assert _read(p) == {"a": 1}
