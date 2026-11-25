from __future__ import annotations

import sys

import pytest

from deskkit.cli.main import run


@pytest.mark.skipif(sys.platform == "win32", reason="Linux-only")
def test_run_without_context_reports_windows_only(capsys) -> None:
    code = run(["install", "list"])
    assert code == 1
    assert "Windows" in capsys.readouterr().err
