import typer

session_app = typer.Typer(
    name="session",
    help="Commands for inspecting Claude Code sessions.",
    no_args_is_help=True,
)

# Subcommand imports are appended here by scripts/add_cmd.py:
from ccm2.commands.session import list  # noqa: F401
from ccm2.commands.session import create  # noqa: F401
from ccm2.commands.session import prompt  # noqa: F401
