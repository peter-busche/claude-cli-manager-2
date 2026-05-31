import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

import typer

from ccm2.commands.session import session_app
from ccm2.lib.colors import blue, green, red, white, yellow
from ccm2.lib.flags import FlagPriority, flag_string

_DEFAULT_TOKEN_LIMIT = 200_000


class ListOptions:
    """Holds validated inputs for the session list command."""

    repo_dir: Path
    sessions_dir: Path
    projects_dir: Path
    show_all: bool


def _build(options: ListOptions, dir: str, show_all: bool) -> None:
    options.repo_dir = Path(dir).resolve()
    home = Path.home()
    options.sessions_dir = home / ".claude" / "sessions"
    options.projects_dir = home / ".claude" / "projects"
    options.show_all = show_all


def _run(options: ListOptions) -> None:
    if not options.sessions_dir.exists() and not options.show_all:
        typer.echo("No Claude sessions directory found")
        return

    typer.echo(f"\n{white(f'Claude Sessions for: {options.repo_dir}')}\n")

    # Collect live sessions first (those with a metadata file in ~/.claude/sessions),
    # then — with --all — fold in completed sessions discovered from their persisted
    # transcripts in ~/.claude/projects. Live status wins on any session ID overlap.
    records: list[dict] = []
    seen: set[str] = set()

    if options.sessions_dir.exists():
        for session_file in sorted(options.sessions_dir.glob("*.json")):
            meta = _read_session_meta(session_file)
            if meta is None or meta.get("cwd") != str(options.repo_dir):
                continue
            sid = meta.get("sessionId")
            if sid:
                seen.add(sid)
            records.append(meta)

    if options.show_all:
        records.extend(_persisted_sessions(options, seen))

    for i, meta in enumerate(records, 1):
        _print_session(options, meta, i)

    if not records:
        typer.echo(red(f"No Claude sessions found for: {options.repo_dir}"))
    else:
        typer.echo(white(f"Total Sessions: {len(records)}"))


def _persisted_sessions(options: ListOptions, seen: set[str]) -> list[dict]:
    """Synthesize session records from persisted transcripts not already live.

    Each ~/.claude/projects/<encoded-cwd>/<sessionID>.jsonl is a session that ran
    in this cwd. Completed headless runs have no live metadata file, so this is the
    only way to surface them (and their sub-agents) after they exit.
    """
    proj = options.projects_dir / _encode_path(str(options.repo_dir))
    if not proj.exists():
        return []

    transcripts = sorted(proj.glob("*.jsonl"), key=lambda p: p.stat().st_mtime, reverse=True)
    out: list[dict] = []
    for transcript in transcripts:
        sid = transcript.stem
        if sid in seen:
            continue
        seen.add(sid)
        out.append(
            {
                "sessionId": sid,
                "cwd": str(options.repo_dir),
                "status": "completed",
                "updatedAt": 0,
            }
        )
    return out


def _print_session(options: ListOptions, meta: dict, num: int) -> None:
    session_id = meta.get("sessionId") or "unknown"
    status = meta.get("status") or "unknown"

    transcript = (
        options.projects_dir / _encode_path(str(options.repo_dir)) / f"{session_id}.jsonl"
    )
    stats = _read_transcript_stats(transcript)

    if meta.get("updatedAt"):
        last_triggered: Optional[datetime] = datetime.fromtimestamp(
            meta["updatedAt"] / 1000, tz=timezone.utc
        )
    else:
        last_triggered = stats["last_activity"]

    def _opt(label: str, value: str) -> None:
        if value:
            typer.echo(f"  {blue(label)} {value}")

    typer.echo(green(f"Session #{num}"))
    typer.echo(f"  {blue('Session ID:')} {session_id}")
    _opt("Title:", stats["custom_title"])
    typer.echo(f"  {blue('Status:')} {status}")
    typer.echo(f"  {blue('Model:')} {stats['model'] or 'unknown'}")
    typer.echo(f"  {blue('Last Triggered:')} {_format_time(last_triggered)}")
    typer.echo(f"  {blue('Context Tokens:')} {_humanize_int(stats['context_tokens'])}")
    typer.echo(f"  {blue('Max Tokens:')} {_humanize_int(_model_max_tokens(stats['model']))}")

    _print_sub_agents(options, str(options.repo_dir), session_id)
    typer.echo()


