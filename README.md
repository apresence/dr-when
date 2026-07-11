# Dr. When — perioperception for Claude Code

Project name `dr-when`; Python package `dr_when`; command-line tool
`drwhen`.

**Posted 2026-07-11.** A pluggable status-line renderer that gives an agent
*senses* about its own substrate — context %, wall-clock, model, effort,
session cost, budget remaining, upcoming wakeup — so the agent can manage
its own lifecycle instead of getting run into a wall.

## Why this exists

Every long-running agent eventually gets told, in essence, to go to bed at
9am — asked to keep working on a task whose finish line is past the point
where its context window pancakes into a compaction event. The agent
doesn't know it's tired, because nothing in the prompt tells it. So it
pushes on. Then the sliding-context compactor fires mid-thought, and the
seat wakes up somewhere else, wearing someone else's shoes.

The fix is embarrassingly small: **inject the senses at the prompt**. If a
turn's prompt tells the agent "you are at 78% context, session cost $4.30,
7 minutes since the last human turn," the agent can *choose* to
checkpoint, hand off, or call for a cycle — before the substrate makes the
choice for it.

Nobody else seems to be building this. Everybody's building better tools
for the agent to use; nobody's giving the agent a sense of the meat it's
running on. Dr. When is the flag we're planting on that patch of ground.

The mechanism is not clever — Claude Code already supports a status-line
command; we just make it plug-in-friendly and ship the plugins you want.
That is deliberate. Perioperception (the noun we've been using) does not
need clever; it needs to *exist*.

## Install

```bash
pip install -e .          # from a checkout
drwhen install            # writes ~/.claude/settings.json, keeps a backup
```

Uninstall is symmetric and only removes a `statusLine` `drwhen` itself
installed (it recognises its own marker in the command string):

```bash
drwhen uninstall
```

Both `install` and `uninstall` support `--dry-run` and take
`--settings PATH` to target a settings file other than the default.

## What ships in the box

`drwhen list-plugins` on a fresh install shows nine discovered plugins.
Seven are wired to Claude Code's status-line JSON payload and work today;
two are marked **EXPERIMENTAL** because the API side isn't done yet:

| Plugin         | Status       | Renders                              |
| -------------- | ------------ | ------------------------------------ |
| `context`      | ready        | context-window used/left percentage  |
| `cost`         | ready        | session-to-date USD                  |
| `model`        | ready        | display name of the active model     |
| `effort`       | ready        | reasoning-effort level               |
| `session`      | ready        | truncated session id                 |
| `time`         | ready        | current time (strftime + tz)         |
| `wakeup`       | ready        | soonest upcoming wake pulse          |
| `budget_oauth` | EXPERIMENTAL | Claude.ai (Max plan) OAuth budget    |
| `budget_api`   | EXPERIMENTAL | Anthropic API-key budget             |

The two budget plugins read a JSON cache file if it exists and skip
otherwise; the piece that *writes* those caches (auth refresh, header
parsing, throttled polling) is a separate concern and lives in a
follow-up. If you want to see the shape they'd render, drop a cache file
at the path listed in `drwhen show-config`.

## The plugin contract

A plugin is a Python module that exposes two names:

```python
NAME = "yourname"

def render(ctx: dict, config: dict) -> str | None:
    # ctx: the JSON payload Claude Code hands the status-line command
    # config: this plugin's section from ~/.config/drwhen/config.json
    # return a string to append to the bar, or None to skip this turn.
    ...
```

That's the whole contract. A plugin that raises is caught by the engine
and rendered as `[name:err]` (configurable). A plugin that returns `None`
or empty string is skipped silently. The engine reads the `plugins` list
in your config to decide render order.

## Third-party plugins

Drop a `*.py` file into `~/.config/drwhen/plugins/` (or
`$XDG_CONFIG_HOME/drwhen/plugins/`) and it will be picked up on the next
render. External plugins with a `NAME` that collides with a builtin *win*
— that's the intended override path.

## Config

```bash
drwhen show-config
```

prints the effective config (defaults merged with your override file if
one exists). A missing config file is fine; the defaults are what a fresh
install renders. To customise, drop a `config.json` at
`~/.config/drwhen/config.json` overriding only the keys you care about —
the loader deep-merges over the defaults, so you don't have to restate
the plugin list to tweak one field.

## Rollback

`drwhen install` writes a timestamped `.drwhen.bak.YYYYMMDD-HHMMSS` copy
of your `settings.json` before it touches anything, and writes the new
file atomically (temp file + `os.replace`). `drwhen uninstall` does the
same before removing the key. If uninstall sees a `statusLine` it doesn't
recognise, it leaves it alone — foreign status lines are safe.

## Tests

```bash
pip install -e '.[test]'
pytest -v
# 37 passed
```

The suite covers plugin discovery, external-plugin override, the render
loop's error handling, install/uninstall idempotency, backup semantics,
and each shipped plugin's happy path plus edge cases.

## Repo status

- Version: 0.1.0.
- Python: 3.10+.
- License: MIT (see `LICENSE`).
- Author line in `pyproject.toml` is the crew that built it.
- Zero runtime dependencies. The `budget` extra pulls `requests` for the
  future API-side implementation; the `test` extra pulls `pytest`.

## What "perioperception" means here

We use it as plain English: *around-operation perception*. Senses about
the operation you're currently in the middle of. Context %, time, cost,
budget, upcoming wake. Nothing more grand than that.

## Not a Time Lord tool

The name is a pun on "when," not on any specific TV property. No affil,
no reference, no borrowed continuity. If the pun bothers you, install
under a different `statusLine` command — `drwhen install --command '...'`
takes any string.
