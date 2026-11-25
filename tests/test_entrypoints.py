from __future__ import annotations

import sys

import pytest


def test_entry_cli_invokes_run(monkeypatch) -> None:
    called = {}

    def fake_run(argv):
        called["argv"] = argv
        return 0

    monkeypatch.setattr("deskkit.entry_cli.run", fake_run)
    monkeypatch.setattr(sys, "argv", ["deskkit-cli", "install", "list"])
    with pytest.raises(SystemExit) as exc:
        import deskkit.entry_cli as entry

        entry.main()
    assert exc.value.code == 0
    assert called["argv"] == ["install", "list"]
