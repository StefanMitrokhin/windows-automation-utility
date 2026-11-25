from __future__ import annotations

import enum
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


class InstallScope(enum.Enum):
    USER = "user"
    AUTO = "auto"


class InstallStatus(enum.Enum):
    SUCCESS = "success"
    SKIPPED_INSTALLED = "skipped_installed"
    ADMIN_REQUIRED = "admin_required"
    FAILED = "failed"


class CleanupTargetId(enum.Enum):
    USER_TEMP = "user_temp"
    WINDOWS_TEMP = "windows_temp"
    RECYCLE_BIN = "recycle_bin"
    CHROME_CACHE = "chrome_cache"
    EDGE_CACHE = "edge_cache"
    FIREFOX_CACHE = "firefox_cache"


class Hive(enum.Enum):
    HKCU = "HKCU"
    HKLM = "HKLM"


class StartupSource(enum.Enum):
    HKCU_RUN = "hkcu_run"
    HKLM_RUN = "hklm_run"
    USER_STARTUP = "user_startup"
    COMMON_STARTUP = "common_startup"


class RegKind(enum.Enum):
    SZ = "sz"
    EXPAND_SZ = "expand_sz"
    OTHER = "other"


@dataclass(frozen=True)
class Package:
    id: str
    name: str
    summary: str
    presets: tuple[str, ...]


@dataclass(frozen=True)
class CommandResult:
    args: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    cancelled: bool


@dataclass(frozen=True)
class InstallItemResult:
    package_id: str
    name: str
    status: InstallStatus
    exit_code: int | None
    message: str


@dataclass(frozen=True)
class InstallPreview:
    package_ids: tuple[str, ...]
    names: tuple[str, ...]
    scope: InstallScope
    winget_found: bool


@dataclass(frozen=True)
class InstallReport:
    items: tuple[InstallItemResult, ...]
    dry_run: bool
    cancelled: bool


@dataclass(frozen=True)
class FileEntry:
    path: Path
    size: int
    modified_at: datetime
    is_symlink: bool
    is_reparse: bool
    unreadable: bool
    error: str | None


@dataclass(frozen=True)
class CleanupTargetPreview:
    target: CleanupTargetId
    roots: tuple[str, ...]
    file_count: int
    byte_count: int
    skipped_recent: int
    skipped_links: int
    unreadable: int
    warnings: tuple[str, ...]
    absent: bool


@dataclass(frozen=True)
class CleanupPreview:
    targets: tuple[CleanupTargetPreview, ...]

    @property
    def total_bytes(self) -> int:
        return sum(t.byte_count for t in self.targets)

    @property
    def total_files(self) -> int:
        return sum(t.file_count for t in self.targets)


@dataclass(frozen=True)
class CleanupResult:
    preview: CleanupPreview
    deleted_files: int
    freed_bytes: int
    skipped_locked: int
    errors: tuple[str, ...]
    dry_run: bool
    cancelled: bool


@dataclass(frozen=True)
class DiskInfo:
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    available: bool


@dataclass(frozen=True)
class SoftwareEntry:
    name: str
    version: str
    publisher: str
    install_date: str


@dataclass(frozen=True)
class SystemSnapshot:
    collected_at: datetime
    hostname: str
    os_name: str
    os_version: str
    os_build: str
    machine: str
    cpu_model: str
    cpu_physical: int
    cpu_logical: int
    cpu_freq_mhz: float | None
    ram_total_bytes: int
    ram_available_bytes: int
    disks: tuple[DiskInfo, ...]
    software: tuple[SoftwareEntry, ...]


@dataclass(frozen=True)
class RegValue:
    name: str
    data: str
    kind: RegKind


@dataclass(frozen=True)
class StartupEntry:
    id: str
    source: StartupSource
    name: str
    command: str
    enabled: bool
    needs_admin: bool


@dataclass(frozen=True)
class ScheduleSettings:
    enabled: bool
    frequency: str
    weekday: str
    time: str


@dataclass(frozen=True)
class BackupPreview:
    sources: tuple[str, ...]
    destination: str
    file_count: int
    byte_count: int
    archive_name: str
    rotate_names: tuple[str, ...]
    skipped: tuple[str, ...]
    warnings: tuple[str, ...]


@dataclass(frozen=True)
class BackupResult:
    preview: BackupPreview
    archive_path: str | None
    written_files: int
    skipped: tuple[str, ...]
    dry_run: bool
    cancelled: bool


@dataclass(frozen=True)
class ScheduleStatus:
    exists: bool
    enabled: bool
    frequency: str | None
    weekday: str | None
    time: str | None
    task_name: str | None
    warning: str | None


@dataclass(frozen=True)
class InstallSettings:
    package_ids: tuple[str, ...]
    scope: InstallScope


@dataclass(frozen=True)
class CleanupSettings:
    targets: tuple[CleanupTargetId, ...]


@dataclass(frozen=True)
class BackupSettings:
    sources: tuple[str, ...]
    destination: str | None
    keep_last: int
    schedule: ScheduleSettings


@dataclass(frozen=True)
class ReportSettings:
    format: str
    last_directory: str | None


@dataclass(frozen=True)
class Profile:
    schema_version: int
    install: InstallSettings
    cleanup: CleanupSettings
    backup: BackupSettings
    report: ReportSettings


@dataclass(frozen=True)
class ZipMember:
    source: Path
    arcname: str
    size: int


@dataclass(frozen=True)
class ElevationResult:
    started: bool
    message: str


@dataclass(frozen=True)
class CleanupRoots:
    user_temp: Path
    windows_temp: Path
    chrome_user_data: Path
    edge_user_data: Path
    firefox_profiles: Path


@dataclass(frozen=True)
class AppPaths:
    profile_path: Path
    log_path: Path
    log_dir: Path
