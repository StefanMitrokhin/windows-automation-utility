from __future__ import annotations

import os
import zipfile
from pathlib import Path

import pytest

from deskkit.models import ZipMember
from deskkit.platform.files import LocalFileOps


def test_walk_sums_and_skips_missing_root(tmp_path: Path) -> None:
    ops = LocalFileOps()
    assert ops.walk_files(tmp_path / "missing") == ()
    target = tmp_path / "f.bin"
    target.write_bytes(b"12345")
    entries = ops.walk_files(tmp_path)
    assert len(entries) == 1
    assert entries[0].size == 5


def test_walk_does_not_follow_symlink(tmp_path: Path) -> None:
    ops = LocalFileOps()
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"x")
    link_dir = tmp_path / "inner"
    link_dir.mkdir()
    try:
        os.symlink(outside, link_dir / "link")
    except OSError:
        pytest.skip("symlink unsupported")
    secret = tmp_path / "secret.bin"
    secret.write_bytes(b"y")
    entries = ops.walk_files(link_dir)
    assert any(e.is_symlink for e in entries)
    assert all(e.path != secret for e in entries)


def test_zip_contains_manifest_and_member(tmp_path: Path) -> None:
    ops = LocalFileOps()
    src = tmp_path / "a.txt"
    src.write_text("hi", encoding="utf-8")
    archive = tmp_path / "out.zip"
    ops.create_zip(
        archive,
        [ZipMember(src, "a.txt", src.stat().st_size)],
        {"app": "DeskKit"},
    )
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        assert "deskkit-manifest.json" in names
        assert "a.txt" in names
    assert not archive.with_suffix(".zip.partial").exists()


def test_zip_cleans_partial_on_bad_arcname(tmp_path: Path) -> None:
    ops = LocalFileOps()
    src = tmp_path / "a.txt"
    src.write_text("x", encoding="utf-8")
    archive = tmp_path / "out.zip"
    with pytest.raises(Exception):
        ops.create_zip(
            archive,
            [ZipMember(src, "../x", 1)],
            {},
        )
    assert not archive.with_suffix(".zip.partial").exists()


def test_delete_and_empty_dir(tmp_path: Path) -> None:
    ops = LocalFileOps()
    f = tmp_path / "a.txt"
    f.write_text("a", encoding="utf-8")
    sub = tmp_path / "sub"
    sub.mkdir()
    g = sub / "b.txt"
    g.write_text("b", encoding="utf-8")
    ops.delete_file(g)
    assert ops.remove_dir_if_empty(sub)
    assert sub.exists() is False
    assert not ops.remove_dir_if_empty(tmp_path)
