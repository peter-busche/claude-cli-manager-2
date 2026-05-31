# Template for a leaf command under an object (e.g. ccm2 {object_name} {action}).
# Variables filled in by scripts/add_cmd.py:
#   {object_name}    snake_case object name  (e.g. session)
#   {action}         kebab-case action name  (e.g. list-sessions)
#   {snake_action}   snake_case action name  (e.g. list_sessions)
#   {pascal_action}  PascalCase action name  (e.g. ListSessions)
#   {alias_arg}      optional alias string   (e.g. , "--alias", "ls")

from typing import Optional

import typer

from ccm2.lib.colors import yellow
from ccm2.lib.flags import FlagErrors, FlagPriority, check_required, flag_string
from ccm2.commands.{object_name} import {object_name}_app


class {pascal_action}Options:
    """Holds validated inputs for the {action} command."""
    # Add fields for the flags this command needs.
    pass


def _build(options: {pascal_action}Options) -> None:
    """Read flags, validate them, and populate the options object."""
    flag_errs = FlagErrors()
    # flag_errs.append(check_required("some-flag", some_value))
    if flag_errs.errors:
        raise typer.BadParameter("\n".join(flag_errs.errors))
    # Populate options fields here.


def _run(options: {pascal_action}Options) -> None:
    """Main command logic."""
    typer.echo(yellow("TODO: Implement {action}"))


@{object_name}_app.command("{action}"{alias_arg})
def {snake_action}(
    # Define flags here, e.g.:
    # name: Optional[str] = typer.Option(None, "--name", "-n", help=flag_string(FlagPriority.REQUIRED, "The name")),
) -> None:
    """TODO: Short description of {action}."""
    options = {pascal_action}Options()
    _build(options)
    _run(options)
