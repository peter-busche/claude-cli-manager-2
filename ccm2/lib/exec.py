import subprocess
import sys


def execute_command(command: str) -> tuple[str, str, Exception | None]:
    """Run a shell command and return (stdout, stderr, error)."""
    result = subprocess.run(command, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        err = RuntimeError(f"command error: exit code {result.returncode}\n{result.stderr.strip()}")
        return result.stdout, result.stderr, err
    return result.stdout, result.stderr, None


def execute_command_live(command: str) -> int:
    """Run a shell command and stream its output to the terminal in real time."""
    result = subprocess.run(
        command,
        shell=True,
        stdin=sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
    )
    return result.returncode


def run_interactive(
    name: str, *args: str, cwd: str | None = None, close_stdin: bool = False
) -> int:
    """Launch an external binary with the terminal attached (stdin/stdout/stderr inherited).

    Set close_stdin=True for headless runs (e.g. `claude -p`) that take their input
    from argv and would otherwise block waiting on stdin.
    """
    result = subprocess.run(
        [name, *args],
        stdin=subprocess.DEVNULL if close_stdin else sys.stdin,
        stdout=sys.stdout,
        stderr=sys.stderr,
        cwd=cwd,
    )
    return result.returncode
