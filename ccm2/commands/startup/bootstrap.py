import fnmatch
import shutil
from pathlib import Path

import typer

from ccm2.commands.startup import startup_app
from ccm2.lib.colors import blue, cyan, green, red, white, yellow
from ccm2.lib.flags import FlagPriority, flag_string

# The canonical .claude lives at the root of the ccm2 repo this package is
# installed from (parents: startup -> commands -> ccm2 -> repo root).
_CANONICAL_CLAUDE = Path(__file__).resolve().parents[3] / ".claude"

# Project-specific or transient entries at the top of .claude/ that must not be
# carried into a fresh repo.
_EXCLUDE_TOP = {
    "agent-memory",          # per-agent memory tied to the source project
    "settings.local.json",   # personal permission allowlist (machine-local)
    "scheduled_tasks.lock",  # transient runtime lock
    "init",                  # only an empty stub; init templates ship inside ccm2
}
# Cruft to drop wherever it appears in the tree.
_EXCLUDE_ANY = {"__pycache__", ".DS_Store", "worktrees", ".git", "node_modules", ".venv"}
_EXCLUDE_GLOB = ("*.pyc", "*.log", "*.lock", "*.cache", "*.local.json", "plan.yaml")


class BootstrapOptions:
    """Holds validated inputs for the bootstrap command."""

    source: Path
    target_claude: Path
    force: bool


def _build(options: BootstrapOptions, dir: str, source: str, force: bool) -> None:
    options.source = (Path(source).resolve() if source else _CANONICAL_CLAUDE)
    options.target_claude = (Path(dir).resolve() / ".claude")
    options.force = force


def _run(options: BootstrapOptions) -> None:
    source = options.source
    target = options.target_claude

    if not source.is_dir():
        typer.echo(red(f"Source .claude not found at {source}"), err=True)
        raise typer.Exit(1)

    # Never bootstrap into the source repo itself — it would delete/clobber the
    # canonical .claude we copy from.
    if target.resolve() == source.resolve():
        typer.echo(
            red("Refusing to bootstrap into the source repo itself (target == source)."),
            err=True,
        )
        raise typer.Exit(1)

    if target.exists():
        if not options.force and not typer.confirm(
            red(f"{target} already exists. Delete it and replace with the bootstrap?"),
            default=False,
        ):
            typer.echo(
                yellow("Aborted. Remove or rename the existing .claude/ and re-run.")
            )
            raise typer.Exit(1)
        shutil.rmtree(target)

    shutil.copytree(source, target, ignore=_make_ignore(source))

    scaffolded = _scaffold_agent_memory(target)
    _report(options, source, target, scaffolded)


def _make_ignore(source: Path):
    """Build a copytree ignore() that drops project-specific and transient files."""
    source = source.resolve()

    def _ignore(directory: str, names: list[str]) -> set[str]:
        ignored: set[str] = set()
        if Path(directory).resolve() == source:
            ignored |= {n for n in names if n in _EXCLUDE_TOP}
        ignored |= {n for n in names if n in _EXCLUDE_ANY}
        ignored |= {n for n in names if any(fnmatch.fnmatch(n, g) for g in _EXCLUDE_GLOB)}
        return ignored

    return _ignore


def _scaffold_agent_memory(target: Path) -> list[str]:
    """Recreate empty, git-trackable per-agent memory dirs (no copied content).

    Claude Code auto-loads agent memory from .claude/agent-memory/<agentType>/.
    The source project's own memory is excluded from the copy; here we seed a
    fresh empty dir per copied agent (with a .gitkeep so it survives a commit, as
    git does not track empty directories). agentType is taken from the agent's
    filename, which matches its `name:` by convention.
    """
    agents_dir = target / "agents"
    if not agents_dir.is_dir():
        return []
    created: list[str] = []
    for agent_file in sorted(agents_dir.glob("*.md")):
        mem_dir = target / "agent-memory" / agent_file.stem
        mem_dir.mkdir(parents=True, exist_ok=True)
        (mem_dir / ".gitkeep").write_text("")
        created.append(agent_file.stem)
    return created


def _report(
    options: BootstrapOptions, source: Path, target: Path, scaffolded: list[str]
) -> None:
    # agent-memory is reported on its own line (content excluded, empty scaffold
    # recreated), so keep it out of the copied/excluded lists to avoid showing it
    # as both.
    present = sorted(p.name for p in source.iterdir())
    excluded = [n for n in present if n in _EXCLUDE_TOP and n != "agent-memory"]
    copied = sorted(p.name for p in target.iterdir() if p.name != "agent-memory")

    typer.echo(green(f"\nBootstrapped .claude/ into {target.parent}"))
    typer.echo(f"  {blue('Source:')} {source}")
    typer.echo(f"  {blue('Copied:')} {', '.join(copied)}")
    if excluded:
        typer.echo(f"  {yellow('Excluded (project-specific/transient):')} {', '.join(excluded)}")
    if scaffolded:
        typer.echo(
            f"  {blue('Agent-memory scaffold:')} empty dirs for {', '.join(scaffolded)}"
        )
    typer.echo(
        f"\n  Next: tailor the root {cyan('CLAUDE.md')} for this repo with "
        f"{cyan('ccm2 startup init')}."
    )


@startup_app.command("bootstrap")
def bootstrap(
    dir: str = typer.Option(
        ".",
        "--dir",
        "-d",
        help=flag_string(FlagPriority.OPTIONAL, "Repository root to bootstrap into", "", "."),
    ),
    source: str = typer.Option(
        "",
        "--source",
        help=flag_string(
            FlagPriority.OPTIONAL, "Source .claude to copy from", "", "ccm2's own .claude"
        ),
    ),
    force: bool = typer.Option(
        False,
        "--force",
        help=flag_string(FlagPriority.OPTIONAL, "Replace an existing .claude/ without prompting"),
    ),
) -> None:
    """Seed a repository with a portable copy of ccm2's .claude framework.

    Copies agents, conventions, skills, and templates into the target repo's
    .claude/, dropping project-specific memory and machine-local settings. If a
    .claude/ already exists, you are prompted to replace it.
    """
    options = BootstrapOptions()
    _build(options, dir, source, force)
    _run(options)
