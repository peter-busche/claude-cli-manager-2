# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with
code in this repository.

## Workflow

- **Never use worktrees.** Make all changes directly on the current branch (`main`).
- The user reviews changes locally before pushing.

## Build and Development Commands

- **Install (editable)**: `pip install -e .` — installs `ccm2` as a CLI command in your active virtualenv
- **Run directly**: `python -m ccm2.main` — runs without installing
- **Test install**: `ccm2 --version` — confirms the CLI is on your PATH
- **Install deps only**: `pip install -r requirements.txt` (if present) or `pip install -e .`

## Maintenance Scripts

Scripts live in the `scripts/` directory.

### Adding new commands

```bash
python scripts/add_cmd.py [object_name] [action] [action_alias](optional)
```

Examples:
- `python scripts/add_cmd.py session list`
- `python scripts/add_cmd.py session list-sessions list`

Object names cannot contain dashes (use `session`, not `my-session`).

This script automatically:
- Creates `ccm2/commands/{object_name}/` package if needed
- Generates `__init__.py` with the Typer sub-app
- Generates a leaf command file with the Options pattern
- Registers the sub-app import and `app.add_typer(...)` call in `ccm2/main.py`

## Architecture

### CLI structure

- Built using [Typer](https://typer.tiangolo.com/) backed by [Rich](https://rich.readthedocs.io/) for colorized output.
- Hierarchical commands: `ccm2 <object> <command> <flags>`.
- Each object (e.g. `session`) is its own package under `ccm2/commands/`.
- The root Typer app and config loading live in `ccm2/main.py`.
- The Claude Code Python SDK (`claude-code-sdk`) is included as a dependency for programmatic session/agent management.

### Command pattern

Each leaf command follows an Options-class pattern:

1. **`XOptions` class** — holds validated inputs.
2. **`_build(options)`** — reads flags, validates them (via `ccm2/lib/flags.py` helpers), and populates the object.
3. **`_run(options)`** — the main command logic.
4. **`@{object}_app.command("action")`** — registers the function on its parent Typer sub-app.

See `templates/cmd-template.py` and `templates/parent-cmd-template.py`.

### Registering a new object in `ccm2/main.py`

When `scripts/add_cmd.py` creates a new object, it inserts after the
`# --- OBJECT COMMANDS (add new sub-apps here) ---` marker in `ccm2/main.py`:

```python
from ccm2.commands.session import session_app
app.add_typer(session_app, name="session")
```

Root-level commands (like the temporary `hello`) are registered after the
`# --- ROOT COMMANDS ---` marker.

### Configuration

- Optional config file at `~/.config/ccm2/config.yaml` (a missing file is not an error — see `_load_config` in `ccm2/main.py`).
- Environment variables prefixed with `CCM2_` are overlaid on top of the file config automatically.

### Shared helpers (`ccm2/lib/`)

- `colors.py` — colorized output helpers (`red`, `green`, `cyan`, etc.) built on Rich.
- `flags.py` — flag-validation system: `FlagErrors`, `check_required`, `check_mutually_exclusive`, `check_at_least_one`, `check_enum`, and `flag_string` for consistent, colorized help text (`REQUIRED` / `CONDITIONAL` / `OPTIONAL`).
- `exec.py` — `execute_command` (captured) and `execute_command_live` (streamed).

### Versioning

- Bump the `VERSION` file (semver) when releasing. `ccm2 --version` reads it at runtime.
- Also update `version` in `pyproject.toml` to match.
