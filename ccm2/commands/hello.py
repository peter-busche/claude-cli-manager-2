from typing import Optional

import typer

from ccm2.lib.colors import cyan, green, yellow
from ccm2.lib.flags import FlagPriority, flag_string


def hello_command(
    name: Optional[str] = typer.Option(
        None,
        "--name",
        "-n",
        help=flag_string(FlagPriority.OPTIONAL, "Who to greet", "", "world"),
    ),
) -> None:
    """Temporary smoke-test command — confirms ccm2 is installed and working."""
    display_name = name or "world"
    typer.echo(
        f"{green('Hello')}, {cyan(display_name)}! {yellow('ccm2 is installed and working.')}"
    )
