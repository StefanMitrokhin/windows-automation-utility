from __future__ import annotations

import json
import os
import zipfile
from pathlib import Path

import pytest

from deskkit.cancel import CancellationToken
from deskkit.errors import ConfirmationRequired, ValidationError
from deskkit.models import FileEntry
from deskkit.platform.files import LocalFileOps
from deskkit.services.backup import BackupService
from tests.fakes import FakeClock


def test_preview_counts(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a").write_bytes(b"a" * 10)
    (src / "b").write_bytes(b"b" * 5)
    svc = BackupService(LocalFileOps(), FakeClock())
    preview = svc.preview([src], tmp_path / "dest", 5)
    assert preview.file_count == 2
    assert preview.byte_count == 15
    assert preview.archive_name == "DeskKit-backup-20260115-090000.zip"


def test_rejects_drive_root() -> None:
    with pytest.raises(ValidationError) as exc:
        BackupService(LocalFileOps(), FakeClock()).preview([Path("C:\\")], Path("/d"), 5)
    assert str(exc.value).startswith("Эту папку копировать нельзя:")


def test_rejects_windows_directory() -> None:
    with pytest.raises(ValidationError) as exc:
        BackupService(LocalFileOps(), FakeClock()).preview(
            [Path(r"C:\Windows\Temp")], Path("/d"), 5
        )
    assert str(exc.value).startswith("Эту папку копировать нельзя:")


def test_rejects_overlap(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    with pytest.raises(ValidationError) as exc:
        BackupService(LocalFileOps(), FakeClock()).preview([src], src / "nested", 5)
    assert str(exc.value) == "Папка назначения пересекается с копируемой."


def test_insufficient_space(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "f").write_bytes(b"x" * 100)
    dest = tmp_path / "dest"
    ops = LocalFileOps()
    monkeypatch.setattr(ops, "disk_free", lambda _p: 10)
    svc = BackupService(ops, FakeClock())
    with pytest.raises(ValidationError) as exc:
        svc.preview([src], dest, 5)
    assert str(exc.value) == "Недостаточно места для копии."


def test_apply_zip_and_manifest(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "f").write_bytes(b"x")
    dest = tmp_path / "dest"
    svc = BackupService(LocalFileOps(), FakeClock())
    result = svc.apply([src], dest, 5, dry_run=False, confirmed=True, cancel=CancellationToken())
    archive = Path(result.archive_path or "")
    assert archive.is_file()
    with zipfile.ZipFile(archive) as zf:
        manifest = json.loads(zf.read("deskkit-manifest.json"))
        assert manifest["app"] == "DeskKit"
        assert any(n.startswith("source-1/") for n in zf.namelist())


def test_two_sources_indexed(tmp_path: Path) -> None:
    a, b = tmp_path / "a", tmp_path / "b"
    a.mkdir()
    b.mkdir()
    (a / "f").write_bytes(b"a")
    (b / "g").write_bytes(b"b")
    svc = BackupService(LocalFileOps(), FakeClock())
    svc.apply(
        [a, b], tmp_path / "dest", 5, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    archive = next((tmp_path / "dest").glob("DeskKit-backup-*.zip"))
    with zipfile.ZipFile(archive) as zf:
        names = zf.namelist()
        assert any(n.startswith("source-2/") for n in names)


def test_unreadable_recorded(tmp_path: Path) -> None:
    class Ops(LocalFileOps):
        def walk_files(self, root: Path):
            return (
                FileEntry(
                    path=root / "bad",
                    size=0,
                    modified_at=FakeClock().now(),
                    is_symlink=False,
                    is_reparse=False,
                    unreadable=True,
                    error="x",
                ),
            )

    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "dest"
    svc = BackupService(Ops(), FakeClock())
    svc.apply([src], dest, 5, dry_run=False, confirmed=True, cancel=CancellationToken())
    archive = next(dest.glob("DeskKit-backup-*.zip"))
    with zipfile.ZipFile(archive) as zf:
        manifest = json.loads(zf.read("deskkit-manifest.json"))
        assert manifest["skipped"]


def test_symlink_skipped(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    try:
        os.symlink(tmp_path / "outside", src / "link")
    except OSError:
        pytest.skip("symlink unsupported")
    svc = BackupService(LocalFileOps(), FakeClock())
    result = svc.apply(
        [src], tmp_path / "dest", 5, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert result.written_files == 0


def test_rotation_only_matching(tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    (dest / "notes.zip").write_bytes(b"x")
    (dest / "DeskKit-backup-20260101-000000.zip").write_bytes(b"old")
    src = tmp_path / "src"
    src.mkdir()
    (src / "f").write_bytes(b"x")
    svc = BackupService(LocalFileOps(), FakeClock())
    svc.apply([src], dest, 1, dry_run=False, confirmed=True, cancel=CancellationToken())
    assert (dest / "notes.zip").exists()
    assert not (dest / "DeskKit-backup-20260101-000000.zip").exists()


def test_dry_run_creates_nothing(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "dest"
    BackupService(LocalFileOps(), FakeClock()).apply(
        [src], dest, 5, dry_run=True, confirmed=False, cancel=CancellationToken()
    )
    assert not dest.exists()


def test_confirmation_required(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "dest"
    with pytest.raises(ConfirmationRequired):
        BackupService(LocalFileOps(), FakeClock()).apply(
            [src], dest, 5, dry_run=False, confirmed=False, cancel=CancellationToken()
        )
    assert not dest.exists()


def test_missing_source(tmp_path: Path) -> None:
    with pytest.raises(ValidationError) as exc:
        BackupService(LocalFileOps(), FakeClock()).preview(
            [tmp_path / "missing"], tmp_path / "d", 5
        )
    assert str(exc.value).startswith("Папка не найдена:")


def test_too_many_sources(tmp_path: Path) -> None:
    sources = [tmp_path / str(i) for i in range(21)]
    for s in sources:
        s.mkdir()
    with pytest.raises(ValidationError) as exc:
        BackupService(LocalFileOps(), FakeClock()).preview(sources, tmp_path / "d", 5)
    assert str(exc.value) == "Можно выбрать не больше 20 папок."


def test_cancel_during_walk(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    (src / "a").write_bytes(b"a")
    token = CancellationToken()
    token.cancel()
    result = BackupService(LocalFileOps(), FakeClock()).apply(
        [src], tmp_path / "dest", 5, dry_run=False, confirmed=True, cancel=token
    )
    assert result.cancelled
    assert not list((tmp_path / "dest").glob("*.zip")) if (tmp_path / "dest").exists() else True
