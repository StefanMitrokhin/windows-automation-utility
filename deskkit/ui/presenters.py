from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from deskkit import __version__
from deskkit.app_context import Context
from deskkit.cancel import CancellationToken
from deskkit.errors import ConfirmationRequired, ValidationError
from deskkit.logging_setup import read_log_tail
from deskkit.models import (
    BackupPreview,
    BackupResult,
    CleanupPreview,
    CleanupResult,
    ElevationResult,
    InstallPreview,
    InstallReport,
    InstallScope,
    Package,
    Profile,
    ScheduleSettings,
    ScheduleStatus,
    StartupEntry,
    SystemSnapshot,
)
from deskkit.profile import default_profile, profile_from_mapping
from deskkit.text import (
    backup_preview_text,
    cleanup_preview_text,
    install_preview_text,
    profile_summary_text,
    schedule_preview_text,
    startup_action_text,
)
from deskkit.ui.strings import CONFIRM_LEAD


def can_execute(view_only: bool) -> bool:
    return not view_only


@dataclass(frozen=True)
class HomeStatus:
    winget_found: bool
    winget_path: str
    profile_exists: bool
    schedule_exists: bool
    schedule_enabled: bool
    is_admin: bool
    version: str
    last_log_line: str


class HomePresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def status(self) -> HomeStatus:
        winget = self._context.installer.winget_path() or ""
        schedule = self._context.schedule.status()
        tail = read_log_tail(self._context.paths.log_path).splitlines()
        last = next((line for line in reversed(tail) if line.strip()), "Журнал пока пуст.")
        return HomeStatus(
            winget_found=bool(winget),
            winget_path=winget,
            profile_exists=self._context.paths.profile_path.is_file(),
            schedule_exists=schedule.exists,
            schedule_enabled=schedule.enabled,
            is_admin=self._context.admin.is_admin(),
            version=__version__,
            last_log_line=last,
        )


class InstallPresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def packages(self) -> tuple[Package, ...]:
        return self._context.catalog.packages()

    def preview(self, package_ids: Sequence[str], scope: InstallScope) -> InstallPreview:
        return self._context.installer.preview(package_ids, scope)

    def execute(
        self,
        package_ids: Sequence[str],
        scope: InstallScope,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> InstallReport:
        return self._context.installer.apply(
            package_ids, scope, dry_run=dry_run, confirmed=confirmed, cancel=cancel
        )

    def confirmation(self, preview: InstallPreview) -> str:
        body = install_preview_text(preview, include_footer=False)
        return CONFIRM_LEAD + "\n\n" + body


class CleanupPresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def preview(self, targets: Sequence) -> CleanupPreview:
        return self._context.cleanup.preview(targets)

    def execute(
        self,
        targets: Sequence,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> CleanupResult:
        return self._context.cleanup.apply(
            targets, dry_run=dry_run, confirmed=confirmed, cancel=cancel
        )

    def confirmation(self, preview: CleanupPreview) -> str:
        body = cleanup_preview_text(preview, include_footer=False)
        return CONFIRM_LEAD + "\n\n" + body


class ReportPresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def collect(self) -> SystemSnapshot:
        return self._context.report.collect()

    def summary(self, snapshot: SystemSnapshot) -> str:
        from deskkit.text import report_summary_text

        return report_summary_text(snapshot)

    def save_html(self, snapshot: SystemSnapshot, path: Path) -> None:
        self._context.report.write_html(snapshot, path)

    def save_xlsx(self, snapshot: SystemSnapshot, path: Path) -> None:
        self._context.report.write_xlsx(snapshot, path)


class StartupPresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def entries(self) -> tuple[StartupEntry, ...]:
        return self._context.startup.list_entries()

    def confirmation(self, entry: StartupEntry, action: str) -> str:
        return CONFIRM_LEAD + "\n\n" + startup_action_text(entry, action)

    def disable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry:
        return self._context.startup.disable(entry_id, dry_run=dry_run, confirmed=confirmed)

    def enable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry:
        return self._context.startup.enable(entry_id, dry_run=dry_run, confirmed=confirmed)

    def elevate(self) -> ElevationResult:
        return self._context.admin.relaunch_elevated([])


class BackupPresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def preview(self, sources: Sequence[Path], destination: Path, keep_last: int) -> BackupPreview:
        return self._context.backup.preview(sources, destination, keep_last)

    def execute(
        self,
        sources: Sequence[Path],
        destination: Path,
        keep_last: int,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> BackupResult:
        return self._context.backup.apply(
            sources, destination, keep_last, dry_run=dry_run, confirmed=confirmed, cancel=cancel
        )

    def confirmation(self, preview: BackupPreview) -> str:
        return CONFIRM_LEAD + "\n\n" + backup_preview_text(preview, include_footer=False)

    def schedule_status(self) -> ScheduleStatus:
        return self._context.schedule.status()

    def schedule_text(self, settings: ScheduleSettings) -> str:
        return schedule_preview_text(self._context.schedule.create_argv(settings))

    def save_schedule(self, settings: ScheduleSettings, *, confirmed: bool) -> ScheduleStatus:
        if not settings.enabled:
            self._context.schedule.remove(confirmed=confirmed)
            return self.schedule_status()
        return self._context.schedule.apply(settings, confirmed=confirmed)

    def remove_schedule(self, *, confirmed: bool) -> None:
        self._context.schedule.remove(confirmed=confirmed)


class ProfilePresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def path(self) -> Path:
        return self._context.paths.profile_path

    def load(self) -> Profile:
        return self._context.profile_store.load()

    def text(self) -> str:
        return profile_summary_text(self.load())

    def init_default(self) -> Profile:
        if self._context.paths.profile_path.is_file():
            raise ValidationError("Профиль уже есть.")
        profile = default_profile()
        self._context.profile_store.save(profile)
        return profile

    def export_to(self, path: Path) -> None:
        """Overwrite if the path exists (OS save dialog already asked the user)."""
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(profile_summary_text(self.load()), encoding="utf-8")

    def parse_file(self, path: Path) -> Profile:
        import json

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise ValidationError("Файл профиля повреждён.") from exc
        return profile_from_mapping(data)

    def import_from(self, path: Path, *, confirmed: bool) -> Profile:
        profile = self.parse_file(path)
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")
        self._context.profile_store.save(profile)
        return profile

    def apply_install(
        self, *, dry_run: bool, confirmed: bool, cancel: CancellationToken
    ) -> InstallReport:
        profile = self.load()
        return self._context.installer.apply(
            profile.install.package_ids,
            profile.install.scope,
            dry_run=dry_run,
            confirmed=confirmed,
            cancel=cancel,
        )


class LogsPresenter:
    def __init__(self, context: Context) -> None:
        self._context = context

    def text(self) -> str:
        return read_log_tail(self._context.paths.log_path)

    def directory(self) -> Path:
        return self._context.paths.log_dir
