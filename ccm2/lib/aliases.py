import json
from pathlib import Path


def _path() -> Path:
    return Path.home() / ".config" / "ccm2" / "aliases.json"


def load() -> dict:
    p = _path()
    if not p.exists():
        return {}
    try:
        return json.loads(p.read_text()) or {}
    except Exception:
        return {}


def save(store: dict) -> None:
    p = _path()
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(store, indent=2) + "\n")


def set_alias(name: str, session_id: str, cwd: str, created_at_ms: int) -> None:
    store = load()
    existing = store.get(name)
    if existing and existing.get("sessionId") != session_id:
        raise ValueError(
            f"alias '{name}' already points to session {existing['sessionId']}; "
            "delete it first before reassigning"
        )
    store[name] = {"sessionId": session_id, "cwd": cwd, "createdAt": created_at_ms}
    save(store)


def resolve(name: str) -> dict | None:
    return load().get(name)


def sorted_names(store: dict) -> list[str]:
    return sorted(store.keys())
