from __future__ import annotations

from deskkit.models import (
    BackupPreview,
    BackupResult,
)
from deskkit.text import (
    backup_result_text,
    output_tail,
    report_summary_text,
    schedule_preview_text,
    startup_list_text,
)
from tests.test_report import _snapshot


def test_backup_dry_run_text() -> None:
    preview = BackupPreview((), "/d", 0, 0, "a.zip", (), (), ())
    result = BackupResult(preview, None, 0, (), True, False)
    assert "Режим просмотра" in backup_result_text(result)


def test_startup_list_empty() -> None:
    assert startup_list_text(()) == "Автозагрузка пуста.\n"


def test_schedule_preview_has_task_name() -> None:
    text = schedule_preview_text(["deskkit", "backup", "run", "--yes"])
    assert "\\DeskKit\\Backup" in text


def test_output_tail_last_lines() -> None:
    assert output_tail("a\nb\nc", "", 2) == "b\nc"


def test_install_report_dry_run() -> None:
    from deskkit.models import InstallReport
    from deskkit.text import install_report_text

    report = InstallReport((), dry_run=True, cancelled=False)
    assert "Режим просмотра" in install_report_text(report)


def test_install_report_cancelled() -> None:
    from deskkit.models import InstallItemResult, InstallReport, InstallStatus

    report = InstallReport(
        (InstallItemResult("a", "A", InstallStatus.SUCCESS, 0, ""),),
        dry_run=False,
        cancelled=True,
    )
    from deskkit.text import install_report_text

    assert install_report_text(report).endswith("Остановлено.\n")


def test_report_summary_disk_unavailable() -> None:
    from dataclasses import replace

    snap = replace(
        _snapshot(),
        disks=(_snapshot().disks[0].__class__("C:", "C:\\", "NTFS", 0, 0, 0, False),),
    )
    text = report_summary_text(snap)
    assert "нет данных" in text
