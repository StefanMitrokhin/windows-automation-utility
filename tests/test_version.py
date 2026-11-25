from __future__ import annotations

import tomllib
from pathlib import Path

from deskkit import __version__


def test_version_string() -> None:
    assert __version__ == "0.1.0"


def test_version_matches_pyproject() -> None:
    data = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    assert data["project"]["version"] == "0.1.0"


def test_version_matches_inno() -> None:
    text = Path("installer/installer.iss").read_text(encoding="utf-8")
    assert '#define MyAppVersion "0.1.0"' in text


def test_version_matches_file_info() -> None:
    text = Path("installer/version_info.txt").read_text(encoding="utf-8")
    assert "filevers=(0, 1, 0, 0)" in text
    assert 'FileVersion", "0.1.0"' in text
