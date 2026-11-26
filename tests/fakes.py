from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from pathlib import Path

from deskkit import __version__
from deskkit.app_context import Context
from deskkit.catalog import Catalog
from deskkit.models import (
    AppPaths,
    CommandResult,
    DiskInfo,
    ElevationResult,
    Hive,
    RegKind,
    RegValue,
    SoftwareEntry,
    SystemSnapshot,
)
from deskkit.paths import cleanup_roots_from_env, log_path_from_env
from deskkit.platform.files import LocalFileOps
from deskkit.profile import ProfileStore
from deskkit.services.backup import BackupService
from deskkit.services.cleanup import CleanupService
from deskkit.services.install import InstallService
from deskkit.services.report import ReportService
from deskkit.services.schedule import ScheduleService
from deskkit.services.startup import StartupService


@dataclass
class FakeRunner:
    queue: list[CommandResult] = field(default_factory=list)
    calls: list[tuple[tuple[str, ...], float]] = field(default_factory=list)
    timeouts: list[float] = field(default_factory=list)
    on_call: object | None = None
    terminated: bool = False

    def enqueue(self, result: CommandResult) -> None:
        self.queue.append(result)

    def run(self, args: Sequence[str], timeout_s: float) -> CommandResult:
        self.calls.append((tuple(args), timeout_s))
        self.timeouts.append(timeout_s)
        if self.on_call:
            self.on_call(args)
        if not self.queue:
            raise AssertionError("FakeRunner queue empty")
        return self.queue.pop(0)

    def terminate(self) -> None:
        self.terminated = True


@dataclass
class FakeRegistry:
    data: dict[tuple[Hive, str], dict[str, RegValue]] = field(default_factory=dict)
    fail_delete: set[tuple[Hive, str, str]] = field(default_factory=set)
    events: list[str] = field(default_factory=list)

    def list_values(self, hive: Hive, key: str) -> tuple[RegValue, ...]:
        return tuple(self.data.get((hive, key), {}).values())

    def set_string(self, hive: Hive, key: str, name: str, data: str) -> None:
        self.events.append(f"set {hive.value}/{key}/{name}")
        bucket = self.data.setdefault((hive, key), {})
        bucket[name] = RegValue(name=name, data=data, kind=RegKind.SZ)

    def delete_value(self, hive: Hive, key: str, name: str) -> None:
        if (hive, key, name) in self.fail_delete:
            raise OSError("delete failed")
        self.events.append(f"delete {hive.value}/{key}/{name}")
        self.data.get((hive, key), {}).pop(name, None)


@dataclass
class FakeRecycle:
    size: int = 0
    count: int = 0
    emptied: list[str] = field(default_factory=list)
    fail_query: bool = False

    def query(self) -> tuple[int, int]:
        if self.fail_query:
            from deskkit.errors import DeskKitError

            raise DeskKitError("Не удалось прочитать корзину.")
        return self.size, self.count

    def empty(self) -> None:
        self.emptied.append("empty")


@dataclass
class FakeAdmin:
    admin: bool = False
    opened: list[Path] = field(default_factory=list)

    def is_admin(self) -> bool:
        return self.admin

    def relaunch_elevated(self, argv: Sequence[str]) -> ElevationResult:
        return ElevationResult(False, "Повышение прав отменено.")


class FakeClock:
    def __init__(self, moment: datetime | None = None) -> None:
        self.moment = moment or datetime(2026, 1, 15, 9, 0, tzinfo=timezone(timedelta(hours=3)))

    def now(self) -> datetime:
        return self.moment


class FakeSoftware:
    def __init__(self, entries: tuple[SoftwareEntry, ...] = ()) -> None:
        self._entries = entries

    def list_installed(self) -> tuple[SoftwareEntry, ...]:
        return self._entries


class FakeSystem:
    def snapshot_base(self) -> SystemSnapshot:
        return SystemSnapshot(
            collected_at=datetime(2026, 1, 15, 9, 0, tzinfo=timezone(timedelta(hours=3))),
            hostname="OFFICE-PC",
            os_name="Windows",
            os_version="11",
            os_build="22631",
            machine="AMD64",
            cpu_model="CPU",
            cpu_physical=1,
            cpu_logical=2,
            cpu_freq_mhz=None,
            ram_total_bytes=1024,
            ram_available_bytes=512,
            disks=(
                DiskInfo(
                    device="C:",
                    mountpoint="C:\\",
                    fstype="NTFS",
                    total_bytes=1024,
                    used_bytes=512,
                    free_bytes=512,
                    available=True,
                ),
            ),
            software=(),
        )


def make_context(tmp_path: Path) -> Context:
    env = {
        "APPDATA": str(tmp_path / "Roaming"),
        "LOCALAPPDATA": str(tmp_path / "Local"),
        "TEMP": str(tmp_path / "Temp"),
        "TMP": str(tmp_path / "Temp"),
        "SYSTEMROOT": str(tmp_path / "Windows"),
        "PROGRAMDATA": str(tmp_path / "ProgramData"),
    }
    home = tmp_path / "home"
    roots = cleanup_roots_from_env(env, home)
    roots = replace(
        roots,
        user_temp=tmp_path / "Temp",
        chrome_user_data=tmp_path / "browsers" / "chrome" / "User Data",
        edge_user_data=tmp_path / "browsers" / "edge" / "User Data",
        firefox_profiles=tmp_path / "browsers" / "firefox" / "Profiles",
    )
    profile_path = tmp_path / "Roaming" / "DeskKit" / "profile.json"
    log_path = log_path_from_env(env, home)
    paths = AppPaths(profile_path=profile_path, log_path=log_path, log_dir=log_path.parent)
    files = LocalFileOps()
    runner = FakeRunner()
    catalog = Catalog()
    recycle = FakeRecycle()
    clock = FakeClock()
    system = FakeSystem()
    software = FakeSoftware()
    admin = FakeAdmin()
    registry = FakeRegistry()
    user_startup = tmp_path / "startup-user"
    common_startup = tmp_path / "startup-common"
    user_startup.mkdir(parents=True, exist_ok=True)
    common_startup.mkdir(parents=True, exist_ok=True)
    install = InstallService(catalog, runner, "winget.exe")
    cleanup = CleanupService(roots, files, recycle, clock)
    report = ReportService(system, software, clock)
    startup = StartupService(registry, admin, user_startup, common_startup)
    backup = BackupService(files, clock)
    schedule = ScheduleService(runner, ["deskkit-cli"])

    def open_folder(path: Path) -> None:
        admin.opened.append(path)

    return Context(
        paths=paths,
        catalog=catalog,
        profile_store=ProfileStore(profile_path),
        installer=install,
        cleanup=cleanup,
        report=report,
        startup=startup,
        backup=backup,
        schedule=schedule,
        clock=clock,
        admin=admin,
        runner=runner,
        open_folder=open_folder,
        version=__version__,
    )
