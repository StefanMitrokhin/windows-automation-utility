from __future__ import annotations

import sys


def dispatch(argv: list[str]) -> int:
    if not argv or argv[0] == "gui":
        if len(argv) > 1:
            print("команда gui не принимает аргументы", file=sys.stderr)
            return 4
        from deskkit.ui.app import run_gui

        run_gui()
        return 0
    if argv[0] in {"-V", "--version"}:
        from deskkit import __version__

        print(f"DeskKit {__version__}")
        return 0
    from deskkit.cli.main import run

    return run(argv)


def main() -> None:
    raise SystemExit(dispatch(sys.argv[1:]))
