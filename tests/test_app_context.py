from __future__ import annotations

import sys

import pytest

from deskkit.app_context import resolve_cli_argv
from deskkit.errors import UnsupportedOSError


def test_resolve_cli_argv_dev() -> None:
    assert resolve_cli_argv() == [sys.executable, "-m", "deskkit"]


def test_build_context_non_windows() -> None:
    from deskkit.app_context import build_context

    if sys.platform == "win32":
        pytest.skip("Windows only negative path")
    with pytest.raises(UnsupportedOSError):
        build_context()
