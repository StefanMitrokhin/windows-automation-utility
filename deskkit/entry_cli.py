from __future__ import annotations

import sys

from deskkit.cli.main import run


def main() -> None:
    raise SystemExit(run(sys.argv[1:]))
