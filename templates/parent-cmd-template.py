# Template for an object (parent) command package — ccm2/commands/{object_name}/__init__.py.
# Variables filled in by scripts/add_cmd.py:
#   {object_name}  snake_case object name (e.g. session)

import typer

{object_name}_app = typer.Typer(
    name="{object_name}",
    help="TODO: Short description of {object_name} commands.",
    no_args_is_help=True,
)

# Import subcommands below so their @{object_name}_app.command() decorators fire:
# from ccm2.commands.{object_name} import list_sessions  # noqa: F401
