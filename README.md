# claude-cli-manager-2 (`ccm2`)

`claude-cli-manager-2` is a CLI tool for managing your Claude tooling. Commands
follow the format `ccm2 <object> <command> <flags>`. Built with
[Typer](https://typer.tiangolo.com/), backed by [Rich](https://rich.readthedocs.io/)
for colorized output.

## Installation

Requires Python 3.11+.

```bash
git clone https://github.com/peter-busche/claude-cli-manager-2.git
cd claude-cli-manager-2
pip install -e .
```

This installs `ccm2` as a CLI command in your active virtualenv.

```bash
ccm2 --version    # confirms the CLI is on your PATH
```

You can also run it without installing:

```bash
python -m ccm2.main --version
```

## The `~/.config/ccm2/` folder

`ccm2` keeps its per-user, cross-repo state in `~/.config/ccm2/`. Nothing here
is required to exist — every file is created lazily the first time it's
needed, and a missing file or folder is never an error. Two files live there:

### `config.yaml` — your settings

An optional config file, loaded once at startup and merged with environment
variables. Environment variables prefixed with `CCM2_` are overlaid on top of
whatever the file contains (e.g. `CCM2_FOO=bar` sets the `foo` config key to
`bar`, taking precedence over a `foo:` entry in the file). There are no
required keys yet — it's a place to put values as commands begin to need them.

```bash
mkdir -p "$HOME/.config/ccm2"
cat > "$HOME/.config/ccm2/config.yaml" << 'EOF'
# ~/.config/ccm2/config.yaml
# Add configuration values here as commands begin to require them.
EOF
```

### `aliases.json` — your session aliases

A global lookup table mapping friendly alias names to Claude Code sessions,
shared across every repository on your machine. Each entry records the
session ID, the working directory the session was created in, and a
creation timestamp. `ccm2` writes and reads it automatically — you normally
never touch the file directly:

- `ccm2 session create --alias <name>` registers a new headless session
  under `<name>`.
- `ccm2 session prompt <name>` looks the alias up here to find which
  session to drive.
- `ccm2 startup init --execute` aliases the generation session it runs for
  each `CLAUDE.md` it writes, keyed by that folder's path relative to the
  repo root, so you can `ccm2 session prompt <folder/path>` to follow up on
  how a particular `CLAUDE.md` was generated. Re-running `--execute`
  repoints an existing alias at the new session rather than failing.
- `ccm2 startup init` also symlinks `.claude/init/aliases.json` inside the
  target repo to this file, so anyone browsing that repo's `.claude/`
  folder can see which sessions were aliased there without ccm2 having to
  duplicate the data per repo.

Because it's global, alias names must be unique across *all* of your
repositories, not just the current one — `ccm2` will refuse to overwrite an
existing alias that points at a different session unless the command
requesting it explicitly allows overwriting.

## Usage

```bash
ccm2              # prints help
ccm2 --version    # prints the version
ccm2 <object> -h  # help text for an object command
```

### Objects and commands

- **`startup`** — one-time setup commands for onboarding a repository.
  - `ccm2 startup bootstrap` — seed a repository with a portable copy of
    ccm2's `.claude/` framework.
  - `ccm2 startup init` — build a narrowed `CLAUDE.md` hierarchy for a large
    repository (plan mode by default; pass `--execute` to generate).
- **`session`** — commands for inspecting and driving Claude Code sessions.
  - `ccm2 session list` (alias `ls`) — list Claude Code sessions and
    sub-agents for a repository.
  - `ccm2 session create` — create a new Claude session, or a sub-agent with
    `--sub`. Pass `--alias <name>` to register it in the global alias store
    (see [The `~/.config/ccm2/` folder](#the-configccm2-folder)).
  - `ccm2 session prompt` — scaffold a prompt from a template, or run
    `prompt.md` in the current folder against a session headlessly,
    resolving `<name>` through the global alias store.

Run `ccm2 <object> <command> --help` for the full flag reference on any
command.

## Contributing

### Local development

```bash
# Run directly without installing
python -m ccm2.main --version

# Install in editable mode and run the installed entrypoint
pip install -e .
ccm2 --version
```

### Adding commands

Use the generator script to scaffold a new command. It creates the parent
(object) package if needed and registers everything in `ccm2/main.py`:

```bash
python scripts/add_cmd.py [object_name] [action] [action_alias](optional)

# e.g.
python scripts/add_cmd.py session list
python scripts/add_cmd.py session list-sessions list
```

Object names cannot contain dashes (use `session`, not `my-session`).
Reference templates live in `templates/`.

Each leaf command follows an Options-class pattern — see
[`templates/cmd-template.py`](templates/cmd-template.py) and
[`templates/parent-cmd-template.py`](templates/parent-cmd-template.py), and
`CLAUDE.md` for the full convention writeup.

### Versioning

Bump the `VERSION` file (semver) when releasing, and update `version` in
`pyproject.toml` to match. `ccm2 --version` reads `VERSION` at runtime.

## Project layout

```
.
├── ccm2/
│   ├── main.py                 # root Typer app, config loading, sub-app registration
│   ├── commands/
│   │   ├── hello.py            # temporary smoke-test command
│   │   ├── session/            # session create / list / prompt
│   │   └── startup/            # startup bootstrap / init
│   └── lib/                    # shared helpers (colors, flag validation, exec, aliases, ...)
├── scripts/
│   └── add_cmd.py              # command generator
├── templates/                  # reference templates for new commands
└── VERSION                     # semver string, read at runtime for --version
```
