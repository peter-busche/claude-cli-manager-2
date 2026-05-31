import os
from pathlib import Path
from typing import Optional

import typer
import yaml

from ccm2.lib.colors import red

VERSION_FILE = Path(__file__).parent.parent / "VERSION"

app = typer.Typer(
    name="ccm2",
    no_args_is_help=True,
    add_completion=True,
)


def _version_callback(value: bool) -> None:
    if value:
        typer.echo(VERSION_FILE.read_text().strip())
        raise typer.Exit()


@app.callback()
def root(
    version: Optional[bool] = typer.Option(
        None,
        "--version",
        "-v",
        callback=_version_callback,
        is_eager=True,
        help="Show version and exit.",
    ),
) -> None:
    """claude-cli-manager-2 (ccm2) is the one stop shop for managing your Claude tooling.

    Commands follow the format 'ccm2 <object> <command> <flags>'.
    Explore by passing the --help flag to any object or command!
    """


# --- OBJECT COMMANDS (add new sub-apps here) ---


# --- ROOT COMMANDS ---
from ccm2.commands.hello import hello_command  # noqa: E402

app.command("hello")(hello_command)


def _load_config() -> dict:
    config_path = Path.home() / ".config" / "ccm2" / "config.yaml"
    if config_path.exists():
        try:
            with config_path.open() as f:
                return yaml.safe_load(f) or {}
        except Exception as exc:
            typer.echo(red(f"Config file error: {exc}"), err=True)
            raise typer.Exit(1) from exc
    return {}


# Read config file then overlay any CCM2_* env vars.
config: dict = _load_config()
for _key, _val in os.environ.items():
    if _key.startswith("CCM2_"):
        config[_key[5:].lower()] = _val
