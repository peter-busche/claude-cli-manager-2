from enum import Enum

from ccm2.lib.colors import cyan, green, magenta, yellow


class FlagPriority(Enum):
    REQUIRED = "required"
    CONDITIONAL = "conditional"
    OPTIONAL = "optional"


class FlagErrors:
    """Collects multiple flag-validation errors to report them together."""

    def __init__(self) -> None:
        self.errors: list[str] = []

    def append(self, error: str | None) -> None:
        if error:
            self.errors.append(error)

    def error(self) -> Exception | None:
        if self.errors:
            return ValueError("\n".join(self.errors))
        return None


def check_required(flag_name: str, value: object) -> str | None:
    """Return an error string if value is falsy (None, empty string, etc.)."""
    if not value and value != 0:
        return f"required flag not set: [{green(f'--{flag_name}')}]"
    return None


def check_mutually_exclusive(flags: dict[str, object]) -> str | None:
    """Return an error if more than one flag in the dict has a truthy value."""
    set_flags = [f"--{name}" for name, val in flags.items() if val]
    if len(set_flags) > 1:
        return f"mutually exclusive flags cannot be set together: [{green(', '.join(set_flags))}]"
    return None


def check_at_least_one(flags: dict[str, object]) -> str | None:
    """Return an error if no flag in the dict has a truthy value."""
    if not any(flags.values()):
        names = [f"--{n}" for n in flags]
        return f"at least one of the following flags must be set: [{green(', '.join(names))}]"
    return None


def check_enum(flag_name: str, value: str | None, allowed: list[str]) -> str | None:
    """Return an error if value is set but not one of the allowed choices."""
    if not value:
        return None
    if value.lower() not in {a.lower() for a in allowed}:
        return (
            f"invalid value {yellow(value)} for {green(f'--{flag_name}')}: "
            f"must be one of [{green(', '.join(allowed))}]"
        )
    return None


def flag_string(
    necessity: FlagPriority,
    description: str,
    options: str = "",
    default: str = "",
) -> str:
    """Build a colorized, consistently formatted help string for a flag."""
    priority_map = {
        FlagPriority.REQUIRED: magenta("[Req]"),
        FlagPriority.CONDITIONAL: yellow("[Cond]"),
        FlagPriority.OPTIONAL: cyan("[Opt]"),
    }
    priority_str = priority_map[necessity]
    options_str = green(f"({options})") if options else ""
    base = f"{priority_str} {description} {options_str}".strip()
    if not default:
        return base
    return f"{base} --- Defaults: ({default})"
