import json
import subprocess
import time
import uuid
from pathlib import Path

import typer
import yaml

from ccm2.commands.startup import startup_app
from ccm2.lib import aliases
from ccm2.lib.colors import blue, cyan, green, red, white, yellow
from ccm2.lib.exec import run_interactive
from ccm2.lib.flags import FlagErrors, FlagPriority, check_enum, flag_string

_PERMISSION_MODES = ("default", "acceptEdits", "plan", "bypassPermissions")
_PLAN_FILE = Path(".claude") / "init" / "plan.yaml"
_BUNDLED_TEMPLATES = Path(__file__).parent / "templates"

# Bash discovery commands must be pre-approved or the headless run blocks forever
# (stdin is closed, so a permission prompt can never be answered).
_ALLOWED_TOOLS = (
    "Read,Glob,Grep,Edit,Write,"
    "Bash(git ls-files:*),Bash(find:*),Bash(ls:*),Bash(cat:*),Bash(head:*),Bash(wc:*)"
)

# A directory needs at least this many tracked files to be worth its own CLAUDE.md.
_FILE_THRESHOLD = 25
# Cap candidates so a huge repo doesn't fan out into hundreds of generation runs.
_MAX_CANDIDATES = 25
# Top-level directories that are vendored/generated/build output, not authored code.
_NOISE_DIRS = {
    "vendor", "third_party", "node_modules", "generated", "gen", "dist",
    "build", "target", ".venv", "venv", "testdata", "fixtures", "docs",
}


class InitOptions:
    """Holds validated inputs for the startup init command."""

    execute: bool
    model: str
    permission_mode: str
    force: bool
    repo_root: Path


def _build(
    options: InitOptions,
    execute: bool,
    model: str,
    permission_mode: str,
    force: bool,
    dir: str,
) -> None:
    flag_errs = FlagErrors()
    flag_errs.append(check_enum("permission-mode", permission_mode, list(_PERMISSION_MODES)))
    if force and not execute:
        flag_errs.append(
            f"{green('--force')} only applies to {green('--execute')} (it controls overwriting "
            "existing CLAUDE.md files)"
        )
    if err := flag_errs.error():
        raise typer.BadParameter(str(err))

    options.execute = execute
    options.model = model
    options.permission_mode = permission_mode
    options.force = force
    options.repo_root = Path(dir).resolve()


def _run(options: InitOptions) -> None:
    if options.execute:
        _run_execute(options)
    else:
        _run_plan(options)


# --------------------------------------------------------------------------- #
# Phase 1: plan (pure Python — no Claude session, no rate limits, can't hang)  #
# --------------------------------------------------------------------------- #


def _run_plan(options: InitOptions) -> None:
    root = options.repo_root
    typer.echo(f"\n{white(f'Planning CLAUDE.md layout for: {root}')}\n")

    counts = _discover(root)
    candidates = _select_candidates(counts)
    excludes = sorted({d for d in counts if "/" not in d and d in _NOISE_DIRS})

    plan = {
        "root": {"rewrite": True},
        "subfolders": [path for path, _ in candidates],
        "exclude": excludes,
    }
    header = (
        "# ccm2 startup init plan — review and edit, then run: ccm2 startup init --execute\n"
        "# root.rewrite: prune/refresh the root CLAUDE.md (kept lean, repo-wide rules only)\n"
        "# subfolders: directories that will each get their own scoped CLAUDE.md\n"
        "# exclude: written to claudeMdExcludes in .claude/settings.json (packages you skip)\n\n"
    )
    plan_path = root / _PLAN_FILE
    plan_path.parent.mkdir(parents=True, exist_ok=True)
    plan_path.write_text(header + yaml.safe_dump(plan, sort_keys=False))

    typer.echo(green(f"Wrote {plan_path}"))
    if candidates:
        typer.echo(f"  {blue('Candidate subfolders:')}")
        for path, count in candidates:
            typer.echo(f"    - {path}  ({_humanize(count)} files)")
        if len(candidates) == _MAX_CANDIDATES:
            typer.echo(yellow(f"    (capped at {_MAX_CANDIDATES}; add more by editing the plan)"))
    else:
        typer.echo(yellow("  No subfolders met the file-count threshold; only the root is planned."))
    if excludes:
        typer.echo(f"  {blue('Proposed claudeMdExcludes:')} {', '.join(excludes)}")

    typer.echo(
        f"\n  1. Review/edit {cyan(str(_PLAN_FILE))} — add or remove folders as you like."
    )
    typer.echo(f"  2. Generate the files with: {cyan('ccm2 startup init --execute')}")


