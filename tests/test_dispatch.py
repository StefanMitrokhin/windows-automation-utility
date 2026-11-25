from __future__ import annotations

import sys

from deskkit.__main__ import dispatch


def test_dispatch_version(capsys) -> None:
    assert dispatch(["--version"]) == 0
    assert "0.1.0" in capsys.readouterr().out


def test_dispatch_empty_argv_monkeypatch(monkeypatch) -> None:
    called = {"ok": False}

    def fake_gui(_context=None) -> None:
        called["ok"] = True

    import types

    monkeypatch.setitem(
        sys.modules,
        "deskkit.ui.app",
        types.SimpleNamespace(run_gui=fake_gui),
    )
    assert dispatch([]) == 0
    assert called["ok"]
