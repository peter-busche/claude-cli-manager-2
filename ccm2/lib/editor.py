import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from ccm2.lib.colors import cyan


def prompt_via_editor(instructions: str, ext_hint: str = "md") -> str:
    """Open the user's editor on a temp file seeded with instructions.

    Instructions are written as '# ' comment lines. Lines starting with '#'
    are stripped from the returned content.
    """
    editor = _choose_editor()
    commented = "\n".join(f"# {line}" for line in instructions.splitlines())

    with tempfile.NamedTemporaryFile(
        suffix=f".{ext_hint}", mode="w", delete=False, encoding="utf-8"
    ) as f:
        tmp_path = f.name
        f.write(commented + "\n")

    try:
        print(cyan(f"Opening {editor} (save & close when done)..."))
        subprocess.run([editor, tmp_path], check=True)
        raw = Path(tmp_path).read_text(encoding="utf-8")
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass

    return _strip_comments(raw).strip()


def _choose_editor() -> str:
    for env_var in ("VISUAL", "EDITOR"):
        val = os.environ.get(env_var, "").strip()
        if val:
            return val
    for fallback in ("nano", "vi"):
        if shutil.which(fallback):
            return fallback
    raise RuntimeError("no editor found; set $VISUAL or $EDITOR")


def _strip_comments(text: str) -> str:
    return "\n".join(line for line in text.splitlines() if not line.startswith("#"))
