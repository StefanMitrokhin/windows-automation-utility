from __future__ import annotations

from pathlib import Path

import pytest

from deskkit.errors import PathNotAllowedError
from deskkit.safety import (
    destination_conflicts,
    ensure_absolute,
    is_denied_source,
    is_drive_root,
    safe_arcname,
)


def test_reject_relative() -> None:
    with pytest.raises(PathNotAllowedError):
        ensure_absolute(Path("docs"))


def test_drive_root() -> None:
    assert is_drive_root(Path("C:\\"))
    assert is_drive_root(Path("/"))
    assert not is_drive_root(Path(r"C:\Users"))


def test_denied_windows_and_program_files() -> None:
    assert is_denied_source(Path(r"C:\Windows"))
    assert is_denied_source(Path(r"D:\Program Files\X"))
    assert is_denied_source(Path(r"c:\program files (x86)\a"))
    assert not is_denied_source(Path(r"C:\Users\A\Documents"))


def test_destination_inside_source() -> None:
    src = Path("/data/docs")
    assert destination_conflicts([src], src / "backup")
    assert destination_conflicts([src / "backup"], src)


def test_safe_arcname_rejects() -> None:
    for bad in ("../a", "/a", "a/../../b", "a\\b"):
        with pytest.raises(PathNotAllowedError):
            safe_arcname(bad)


def test_safe_arcname_accepts() -> None:
    assert safe_arcname("source-1/docs/a.txt") == "source-1/docs/a.txt"


def test_denied_windows_path_string() -> None:
    assert is_denied_source(Path("C:/Windows/System32"))


def test_no_shell_true_in_sources() -> None:
    root = Path("deskkit")
    banned = ("shell=True", "os.system", "pickle.loads", "eval(")
    for path in root.rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for token in banned:
            assert token not in text
