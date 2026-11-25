from __future__ import annotations

from pathlib import Path

from deskkit.cancel import CancellationToken
from deskkit.models import CleanupTargetId, InstallScope, ScheduleSettings
from deskkit.ui.presenters import (
    BackupPresenter,
    CleanupPresenter,
    InstallPresenter,
    LogsPresenter,
    ProfilePresenter,
    ReportPresenter,
    StartupPresenter,
)


def test_presenters_smoke(context, tmp_path: Path) -> None:
    targets = (CleanupTargetId.USER_TEMP,)
    cleanup = CleanupPresenter(context)
    preview = cleanup.preview(targets)
    cleanup.confirmation(preview)
    StartupPresenter(context).entries()
    ReportPresenter(context).collect()
    LogsPresenter(context).text()
    profile = ProfilePresenter(context)
    profile.text()
    profile.path()
    from deskkit.models import CommandResult

    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    backup = BackupPresenter(context)
    backup.schedule_status()
    backup.schedule_text(ScheduleSettings(False, "weekly", "MON", "09:00"))
    inst = context.catalog.ids_for_preset("home")[:1]
    ip = InstallPresenter(context)
    install_preview = ip.preview(inst, InstallScope.USER)
    ip.confirmation(install_preview)
    ip.execute(inst, InstallScope.USER, dry_run=True, confirmed=False, cancel=CancellationToken())
    dest = tmp_path / "dest"
    dest.mkdir()
    src = tmp_path / "src"
    src.mkdir()
    bp = BackupPresenter(context)
    backup_preview = bp.preview([src], dest, 5)
    bp.confirmation(backup_preview)
