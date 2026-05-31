import typer

startup_app = typer.Typer(
    name="startup",
    help="One-time setup commands for onboarding a repository.",
    no_args_is_help=True,
)

# Subcommand imports are appended here by scripts/add_cmd.py:
from ccm2.commands.startup import init  # noqa: F401
from ccm2.commands.startup import bootstrap  # noqa: F401
