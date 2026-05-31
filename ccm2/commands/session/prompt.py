import os
from pathlib import Path
from typing import Optional

import typer
import yaml

from ccm2.commands.session import session_app
from ccm2.lib import aliases, claude_session
from ccm2.lib.colors import blue, cyan, green, red, yellow
from ccm2.lib.exec import run_interactive
from ccm2.lib.flags import FlagErrors, FlagPriority, check_enum, flag_string

_PROMPT_FILE = "prompt.md"
_TEMPLATES_DIR = Path(".claude") / "prompt-templates"
_PERMISSION_MODES = ("default", "acceptEdits", "plan", "bypassPermissions")


class PromptOptions:
    """Holds validated inputs for the session prompt command."""

    target: str
    template: str
    run: bool


def _build(options: PromptOptions, target: Optional[str], template: str, run: bool) -> None:
    flag_errs = FlagErrors()
    if run:
        if target:
            flag_errs.append(f"{green('--run')} cannot be combined with a target argument")
        if template:
            flag_errs.append(f"{green('--run')} cannot be combined with {green('--template')}")
    else:
        if not target:
            flag_errs.append(
                "provide a session alias or ID, e.g. "
                f"{green('ccm2 session prompt <alias> -t <template>')}"
            )
        if not template:
            flag_errs.append(f"{green('--template')} is required when scaffolding a prompt")
    if err := flag_errs.error():
        raise typer.BadParameter(str(err))
    options.target = target or ""
    options.template = template
    options.run = run


def _run(options: PromptOptions) -> None:
    if options.run:
        _run_prompt_file()
    else:
        _scaffold(options.target, options.template)


def _scaffold(target: str, template: str) -> None:
    """Copy a template into the current folder as prompt.md, pre-filling frontmatter."""
    templates_dir = Path.cwd() / _TEMPLATES_DIR
    name = template[:-3] if template.endswith(".md") else template
    template_path = templates_dir / f"{name}.md"

    if not template_path.exists():
        msg = f"template {green(name)} not found at {template_path}"
        if templates_dir.exists():
            available = sorted(p.stem for p in templates_dir.glob("*.md"))
            if available:
                msg += f"\nAvailable templates: {green(', '.join(available))}"
        typer.echo(red(msg), err=True)
        raise typer.Exit(1)

    dest = Path.cwd() / _PROMPT_FILE
    if dest.exists():
        typer.echo(
            red(
                f"{_PROMPT_FILE} already exists in this folder. Edit and run it with "
                f"{green('ccm2 session prompt --run')}, or remove it first."
            ),
            err=True,
        )
        raise typer.Exit(1)

    frontmatter = (
        "---\n"
        f"target: {target}\n"
        "model: sonnet\n"
        "permission-mode: acceptEdits\n"
        "skip-permissions: false\n"
        "force: false\n"
        "---\n\n"
    )
    dest.write_text(frontmatter + template_path.read_text())

    typer.echo(green(f"Created {dest}"))
    typer.echo(f"  {blue('Template:')} {name}")
    typer.echo(f"  {blue('Target:')}   {target}")
    typer.echo(f"\n  1. Edit {cyan(_PROMPT_FILE)} — set the frontmatter and write your prompt.")
    typer.echo(f"  2. Run it with: {cyan('ccm2 session prompt --run')}")


def _run_prompt_file() -> None:
    """Parse prompt.md in the current folder, run it, then delete it."""
    path = Path.cwd() / _PROMPT_FILE
    if not path.exists():
        typer.echo(
            red(
                f"No {_PROMPT_FILE} found in this folder. Scaffold one with "
                f"{green('ccm2 session prompt <alias> -t <template>')}."
            ),
            err=True,
        )
        raise typer.Exit(1)

    meta, body = _parse_prompt_file(path)

    target = str(meta.get("target", "") or "").strip()
    if not target:
        typer.echo(red(f"{_PROMPT_FILE} frontmatter is missing {green('target')}."), err=True)
        raise typer.Exit(1)

    prompt_text = body.strip()
    if not prompt_text:
        typer.echo(red(f"{_PROMPT_FILE} has no prompt body below the frontmatter."), err=True)
        raise typer.Exit(1)

    model = str(meta.get("model", "") or "").strip()
    permission_mode = str(meta.get("permission-mode", "") or "").strip()
    skip_permissions = bool(meta.get("skip-permissions", False))
    force = bool(meta.get("force", False))

    if permission_mode:
        err = check_enum("permission-mode", permission_mode, list(_PERMISSION_MODES))
        if err:
            typer.echo(red(err), err=True)
            raise typer.Exit(1)

    # Pre-flight (resolve + busy-guard) may exit without invoking claude; in that
    # case prompt.md is preserved so the user doesn't lose their written prompt.
    # Once claude is invoked, the prompt has been sent, so we delete prompt.md.
    rc = _execute(target, prompt_text, model, permission_mode, skip_permissions, force)

    try:
        path.unlink()
        typer.echo(yellow(f"\nRemoved {_PROMPT_FILE}."))
    except OSError as exc:
        typer.echo(yellow(f"\nCould not remove {_PROMPT_FILE}: {exc}"))

    if rc != 0:
        raise typer.Exit(rc)


