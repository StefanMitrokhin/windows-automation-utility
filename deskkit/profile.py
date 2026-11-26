from __future__ import annotations

import json
import os
import re
from collections.abc import Mapping
from pathlib import Path

from deskkit.catalog import Catalog
from deskkit.errors import ProfileVersionError, ValidationError
from deskkit.models import (
    BackupSettings,
    CleanupSettings,
    CleanupTargetId,
    InstallScope,
    InstallSettings,
    Profile,
    ReportSettings,
    ScheduleSettings,
)

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")
_WEEKDAYS = frozenset({"MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"})


def default_profile() -> Profile:
    return Profile(
        schema_version=1,
        install=InstallSettings(package_ids=(), scope=InstallScope.USER),
        cleanup=CleanupSettings(
            targets=(
                CleanupTargetId.USER_TEMP,
                CleanupTargetId.RECYCLE_BIN,
                CleanupTargetId.CHROME_CACHE,
                CleanupTargetId.EDGE_CACHE,
                CleanupTargetId.FIREFOX_CACHE,
            )
        ),
        backup=BackupSettings(
            sources=(),
            destination=None,
            keep_last=5,
            schedule=ScheduleSettings(
                enabled=False, frequency="weekly", weekday="MON", time="09:00"
            ),
        ),
        report=ReportSettings(format="html", last_directory=None),
    )


def profile_to_mapping(profile: Profile) -> dict[str, object]:
    return {
        "schema_version": profile.schema_version,
        "install": {
            "package_ids": list(profile.install.package_ids),
            "scope": profile.install.scope.value,
        },
        "cleanup": {
            "targets": [t.value for t in profile.cleanup.targets],
        },
        "backup": {
            "sources": list(profile.backup.sources),
            "destination": profile.backup.destination,
            "keep_last": profile.backup.keep_last,
            "schedule": {
                "enabled": profile.backup.schedule.enabled,
                "frequency": profile.backup.schedule.frequency,
                "weekday": profile.backup.schedule.weekday,
                "time": profile.backup.schedule.time,
            },
        },
        "report": {
            "format": profile.report.format,
            "last_directory": profile.report.last_directory,
        },
    }


def profile_from_mapping(data: Mapping[str, object]) -> Profile:
    defaults = default_profile()
    schema = data.get("schema_version")
    if schema is None:
        raise ValidationError("Версия профиля не поддерживается.")
    if schema != 1:
        raise ProfileVersionError("Версия профиля не поддерживается.")

    install_raw = data.get("install", {})
    install: InstallSettings = defaults.install
    if isinstance(install_raw, Mapping):
        ids_raw = install_raw.get("package_ids", [])
        scope_raw = install_raw.get("scope", defaults.install.scope.value)
        if isinstance(ids_raw, list):
            catalog = Catalog()
            package_ids = tuple(str(x) for x in ids_raw)
            for pid in package_ids:
                catalog.get(pid)
            if scope_raw == "user":
                scope = InstallScope.USER
            elif scope_raw == "auto":
                scope = InstallScope.AUTO
            else:
                raise ValidationError("Неизвестная область установки.")
            install = InstallSettings(package_ids=package_ids, scope=scope)

    cleanup_raw = data.get("cleanup", {})
    cleanup: CleanupSettings = defaults.cleanup
    if isinstance(cleanup_raw, Mapping):
        targets_raw = cleanup_raw.get("targets", [])
        if isinstance(targets_raw, list):
            targets: list[CleanupTargetId] = []
            for item in targets_raw:
                try:
                    targets.append(CleanupTargetId(str(item)))
                except ValueError:
                    raise ValidationError("Неизвестная цель очистки.") from None
            cleanup = CleanupSettings(targets=tuple(targets))

    backup_raw = data.get("backup", {})
    backup: BackupSettings = defaults.backup
    if isinstance(backup_raw, Mapping):
        sources_raw = backup_raw.get("sources", defaults.backup.sources)
        sources = tuple(str(x) for x in sources_raw) if isinstance(sources_raw, list) else ()
        destination = backup_raw.get("destination", defaults.backup.destination)
        if destination is not None:
            destination = str(destination)
        keep_last = backup_raw.get("keep_last", defaults.backup.keep_last)
        if not isinstance(keep_last, int) or keep_last < 1 or keep_last > 30:
            raise ValidationError("Хранить можно от 1 до 30 архивов.")
        sched_raw = backup_raw.get("schedule", {})
        schedule = defaults.backup.schedule
        if isinstance(sched_raw, Mapping):
            enabled = bool(sched_raw.get("enabled", schedule.enabled))
            frequency = str(sched_raw.get("frequency", schedule.frequency))
            weekday = str(sched_raw.get("weekday", schedule.weekday))
            time = str(sched_raw.get("time", schedule.time))
            if frequency not in ("daily", "weekly"):
                raise ValidationError("Неизвестная периодичность.")
            if weekday not in _WEEKDAYS:
                raise ValidationError("Неизвестный день недели.")
            if not _TIME_RE.match(time):
                raise ValidationError("Время задаётся как ЧЧ:ММ.")
            schedule = ScheduleSettings(
                enabled=enabled, frequency=frequency, weekday=weekday, time=time
            )
        backup = BackupSettings(
            sources=sources,
            destination=destination,
            keep_last=keep_last,
            schedule=schedule,
        )

    report_raw = data.get("report", {})
    report: ReportSettings = defaults.report
    if isinstance(report_raw, Mapping):
        fmt = str(report_raw.get("format", defaults.report.format))
        if fmt not in ("html", "xlsx"):
            raise ValidationError("Неизвестный формат отчёта.")
        last_dir = report_raw.get("last_directory", defaults.report.last_directory)
        if last_dir is not None:
            last_dir = str(last_dir)
        report = ReportSettings(format=fmt, last_directory=last_dir)

    return Profile(
        schema_version=1,
        install=install,
        cleanup=cleanup,
        backup=backup,
        report=report,
    )


class ProfileStore:
    def __init__(self, path: Path) -> None:
        self._path = path

    @property
    def path(self) -> Path:
        return self._path

    def load(self) -> Profile:
        if not self._path.is_file():
            return default_profile()
        try:
            raw_text = self._path.read_text(encoding="utf-8")
            data = json.loads(raw_text)
        except (OSError, json.JSONDecodeError):
            raise ValidationError("Файл профиля повреждён.") from None
        if not isinstance(data, dict):
            raise ValidationError("Файл профиля повреждён.")
        return profile_from_mapping(data)

    def save(self, profile: Profile) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self._path.with_name(self._path.name + ".tmp")
        payload = json.dumps(profile_to_mapping(profile), ensure_ascii=False, indent=2) + "\n"
        try:
            with tmp_path.open("w", encoding="utf-8") as handle:
                handle.write(payload)
                handle.flush()
                os.fsync(handle.fileno())
            os.replace(tmp_path, self._path)
        except OSError:
            if tmp_path.exists():
                tmp_path.unlink(missing_ok=True)
            raise
