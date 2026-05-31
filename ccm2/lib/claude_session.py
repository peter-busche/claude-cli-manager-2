import json
import subprocess
from pathlib import Path


def list_live_sessions() -> list[dict]:
    """Run `claude agents --json` and return the parsed list."""
    result = subprocess.run(
        ["claude", "agents", "--json"],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        raise RuntimeError(f"claude agents --json failed: {result.stderr.strip()}")
    return json.loads(result.stdout) or []


def find_by_session_id(sessions: list[dict], session_id: str) -> dict | None:
    for s in sessions:
        if s.get("sessionId") == session_id:
            return s
    return None


def transcript_path(cwd: str, session_id: str) -> Path:
    encoded = cwd.replace("/", "-")
    return Path.home() / ".claude" / "projects" / encoded / f"{session_id}.jsonl"


def conversation_exists(cwd: str, session_id: str) -> bool:
    p = transcript_path(cwd, session_id)
    return p.exists() and p.stat().st_size > 0