def _discover(root: Path) -> dict[str, int]:
    """Map each depth-1 and depth-2 directory to its recursive tracked-file count."""
    counts: dict[str, int] = {}
    for rel in _list_tracked_files(root):
        parts = Path(rel).parts
        if len(parts) >= 2:
            counts[parts[0]] = counts.get(parts[0], 0) + 1
        if len(parts) >= 3:
            d2 = f"{parts[0]}/{parts[1]}"
            counts[d2] = counts.get(d2, 0) + 1
    return counts


def _list_tracked_files(root: Path) -> list[str]:
    """Tracked files via `git ls-files`, falling back to a bounded `find`."""
    try:
        r = subprocess.run(["git", "ls-files"], cwd=root, capture_output=True, text=True)
        if r.returncode == 0 and r.stdout.strip():
            return [line for line in r.stdout.splitlines() if line]
    except OSError:
        pass
    try:
        r = subprocess.run(
            ["find", ".", "-maxdepth", "4", "-type", "f", "-not", "-path", "*/.*"],
            cwd=root, capture_output=True, text=True,
        )
        if r.returncode == 0:
            return [
                line[2:] if line.startswith("./") else line
                for line in r.stdout.splitlines()
                if line
            ]
    except OSError:
        pass
    return []


def _select_candidates(counts: dict[str, int]) -> list[tuple[str, int]]:
    """Pick directories worth a CLAUDE.md, preferring specific depth-2 dirs over their parent."""
    depth1 = {k: v for k, v in counts.items() if "/" not in k}
    chosen: list[tuple[str, int]] = []
    for d1, c1 in depth1.items():
        if d1.startswith(".") or d1 in _NOISE_DIRS or c1 < _FILE_THRESHOLD:
            continue
        children = [
            (k, v)
            for k, v in counts.items()
            if k.startswith(f"{d1}/") and v >= _FILE_THRESHOLD
        ]
        chosen.extend(children if children else [(d1, c1)])

    chosen.sort(key=lambda kv: kv[1], reverse=True)
    return chosen[:_MAX_CANDIDATES]


# --------------------------------------------------------------------------- #
# Phase 2: execute (one headless `claude -p` per target, sequential)          #
# --------------------------------------------------------------------------- #