def _parse_prompt_file(path: Path) -> tuple[dict, str]:
    """Split a prompt.md into (frontmatter dict, body string)."""
    text = path.read_text()
    if not text.lstrip().startswith("---"):
        typer.echo(
            red(f"{_PROMPT_FILE} must start with a {green('---')} YAML frontmatter block."),
            err=True,
        )
        raise typer.Exit(1)

    # ['', <frontmatter>, <body>] for a file shaped like "---\n...\n---\nbody".
    parts = text.split("---", 2)
    if len(parts) < 3:
        typer.echo(
            red(f"{_PROMPT_FILE} frontmatter is not closed with a {green('---')} line."),
            err=True,
        )
        raise typer.Exit(1)

    try:
        meta = yaml.safe_load(parts[1]) or {}
    except yaml.YAMLError as exc:
        typer.echo(red(f"Could not parse {_PROMPT_FILE} frontmatter: {exc}"), err=True)
        raise typer.Exit(1) from exc

    if not isinstance(meta, dict):
        meta = {}
    return meta, parts[2]


def _execute(
    target: str,
    prompt_text: str,
    model: str,
    permission_mode: str,
    skip_permissions: bool,
    force: bool,
) -> int:
    """Resolve the target session and run the prompt headlessly via the claude CLI."""
    session_id = target
    cwd = ""

    alias_entry = aliases.resolve(target)
    if alias_entry:
        session_id = alias_entry["sessionId"]
        cwd = alias_entry.get("cwd", "")

    try:
        live = claude_session.list_live_sessions()
        session = claude_session.find_by_session_id(live, session_id)
        if session:
            if not cwd:
                cwd = session.get("cwd", "")
            if session.get("status") == "busy" and not force:
                typer.echo(
                    red(
                        f"Session {cyan(session_id)} is currently busy (running in another "
                        f"tab); prompting it now risks transcript conflicts.\n"
                        f"Set {green('force: true')} in the frontmatter to override."
                    ),
                    err=True,
                )
                raise typer.Exit(1)
    except RuntimeError as exc:
        typer.echo(yellow(f"Warning: couldn't check live sessions ({exc}); skipping busy-check."))

    if not cwd:
        cwd = os.getcwd()

    if claude_session.conversation_exists(cwd, session_id):
        typer.echo(yellow(f"Prompting session {session_id} ...\n"))
        args = ["--resume", session_id, "-p", prompt_text]
    else:
        typer.echo(yellow(f"Starting session {session_id} (first prompt) ...\n"))
        args = ["--session-id", session_id, "-p", prompt_text]

    if model:
        args += ["--model", model]
    if skip_permissions:
        args.append("--dangerously-skip-permissions")
    elif permission_mode:
        args += ["--permission-mode", permission_mode]

    return run_interactive("claude", *args, cwd=cwd, close_stdin=True)


@session_app.command("prompt")
def prompt(
    target: Optional[str] = typer.Argument(
        None,
        metavar="ALIAS_OR_ID",
        help="Session alias or raw session ID (scaffold mode)",
    ),
    template: str = typer.Option(
        "",
        "--template",
        "-t",
        help=flag_string(
            FlagPriority.CONDITIONAL,
            "Template from .claude/prompt-templates/ to scaffold into prompt.md",
        ),
    ),
    run: bool = typer.Option(
        False,
        "--run",
        help=flag_string(FlagPriority.CONDITIONAL, "Run prompt.md in the current folder, then delete it"),
    ),
) -> None:
    """Scaffold a prompt from a template, or run prompt.md against a session.

    Scaffold:  ccm2 session prompt <alias-or-id> -t <template_name>
    Run:       ccm2 session prompt --run
    """
    options = PromptOptions()
    _build(options, target, template, run)
    _run(options)