def _print_sub_agents(options: ListOptions, cwd: str, session_id: str) -> None:
    subagents_dir = options.projects_dir / _encode_path(cwd) / session_id / "subagents"
    if not subagents_dir.exists():
        return
    agent_files = sorted(subagents_dir.glob("agent-*.jsonl"))
    if not agent_files:
        return

    agents = []
    for agent_file in agent_files:
        meta_path = agent_file.parent / (agent_file.stem + ".meta.json")
        sub_meta = _read_sub_agent_meta(meta_path)
        name = sub_meta.get("agentType") or agent_file.stem
        agents.append((name, _read_transcript_stats(agent_file)))
    agents.sort(key=lambda x: x[0])

    typer.echo(f"  {yellow('Triggered sub-agents:')}")
    for name, stats in agents:
        typer.echo(f"    - {green(name)}")
        typer.echo(f"        {blue('Model:')} {stats['model'] or 'unknown'}")
        typer.echo(f"        {blue('Last Triggered:')} {_format_time(stats['last_activity'])}")
        typer.echo(f"        {blue('Context Tokens:')} {_humanize_int(stats['context_tokens'])}")
        typer.echo(f"        {blue('Max Tokens:')} {_humanize_int(_model_max_tokens(stats['model']))}")


def _read_session_meta(path: Path) -> Optional[dict]:
    try:
        return json.loads(path.read_text())
    except Exception:
        return None


def _read_sub_agent_meta(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except Exception:
        return {}


def _read_transcript_stats(path: Path) -> dict:
    stats: dict = {
        "model": "",
        "last_activity": None,
        "context_tokens": 0,
        "custom_title": "",
    }
    if not path.exists():
        return stats

    latest_assistant_ts: Optional[datetime] = None
    try:
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except json.JSONDecodeError:
                    continue

                ts = _parse_timestamp(entry.get("timestamp", ""))
                if ts and (stats["last_activity"] is None or ts > stats["last_activity"]):
                    stats["last_activity"] = ts

                if entry.get("type") == "custom-title" and entry.get("customTitle"):
                    stats["custom_title"] = entry["customTitle"]

                if entry.get("type") == "assistant":
                    msg = entry.get("message", {})
                    usage = msg.get("usage", {})
                    if ts and (latest_assistant_ts is None or ts > latest_assistant_ts):
                        latest_assistant_ts = ts
                        stats["model"] = msg.get("model", "")
                        stats["context_tokens"] = (
                            usage.get("input_tokens", 0)
                            + usage.get("cache_creation_input_tokens", 0)
                            + usage.get("cache_read_input_tokens", 0)
                            + usage.get("output_tokens", 0)
                        )
    except Exception:
        pass

    return stats


def _model_max_tokens(model: str) -> int:
    try:
        from ccm2.main import config  # noqa: PLC0415

        limits = config.get("model_token_limits", {})
        if isinstance(limits, dict) and model:
            for key, val in limits.items():
                if key in model:
                    try:
                        return int(val)
                    except (ValueError, TypeError):
                        pass
        default = config.get("default_token_limit")
        if default:
            try:
                return int(default)
            except (ValueError, TypeError):
                pass
    except ImportError:
        pass
    return _DEFAULT_TOKEN_LIMIT


def _encode_path(p: str) -> str:
    """Match ~/.claude/projects directory naming: replace '/' with '-'."""
    return p.replace("/", "-")


def _parse_timestamp(s: str) -> Optional[datetime]:
    if not s:
        return None
    try:
        return datetime.fromisoformat(s.replace("Z", "+00:00"))
    except ValueError:
        return None


def _format_time(t: Optional[datetime]) -> str:
    if t is None:
        return "unknown"
    return t.astimezone().strftime("%Y-%m-%d %H:%M:%S")


def _humanize_int(n: int) -> str:
    return f"{n:,}"


@session_app.command("list")
@session_app.command("ls")
def list_command(
    dir: str = typer.Option(
        ".",
        "--dir",
        "-d",
        help=flag_string(FlagPriority.OPTIONAL, "Repository directory to inspect", "", "."),
    ),
    show_all: bool = typer.Option(
        False,
        "--all",
        "-a",
        help=flag_string(
            FlagPriority.OPTIONAL,
            "Include completed sessions (from persisted transcripts), not just live ones",
        ),
    ),
) -> None:
    """List Claude Code sessions and sub-agents for a repository.

    By default only live sessions (those with a process metadata file) are shown.
    Use --all to also surface completed sessions and their sub-agents from
    persisted transcripts in ~/.claude/projects.
    """
    options = ListOptions()
    _build(options, dir, show_all)
    _run(options)