def _run_execute(options: InitOptions) -> None:
    root = options.repo_root
    plan_path = root / _PLAN_FILE
    if not plan_path.exists():
        typer.echo(
            red(
                f"No plan found at {plan_path}. Build one first with "
                f"{green('ccm2 startup init')}."
            ),
            err=True,
        )
        raise typer.Exit(1)

    try:
        plan = yaml.safe_load(plan_path.read_text()) or {}
    except yaml.YAMLError as exc:
        typer.echo(red(f"Could not parse {plan_path}: {exc}"), err=True)
        raise typer.Exit(1) from exc
    if not isinstance(plan, dict):
        typer.echo(red(f"{plan_path} is not a valid plan mapping."), err=True)
        raise typer.Exit(1)

    targets: list[tuple[str, Path, str]] = []  # (label, directory, template-name)
    if (plan.get("root") or {}).get("rewrite"):
        targets.append(("root", root, "generate-root"))
    for sub in plan.get("subfolders") or []:
        targets.append((str(sub), root / str(sub), "generate-subdir"))

    typer.echo(f"\n{white(f'Generating CLAUDE.md files in: {root}')}\n")

    tally = {"created": 0, "skipped": 0, "failed": 0}
    aliased: list[tuple[str, str]] = []  # (alias, session-id)
    for label, target_dir, template_name in targets:
        target_dir = target_dir.resolve()
        if not target_dir.is_dir():
            typer.echo(red(f"  skip {label}: not a directory ({target_dir})"))
            tally["skipped"] += 1
            continue

        claude_md = target_dir / "CLAUDE.md"
        exists = claude_md.exists()
        if exists and not options.force:
            typer.echo(
                yellow(f"  skip {label}: CLAUDE.md already exists (use --force to refresh)")
            )
            tally["skipped"] += 1
            continue

        prompt = _read_template(root, template_name)
        if exists and options.force:
            prompt += (
                "\n\nNOTE: A CLAUDE.md already exists here. Refine and tighten it, preserving "
                "still-accurate content; do not discard useful knowledge. Still enforce the "
                "size budget above."
            )

        # Alias the session with the relative path it ran in (e.g. "ccm2/commands"),
        # so it can later be driven by name with `ccm2 session prompt <alias>`. We
        # register the alias up front and overwrite any stale one so a --force refresh
        # repoints the alias at the freshly generated session.
        session_id = str(uuid.uuid4())
        _register_alias(label, session_id, str(target_dir), aliased)

        typer.echo(yellow(f"  {'refreshing' if exists else 'creating'} {label}/CLAUDE.md ..."))
        rc = run_interactive(
            "claude",
            "--session-id", session_id,
            "-p", prompt,
            "--model", options.model,
            "--permission-mode", options.permission_mode,
            "--allowedTools", _ALLOWED_TOOLS,
            cwd=str(target_dir),
            close_stdin=True,
        )
        if rc == 0:
            tally["created"] += 1
        else:
            typer.echo(red(f"  failed {label}: claude exited {rc}"))
            tally["failed"] += 1

    _apply_excludes(options, plan.get("exclude") or [])

    typer.echo(
        f"\n{white('Done.')} "
        f"{green(str(tally['created']) + ' written')}, "
        f"{yellow(str(tally['skipped']) + ' skipped')}, "
        f"{red(str(tally['failed']) + ' failed')}."
    )
    if aliased:
        typer.echo(f"\n{blue('Sessions aliased by folder')} (drive them with "
                   f"{cyan('ccm2 session prompt <alias>')}):")
        for alias, session_id in aliased:
            typer.echo(f"    - {green(alias)}  ->  {session_id}")
    _link_aliases_file(root)
    typer.echo(
        "\nTo get the context-narrowing benefit: start future sessions INSIDE these subfolders, "
        "and keep the root CLAUDE.md lean."
    )


def _register_alias(
    label: str, session_id: str, cwd: str, aliased: list[tuple[str, str]]
) -> None:
    """Record a folder's generation session under its relative-path alias (best effort).

    Overwrites any existing alias of the same name so re-running --execute repoints it
    at the new session rather than failing on the stale one.
    """
    try:
        aliases.set_alias(label, session_id, cwd, _now_ms(), overwrite=True)
        aliased.append((label, session_id))
    except ValueError as exc:
        typer.echo(yellow(f"  could not alias {label}: {exc}"))


def _link_aliases_file(root: Path) -> None:
    """Symlink .claude/init/aliases.json -> the global ccm2 alias store.

    Gives the repo an at-a-glance view of every session aliased here. Best effort:
    a pre-existing real file is left untouched, and a stale symlink is repointed.
    """
    target = aliases.path().resolve()
    link = root / ".claude" / "init" / "aliases.json"
    link.parent.mkdir(parents=True, exist_ok=True)

    if link.is_symlink():
        try:
            if link.resolve() == target:
                return  # already linked correctly
        except OSError:
            pass
        link.unlink()  # stale/broken/wrong symlink — replace it
    elif link.exists():
        typer.echo(yellow(f"  {link} exists and is not a symlink; leaving it untouched."))
        return

    try:
        link.symlink_to(target)
        typer.echo(green(f"  Linked {link} -> {target}"))
    except OSError as exc:
        typer.echo(yellow(f"  Could not link aliases file: {exc}"))


