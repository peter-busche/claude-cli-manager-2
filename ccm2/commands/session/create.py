import os
import shlex
import uuid
from pathlib import Path
from typing import Optional

import typer

from ccm2.commands.session import session_app
from ccm2.lib import aliases
from ccm2.lib.colors import blue, cyan, green, red, yellow
from ccm2.lib.editor import prompt_via_editor
from ccm2.lib.exec import run_interactive
from ccm2.lib.flags import FlagErrors, FlagPriority, check_mutually_exclusive, flag_string


class CreateOptions:
    """Holds validated inputs for the session create command."""

    sub: bool
    alias: str


def _build(options: CreateOptions, sub: bool, alias: str) -> None:
    flag_errs = FlagErrors()
    flag_errs.append(check_mutually_exclusive({"sub": sub, "alias": alias}))
    if err := flag_errs.error():
        raise typer.BadParameter(str(err))
    options.sub = sub
    options.alias = alias


def _run(options: CreateOptions) -> None:
    if options.sub:
        _create_sub_agent()
    else:
        _create_session(options.alias)


def _create_session(alias: str) -> None:
    cwd = os.getcwd()
    session_id = str(uuid.uuid4())

    if alias:
        try:
            aliases.set_alias(alias, session_id, cwd, _now_ms())
        except ValueError as exc:
            typer.echo(red(str(exc)), err=True)
            raise typer.Exit(1) from exc
        typer.echo(green("Registered headless session (no tab opened)."))
        typer.echo(f"  {blue('Session ID:')} {session_id}")
        typer.echo(f"  {blue('Alias:')}      {alias}")
        typer.echo(f"  Drive it with: {cyan(f'ccm2 session prompt {alias}')}")
        return

    # No alias: try to open an interactive tab; fall back to current terminal.
    launch_cmd = f"cd {shlex.quote(cwd)} && claude --session-id {session_id}"
    script = _new_tab_applescript(launch_cmd)
    if script is None:
        typer.echo(yellow("New terminal tab not supported here; starting in the current tab."))
        typer.echo(f"  {blue('Session ID:')} {session_id}")
        run_interactive("claude", "--session-id", session_id, cwd=cwd)
        return

    import subprocess

    result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
    if result.returncode != 0:
        typer.echo(red(f"Failed to open terminal tab: {result.stderr.strip()}"), err=True)
        raise typer.Exit(1)

    typer.echo(green("Opening a new Claude session in a new terminal tab..."))
    typer.echo(f"  {blue('Session ID:')} {session_id}")


def _create_sub_agent() -> None:
    description = prompt_via_editor(
        "Describe what this agent should do and when it should be used "
        "(be comprehensive for best results).",
        "md",
    )
    if not description:
        typer.echo(red("No description provided."), err=True)
        raise typer.Exit(1)

    cwd = os.getcwd()
    agents_dir = Path(cwd) / ".claude" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)

    typer.echo(yellow("\nGenerating sub-agent with Claude..."))
    rc = run_interactive(
        "claude",
        "-p",
        _build_agent_gen_prompt(description),
        "--dangerously-skip-permissions",
        cwd=cwd,
    )
    if rc != 0:
        typer.echo(red("Failed to generate sub-agent."), err=True)
        raise typer.Exit(rc)

    typer.echo(green("\nDone. Project agents in .claude/agents/:"))
    for entry in sorted(agents_dir.iterdir()):
        if entry.is_file():
            typer.echo(f"  - {entry.name}")


def _new_tab_applescript(shell_cmd: str) -> Optional[str]:
    """Return AppleScript to open a new terminal tab, or None if unsupported."""
    import platform

    if platform.system() != "Darwin":
        return None

    esc = shell_cmd.replace("\\", "\\\\").replace('"', '\\"')

    if os.environ.get("TERM_PROGRAM") == "iTerm.app":
        return (
            'tell application "iTerm"\n'
            "\tactivate\n"
            "\ttell current window\n"
            "\t\tcreate tab with default profile\n"
            f'\t\ttell current session of current tab to write text "{esc}"\n'
            "\tend tell\n"
            "end tell"
        )

    return (
        'tell application "Terminal"\n'
        "\tactivate\n"
        '\ttell application "System Events" to keystroke "t" using command down\n'
        "\tdelay 0.3\n"
        f'\tdo script "{esc}" in front window\n'
        "end tell"
    )


def _build_agent_gen_prompt(description: str) -> str:
    return (
        "Create a new Claude Code subagent for THIS project based on the description below.\n\n"
        "Save it as a single Markdown file at .claude/agents/<name>.md, choosing a short,\n"
        "descriptive kebab-case <name>. The file must begin with YAML frontmatter containing:\n"
        "  - name: the kebab-case name\n"
        "  - description: a clear statement of WHEN this agent should be used\n"
        "  - tools: a sensible comma-separated subset of available tools\n"
        "  - model: an appropriate model (e.g. sonnet, haiku, opus)\n"
        "  - color: a display color\n"
        "Follow the frontmatter with a thorough system prompt for the agent.\n\n"
        "Create only that one file; do not modify anything else.\n\n"
        f"Agent description:\n{description}"
    )


def _now_ms() -> int:
    import time

    return int(time.time() * 1000)


@session_app.command("create")
def create(
    alias: str = typer.Option(
        "",
        "--alias",
        "-a",
        help=flag_string(FlagPriority.OPTIONAL, "Friendly alias for the new session"),
    ),
    sub: bool = typer.Option(
        False,
        "--sub",
        help=flag_string(FlagPriority.OPTIONAL, "Create a sub-agent instead of a new session"),
    ),
) -> None:
    """Create a new Claude session, or a sub-agent with --sub."""
    options = CreateOptions()
    _build(options, sub=sub, alias=alias)
    _run(options)
