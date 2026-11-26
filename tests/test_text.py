from __future__ import annotations

import pytest

from deskkit.models import (
    BackupPreview,
    BackupResult,
    CleanupPreview,
    CleanupResult,
    CleanupTargetId,
    CleanupTargetPreview,
    InstallItemResult,
    InstallPreview,
    InstallReport,
    InstallScope,
    InstallStatus,
    StartupEntry,
    StartupSource,
)
from deskkit.text import (
    cleanup_preview_text,
    confirmation_footer,
    format_bytes,
    install_preview_text,
    install_report_text,
    install_scope_label,
)


def test_format_bytes_table() -> None:
    assert format_bytes(0) == "0 Б"
    assert format_bytes(1023) == "1023 Б"
    assert format_bytes(1024) == "1,0 КБ"
    assert format_bytes(1536) == "1,5 КБ"
    assert format_bytes(1048576) == "1,0 МБ"
    assert format_bytes(1073741824) == "1,0 ГБ"


def test_format_bytes_negative() -> None:
    with pytest.raises(ValueError):
        format_bytes(-1)


def test_install_preview_text_exact() -> None:
    preview = InstallPreview(
        package_ids=("7zip.7zip", "VideoLAN.VLC"),
        names=("7-Zip", "VLC"),
        scope=InstallScope.USER,
        winget_found=True,
    )
    expected = (
        "Будет установлено: 2\n"
        "Область: для текущего пользователя\n"
        "1. 7-Zip (7zip.7zip)\n"
        "2. VLC (VideoLAN.VLC)\n"
        "Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено.\n"
    )
    assert install_preview_text(preview, include_footer=True) == expected


def test_install_preview_missing_winget() -> None:
    preview = InstallPreview((), (), InstallScope.USER, winget_found=False)
    text = install_preview_text(preview, include_footer=False)
    assert text.startswith("winget не найден. Установка не начнётся.\n")


def test_confirmation_footer_exact() -> None:
    assert confirmation_footer() == "Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено."


def test_cleanup_preview_text_exact() -> None:
    preview = CleanupPreview(
        targets=(
            CleanupTargetPreview(
                target=CleanupTargetId.USER_TEMP,
                roots=(r"C:\Temp",),
                file_count=3,
                byte_count=1536,
                skipped_recent=0,
                skipped_links=0,
                unreadable=0,
                warnings=(),
                absent=False,
            ),
        )
    )
    text = """К очистке: 1,5 КБ в 3 файлах
Временные файлы пользователя: 3 файлов, 1,5 КБ
Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено.
"""
    assert cleanup_preview_text(preview, include_footer=True) == text


def test_install_report_text_exact() -> None:
    report = InstallReport(
        items=(
            InstallItemResult("a", "7-Zip", InstallStatus.SKIPPED_INSTALLED, 0, ""),
            InstallItemResult("b", "VLC", InstallStatus.SUCCESS, 0, ""),
        ),
        dry_run=False,
        cancelled=False,
    )
    expected = (
        "[1/2] 7-Zip — уже установлен, пропуск\n"
        "[2/2] VLC — установлено\n"
        "Готово: установлено 1, пропущено 1, ошибок 0\n"
    )
    assert install_report_text(report) == expected


def test_scope_labels() -> None:
    from deskkit.text import (
        backup_preview_text,
        backup_result_text,
        cleanup_result_text,
        output_tail,
        schedule_preview_text,
        startup_action_text,
        startup_list_text,
        startup_source_label,
    )

    assert install_scope_label(InstallScope.USER) == "для текущего пользователя"
    assert install_scope_label(InstallScope.AUTO) == "как решит winget"
    entry = StartupEntry("hkcu|A", StartupSource.HKCU_RUN, "A", "cmd", True, False)
    assert startup_source_label(StartupSource.HKCU_RUN)
    assert startup_list_text((entry,))
    assert startup_action_text(entry, "disable")
    bprev = BackupPreview(
        sources=("/src",),
        destination="/dest",
        file_count=1,
        byte_count=2,
        archive_name="arch.zip",
        rotate_names=(),
        skipped=(),
        warnings=(),
    )
    assert backup_preview_text(bprev, include_footer=True)
    assert backup_result_text(
        BackupResult(
            preview=bprev,
            archive_path="/dest/arch.zip",
            written_files=1,
            skipped=(),
            dry_run=False,
            cancelled=False,
        )
    )
    assert schedule_preview_text(["deskkit-cli", "backup", "run", "--yes"])
    cprev = CleanupPreview(targets=())
    assert cleanup_result_text(
        CleanupResult(
            preview=cprev,
            deleted_files=0,
            freed_bytes=0,
            skipped_locked=0,
            errors=(),
            dry_run=False,
            cancelled=False,
        )
    )
    assert output_tail("line\n", "err\n", lines=1)