def _read_template(root: Path, name: str) -> str:
    """Per-repo override at .claude/init/<name>.md, else the template bundled with ccm2."""
    override = root / ".claude" / "init" / f"{name}.md"
    if override.exists():
        text = override.read_text().strip()
        if text:
            return text
    return (_BUNDLED_TEMPLATES / f"{name}.md").read_text().strip()


def _apply_excludes(options: InitOptions, excludes: list) -> None:
    """Merge proposed directories into claudeMdExcludes in .claude/settings.json.

    claudeMdExcludes patterns are matched against the ABSOLUTE path of each
    CLAUDE.md file via picomatch, so a pattern must be anchorable to a full path.
    `**/<dir>/**` matches any CLAUDE.md under <dir> at any depth; a bare
    `<dir>/**` would never match an absolute path and is silently ignored.
    """
    globs = [f"**/{str(e).strip('/')}/**" for e in excludes if str(e).strip()]
    if not globs:
        return
    if not typer.confirm(
        f"\nWrite claudeMdExcludes ({', '.join(globs)}) to .claude/settings.json?",
        default=True,
    ):
        typer.echo(yellow("  skipped claudeMdExcludes."))
        return

    settings_path = options.repo_root / ".claude" / "settings.json"
    settings_path.parent.mkdir(parents=True, exist_ok=True)
    data: dict = {}
    if settings_path.exists():
        try:
            data = json.loads(settings_path.read_text()) or {}
        except json.JSONDecodeError:
            typer.echo(red(f"  {settings_path} is not valid JSON; leaving it untouched."))
            return
    existing = data.get("claudeMdExcludes") or []
    data["claudeMdExcludes"] = sorted(set(existing) | set(globs))
    settings_path.write_text(json.dumps(data, indent=2) + "\n")
    typer.echo(green(f"  Updated claudeMdExcludes in {settings_path}"))


def _humanize(n: int) -> str:
    return f"{n:,}"


def _now_ms() -> int:
    return int(time.time() * 1000)


@startup_app.command("init")
def init(
    execute: bool = typer.Option(
        False,
        "--execute",
        help=flag_string(FlagPriority.OPTIONAL, "Generate the CLAUDE.md files from the plan"),
    ),
    model: str = typer.Option(
        "sonnet",
        "--model",
        help=flag_string(FlagPriority.OPTIONAL, "Model for generation runs", "", "sonnet"),
    ),
    permission_mode: str = typer.Option(
        "acceptEdits",
        "--permission-mode",
        help=flag_string(
            FlagPriority.OPTIONAL,
            "Permission mode for generation runs",
            "default, acceptEdits, plan, bypassPermissions",
            "acceptEdits",
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=flag_string(FlagPriority.OPTIONAL, "Overwrite/refresh existing CLAUDE.md files"),
    ),
    dir: str = typer.Option(
        ".",
        "--dir",
        "-d",
        help=flag_string(FlagPriority.OPTIONAL, "Repository root to operate on", "", "."),
    ),
) -> None:
    """Build a narrowed CLAUDE.md hierarchy for a large repository.

    Plan:     ccm2 startup init            (analyzes the repo, writes .claude/init/plan.yaml)
    Execute:  ccm2 startup init --execute  (generates root + per-subfolder CLAUDE.md files)

    Run the plan step first, edit the plan to taste, then run --execute.
    """
    options = InitOptions()
    _build(options, execute, model, permission_mode, force, dir)
    _run(options)
