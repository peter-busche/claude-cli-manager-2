#!/usr/bin/env python3
"""Generate a new ccm2 object+command pair.

Usage:
    python scripts/add_cmd.py <object_name> <action> [alias]

Examples:
    python scripts/add_cmd.py session list
    python scripts/add_cmd.py session list-sessions list
"""
import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
COMMANDS_DIR = PROJECT_ROOT / "ccm2" / "commands"
MAIN_PY = PROJECT_ROOT / "ccm2" / "main.py"


def to_snake(name: str) -> str:
    return name.replace("-", "_")


def to_pascal(name: str) -> str:
    return "".join(w.capitalize() for w in name.replace("-", "_").split("_"))


def create_object_package(object_name: str) -> Path:
    pkg_dir = COMMANDS_DIR / object_name
    pkg_dir.mkdir(parents=True, exist_ok=True)

    init_file = pkg_dir / "__init__.py"
    if not init_file.exists():
        init_file.write_text(
            f"import typer\n\n"
            f"{object_name}_app = typer.Typer(\n"
            f'    name="{object_name}",\n'
            f'    help="TODO: Short description of {object_name} commands.",\n'
            f"    no_args_is_help=True,\n"
            f")\n\n"
            f"# Subcommand imports are appended here by scripts/add_cmd.py:\n"
        )
        print(f"Created {init_file.relative_to(PROJECT_ROOT)}")
    else:
        print(f"Object {object_name} already exists — skipping __init__.py creation")

    return pkg_dir


def create_command_file(pkg_dir: Path, object_name: str, action: str, alias: str = "") -> Path:
    snake_action = to_snake(action)
    pascal_action = to_pascal(action)
    alias_arg = f', "--alias", "{alias}"' if alias else ""

    cmd_file = pkg_dir / f"{snake_action}.py"
    if cmd_file.exists():
        print(f"Command {action} already exists at {cmd_file.relative_to(PROJECT_ROOT)}")
        return cmd_file

    cmd_file.write_text(
        f"from typing import Optional\n\n"
        f"import typer\n\n"
        f"from ccm2.lib.colors import yellow\n"
        f"from ccm2.lib.flags import FlagErrors, FlagPriority, check_required, flag_string\n"
        f"from ccm2.commands.{object_name} import {object_name}_app\n\n\n"
        f"class {pascal_action}Options:\n"
        f'    """Holds validated inputs for the {action} command."""\n\n'
        f"    # Add fields for the flags this command needs.\n"
        f"    pass\n\n\n"
        f"def _build(options: {pascal_action}Options) -> None:\n"
        f'    """Read flags, validate them, and populate the options object."""\n'
        f"    flag_errs = FlagErrors()\n"
        f'    # flag_errs.append(check_required("some-flag", some_value))\n'
        f"    if flag_errs.errors:\n"
        f'        raise typer.BadParameter("\\n".join(flag_errs.errors))\n\n\n'
        f"def _run(options: {pascal_action}Options) -> None:\n"
        f'    """Main command logic."""\n'
        f'    typer.echo(yellow("TODO: Implement {action}"))\n\n\n'
        f'@{object_name}_app.command("{action}"{alias_arg})\n'
        f"def {snake_action}(\n"
        f"    # Define flags here, e.g.:\n"
        f"    # name: Optional[str] = typer.Option(None, \"--name\", \"-n\","
        f" help=flag_string(FlagPriority.REQUIRED, \"The name\")),\n"
        f") -> None:\n"
        f'    """TODO: Short description of {action}."""\n'
        f"    options = {pascal_action}Options()\n"
        f"    _build(options)\n"
        f"    _run(options)\n"
    )
    print(f"Created {cmd_file.relative_to(PROJECT_ROOT)}")

    # Add import to the object's __init__.py so the decorator fires.
    init_file = pkg_dir / "__init__.py"
    init_content = init_file.read_text()
    import_line = f"from ccm2.commands.{object_name} import {snake_action}  # noqa: F401\n"
    existing_lines = init_content.splitlines()
    if import_line.rstrip() not in existing_lines:
        init_file.write_text(init_content + import_line)
        print(f"Registered {snake_action} in {init_file.relative_to(PROJECT_ROOT)}")

    return cmd_file


def register_object_in_main(object_name: str) -> None:
    main_content = MAIN_PY.read_text()

    import_line = f"from ccm2.commands.{object_name} import {object_name}_app"
    register_line = f'app.add_typer({object_name}_app, name="{object_name}")'

    if import_line in main_content:
        print(f"Object {object_name} already registered in main.py")
        return

    marker = "# --- OBJECT COMMANDS (add new sub-apps here) ---"
    if marker not in main_content:
        print(f"WARNING: marker not found in main.py. Add these lines manually:")
        print(f"  {import_line}")
        print(f"  {register_line}")
        return

    MAIN_PY.write_text(
        main_content.replace(marker, f"{marker}\n{import_line}\n{register_line}")
    )
    print(f"Registered {object_name} in ccm2/main.py")


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("object_name", help="Object name, e.g. 'session'")
    parser.add_argument("action", help="Action name, e.g. 'list' or 'list-sessions'")
    parser.add_argument("alias", nargs="?", default="", help="Optional short alias, e.g. 'ls'")
    args = parser.parse_args()

    object_name = to_snake(args.object_name)
    if "-" in object_name:
        print("Error: object_name cannot contain dashes. Use underscores or a single word.")
        sys.exit(1)

    pkg_dir = create_object_package(object_name)
    create_command_file(pkg_dir, object_name, args.action, args.alias)
    register_object_in_main(object_name)

    print("\nDone. Run 'pip install -e .' if you haven't already, then test with 'ccm2'.")


if __name__ == "__main__":
    main()
