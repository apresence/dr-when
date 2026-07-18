# Dr. When — perioperception for agents

Project name `dr-when`; Python package `dr_when`; command-line tool
`drwhen`.

A pluggable status-line renderer that surfaces an agent's substrate
state — context %, wall-clock, model, effort, session cost, budget
remaining, upcoming wakeup — where it can be seen and acted on before
the substrate acts first. Today it ships as a Claude Code status-line
tool: the first client of an idea that isn't Claude-specific.

## Why this exists

Every long-running agent eventually gets run past its own limits —
asked to finish a task whose finish line is beyond the point where its
context window auto-compacts. The agent doesn't know it's tired,
because nothing tells it. So it pushes on, compaction fires
mid-thought, and continuity is lost.

The fix is small: **put the senses where they can be seen.** A status
line that reads "78% context, session cost $4.30, next wakeup in 12
minutes" turns lifecycle management from a surprise into a choice —
checkpoint, hand off, or cycle, before the substrate decides for you.

An honest note on the mechanism: Claude Code's status-line hook
renders to the operator's terminal — the agent itself doesn't see it
yet. Getting these senses into the agent's own turn context is the
point of the project; the status line is the first, deliberately
boring step. Perioperception — the word we use for it — doesn't need
clever; it needs to exist.

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
— that's the intended override path. Treat that directory accordingly:
anything in it runs on every render and can replace your gauges.

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

Around-operation perception: senses about the operation you're
currently in the middle of. Context %, time, cost, budget, upcoming
wake. Nothing more grand than that.

## The name

A pun on "when," nothing more. If it bothers you,
`drwhen install --command '...'` takes any string.
