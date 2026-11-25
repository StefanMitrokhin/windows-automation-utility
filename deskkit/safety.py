from __future__ import annotations

import os
import sys
from collections.abc import Sequence
from pathlib import Path

from deskkit.errors import PathNotAllowedError

DENIED_PREFIXES: tuple[str, ...] = (
    "windows",
    "program files",
    "program files (x86)",
)

FILE_ATTRIBUTE_REPARSE_POINT = 0x400


def ensure_absolute(path: Path) -> Path:
    expanded = path.expanduser()
    text = str(expanded)
    if len(text) >= 2 and text[1] == ":":
        return expanded
    if not expanded.is_absolute():
        raise PathNotAllowedError("Нужен полный путь.")
    return expanded


def is_drive_root(path: Path) -> bool:
    if path.is_absolute() and path == Path(path.anchor):
        return True
    text = str(path)
    return len(text) == 3 and text[1] == ":" and text[2] in ("/", "\\")


def is_denied_source(path: Path) -> bool:
    if is_drive_root(path):
        return True
    parts = path.parts
    if len(parts) >= 2:
        first = parts[1].lower()
        if first in DENIED_PREFIXES:
            return True
    text = str(path).replace("\\", "/")
    if ":" in text:
        tail = text.split(":", maxsplit=1)[1].lstrip("/")
        first = tail.split("/", maxsplit=1)[0].lower()
        return first in DENIED_PREFIXES
    return False


def destination_conflicts(sources: Sequence[Path], destination: Path) -> bool:
    dst = destination.resolve(strict=False)
    for src in sources:
        s = src.resolve(strict=False)
        if dst == s:
            return True
        try:
            if dst.is_relative_to(s) or s.is_relative_to(dst):
                return True
        except (ValueError, OSError):
            continue
    return False


def safe_arcname(arcname: str) -> str:
    if not arcname:
        raise PathNotAllowedError("Недопустимое имя в архиве.")
    if "\\" in arcname:
        raise PathNotAllowedError("Недопустимое имя в архиве.")
    if arcname.startswith("/") or Path(arcname).is_absolute():
        raise PathNotAllowedError("Недопустимое имя в архиве.")
    for segment in arcname.split("/"):
        if segment in (".", "..", ""):
            raise PathNotAllowedError("Недопустимое имя в архиве.")
    return arcname


def is_reparse_point(path: Path) -> bool:
    if path.is_symlink():
        return True
    if sys.platform == "win32":
        st = os.stat(path, follow_symlinks=False)
        attrs = getattr(st, "st_file_attributes", 0)
        if attrs & FILE_ATTRIBUTE_REPARSE_POINT:
            return True
    return False
