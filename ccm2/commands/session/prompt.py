import os
from typing import Optional

import typer

from ccm2.commands.session import session_app
from ccm2.lib import aliases
from ccm2.lib import claude_session
from ccm2.lib.colors import cyan, green, red, yellow
from ccm2.lib.editor import prompt_via_editor
from ccm2.lib.exec import run_interactive
from ccm2.lib.flags import FlagPriority, flag_string

_PERMISSION_MODES = ("default", "acceptEdits", "plan", "bypassPermissions")


class PromptOptions:
    """Holds validated inputs for the session prompt command."""

    target: str
    message: str
    model: str
    permission_mode: str
    skip_permissions: bool
    force: bool

    # Resolved at runtime.
    session_id: str
    cwd: str


def _build(
    options: PromptOptions,
    target: str,
    message: str,
    model: str,
    permission_mode: str,
    skip_permissions: bool,
    force: bool,
) -> None:
    if not target:
        raise typer.BadParameter(
            f"provide a session alias or ID: {green('ccm2 session prompt <alias>')}"
        )
    options.target = target
    options.message = message
    options.model = model
    options.permission_mode = permission_mode
    options.skip_permissions = skip_permissions
    options.force = force


def _run(options: PromptOptions) -> None:
    # Resolve alias → session ID + cwd.
    options.session_id = options.target
    options.cwd = ""

    alias_entry = aliases.resolve(options.target)
    if alias_entry:
        options.session_id = alias_entry["sessionId"]
        options.cwd = alias_entry.get("cwd", "")

    # Check live sessions for busy-guard and cwd fallback.
    try:
        live = claude_session.list_live_sessions()
        session = claude_session.find_by_session_id(live, options.session_id)
        if session:
            if not options.cwd:
                options.cwd = session.get("cwd", "")
            if session.get("status") == "busy" and not options.force:
                typer.echo(
                    red(
                        f"Session {cyan(options.session_id)} is currently busy (running in "
                        f"another tab); prompting it now risks transcript conflicts.\n"
                        f"Re-run with {green('--force')} to override."
                    ),
                    err=True,
                )
                raise typer.Exit(1)
    except RuntimeError as exc:
        typer.echo(yellow(f"Warning: couldn't check live sessions ({exc}); skipping busy-check."))

    if not options.cwd:
        options.cwd = os.getcwd()

    # Collect prompt text.
    prompt_text = options.message
    if not prompt_text:
        prompt_text = prompt_via_editor(
            f'Write the prompt to send to session "{options.target}".',
            "md",
        )
    if not prompt_text:
        typer.echo(red("No prompt provided."), err=True)
        raise typer.Exit(1)

    # Build claude args.
    if claude_session.conversation_exists(options.cwd, options.session_id):
        typer.echo(yellow(f"Prompting session {options.session_id} ...\n"))
        args = ["--resume", options.session_id, "-p", prompt_text]
    else:
        typer.echo(yellow(f"Starting session {options.session_id} (first prompt) ...\n"))
        args = ["--session-id", options.session_id, "-p", prompt_text]

    if options.model:
        args += ["--model", options.model]
    if options.skip_permissions:
        args.append("--dangerously-skip-permissions")
    elif options.permission_mode:
        args += ["--permission-mode", options.permission_mode]

    rc = run_interactive("claude", *args, cwd=options.cwd)
    if rc != 0:
        raise typer.Exit(rc)


@session_app.command("prompt")
def prompt(
    target: str = typer.Argument(
        ...,
        help="Session alias or raw session ID",
        metavar="ALIAS_OR_ID",
    ),
    message: str = typer.Option(
        "",
        "--message",
        "-m",
        help=flag_string(FlagPriority.OPTIONAL, "Prompt text (skips the editor)"),
    ),
    model: str = typer.Option(
        "",
        "--model",
        help=flag_string(FlagPriority.OPTIONAL, "Model override (e.g. claude-sonnet-4-5)"),
    ),
    permission_mode: str = typer.Option(
        "acceptEdits",
        "--permission-mode",
        help=flag_string(
            FlagPriority.OPTIONAL,
            "Permission mode for the run",
            "default, acceptEdits, plan, bypassPermissions",
            "acceptEdits",
        ),
    ),
    skip_permissions: bool = typer.Option(
        False,
        "--skip-permissions",
        help=flag_string(
            FlagPriority.OPTIONAL,
            "Run with --dangerously-skip-permissions (full tool access)",
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=flag_string(FlagPriority.OPTIONAL, "Prompt even if the session is busy"),
    ),
) -> None:
    """Send a prompt to a Claude session (by alias or session ID)."""
    options = PromptOptions()
    _build(options, target, message, model, permission_mode, skip_permissions, force)
    _run(options)
