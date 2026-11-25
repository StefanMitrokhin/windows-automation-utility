from __future__ import annotations

import os
from dataclasses import replace
from datetime import timedelta
from pathlib import Path

import pytest

from deskkit.cancel import CancellationToken
from deskkit.errors import ConfirmationRequired, ValidationError
from deskkit.models import CleanupTargetId
from deskkit.platform.files import LocalFileOps


def _service(context, tmp_path: Path):
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    return context.cleanup, temp


def test_preview_sums_files(context, tmp_path: Path) -> None:
    cleanup, temp = _service(context, tmp_path)
    old = temp / "old.bin"
    old.write_bytes(b"abc" * 100)
    os.utime(old, (0, 0))
    context.clock.moment = context.clock.now()
    preview = cleanup.preview([CleanupTargetId.USER_TEMP])
    assert preview.total_files == 1
    assert preview.total_bytes > 0


def test_skips_recent_temp_only(context, tmp_path: Path) -> None:
    cleanup, temp = _service(context, tmp_path)
    recent = temp / "new.bin"
    recent.write_bytes(b"x")
    chrome = tmp_path / "browsers" / "chrome" / "User Data" / "Default" / "Cache"
    chrome.mkdir(parents=True)
    (chrome / "c.bin").write_bytes(b"y")
    preview = cleanup.preview([CleanupTargetId.USER_TEMP, CleanupTargetId.CHROME_CACHE])
    user = next(t for t in preview.targets if t.target == CleanupTargetId.USER_TEMP)
    chrome_t = next(t for t in preview.targets if t.target == CleanupTargetId.CHROME_CACHE)
    assert user.skipped_recent == 1
    assert chrome_t.file_count == 1


def test_does_not_include_cookies(context, tmp_path: Path) -> None:
    root = tmp_path / "browsers" / "chrome" / "User Data" / "Default"
    root.mkdir(parents=True)
    (root / "Cookies").write_bytes(b"x")
    cache = root / "Cache"
    cache.mkdir()
    (cache / "a.bin").write_bytes(b"y")
    preview = context.cleanup.preview([CleanupTargetId.CHROME_CACHE])
    assert preview.total_files == 1


def test_absent_browser(context) -> None:
    preview = context.cleanup.preview([CleanupTargetId.CHROME_CACHE])
    assert preview.targets[0].absent


def test_symlink_not_counted(context, tmp_path: Path) -> None:
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    outside = tmp_path / "outside.bin"
    outside.write_bytes(b"z")
    try:
        os.symlink(outside, temp / "link.bin")
    except OSError:
        pytest.skip("symlink unsupported")
    preview = context.cleanup.preview([CleanupTargetId.USER_TEMP])
    assert preview.targets[0].skipped_links >= 1


def test_apply_deletes_and_keeps_root(context, tmp_path: Path) -> None:
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    f = temp / "old.bin"
    f.write_bytes(b"x")
    os.utime(f, (0, 0))
    context.clock.moment += timedelta(hours=48)
    result = context.cleanup.apply(
        [CleanupTargetId.USER_TEMP], dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert not f.exists()
    assert temp.exists()
    assert result.deleted_files == 1


def test_dry_run_deletes_nothing(context, tmp_path: Path) -> None:
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    f = temp / "a.bin"
    f.write_bytes(b"x")
    context.cleanup.apply(
        [CleanupTargetId.USER_TEMP], dry_run=True, confirmed=False, cancel=CancellationToken()
    )
    assert f.exists()


def test_confirmation_required(context, tmp_path: Path) -> None:
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    f = temp / "a.bin"
    f.write_bytes(b"x")
    with pytest.raises(ConfirmationRequired):
        context.cleanup.apply(
            [CleanupTargetId.USER_TEMP], dry_run=False, confirmed=False, cancel=CancellationToken()
        )
    assert f.exists()


class LockedOps(LocalFileOps):
    def __init__(self, locked: Path) -> None:
        super().__init__()
        self._locked = locked

    def delete_file(self, path: Path) -> None:
        if path == self._locked:
            raise PermissionError("locked")
        super().delete_file(path)


def test_locked_file_skipped(context, tmp_path: Path) -> None:
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    a, b = temp / "a.bin", temp / "b.bin"
    a.write_bytes(b"a")
    b.write_bytes(b"b")
    os.utime(a, (0, 0))
    os.utime(b, (0, 0))
    from deskkit.services.cleanup import CleanupService

    ctx = replace(
        context,
        cleanup=CleanupService(
            context.cleanup._roots,
            LockedOps(a),
            context.cleanup._recycle,
            context.cleanup._clock,
        ),
    )
    result = ctx.cleanup.apply(
        [CleanupTargetId.USER_TEMP], dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert result.skipped_locked == 1
    assert a.exists()
    assert not b.exists()


def test_cancel_before_second_file(context, tmp_path: Path) -> None:
    temp = tmp_path / "Temp"
    temp.mkdir(parents=True, exist_ok=True)
    (temp / "a.bin").write_bytes(b"a")
    (temp / "b.bin").write_bytes(b"b")
    os.utime(temp / "a.bin", (0, 0))
    os.utime(temp / "b.bin", (0, 0))
    token = CancellationToken()

    def on_delete():
        token.cancel()

    # delete happens in apply loop - cancel after first file via patched delete
    original = context.cleanup._files.delete_file

    def wrapped(path):
        on_delete()
        original(path)

    context.cleanup._files.delete_file = wrapped  # type: ignore[method-assign]
    result = context.cleanup.apply(  # type: ignore[attr-defined]
        [CleanupTargetId.USER_TEMP], dry_run=False, confirmed=True, cancel=token
    )
    assert result.cancelled
    assert not (temp / "b.bin").exists()


def test_recycle_only_when_selected(context) -> None:
    context.cleanup.apply(
        [CleanupTargetId.USER_TEMP], dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert not context.cleanup._recycle.emptied
    context.cleanup.apply(
        [CleanupTargetId.RECYCLE_BIN], dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert len(context.cleanup._recycle.emptied) == 1


def test_recycle_error_is_warning(context) -> None:
    context.cleanup._recycle.fail_query = True
    preview = context.cleanup.preview([CleanupTargetId.RECYCLE_BIN])
    assert preview.targets[0].warnings


def test_empty_targets(context) -> None:
    with pytest.raises(ValidationError):
        context.cleanup.preview(())
