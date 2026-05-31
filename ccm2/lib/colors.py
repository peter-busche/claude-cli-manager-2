from rich.console import Console

_console = Console(highlight=False)


def _colorize(text: object, style: str) -> str:
    with _console.capture() as capture:
        _console.print(str(text), style=style, end="")
    return capture.get()


def red(text: object) -> str:
    return _colorize(text, "red")


def green(text: object) -> str:
    return _colorize(text, "green")


def blue(text: object) -> str:
    return _colorize(text, "blue")


def yellow(text: object) -> str:
    return _colorize(text, "yellow")


def magenta(text: object) -> str:
    return _colorize(text, "magenta")


def cyan(text: object) -> str:
    return _colorize(text, "cyan")


def white(text: object) -> str:
    return _colorize(text, "white")


def orange(text: object) -> str:
    return _colorize(text, "color(214)")


def pink(text: object) -> str:
    return _colorize(text, "color(213)")
