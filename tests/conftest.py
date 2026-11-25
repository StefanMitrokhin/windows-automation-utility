from __future__ import annotations

from pathlib import Path

import pytest

from tests.fakes import make_context


@pytest.fixture(autouse=True)
def isolated_env(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "Roaming").mkdir()
    (tmp_path / "Local").mkdir()
    (tmp_path / "Temp").mkdir()
    (tmp_path / "Windows").mkdir()
    (tmp_path / "ProgramData").mkdir()
    monkeypatch.setenv("APPDATA", str(tmp_path / "Roaming"))
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path / "Local"))
    monkeypatch.setenv("TEMP", str(tmp_path / "Temp"))
    monkeypatch.setenv("TMP", str(tmp_path / "Temp"))
    monkeypatch.setenv("SYSTEMROOT", str(tmp_path / "Windows"))
    monkeypatch.setenv("PROGRAMDATA", str(tmp_path / "ProgramData"))
    monkeypatch.delenv("DESKKIT_PROFILE", raising=False)


@pytest.fixture
def context(tmp_path: Path):
    return make_context(tmp_path)
