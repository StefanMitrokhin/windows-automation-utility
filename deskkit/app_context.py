from __future__ import annotations

import os
import sys
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from deskkit import __version__
from deskkit.catalog import Catalog
from deskkit.errors import ScheduleError, UnsupportedOSError
from deskkit.logging_setup import setup_logging
from deskkit.models import AppPaths
from deskkit.paths import (
    cleanup_roots_from_env,
    log_path_from_env,
    profile_path_from_env,
    startup_folders_from_env,
)
from deskkit.platform.files import LocalFileOps
from deskkit.platform.process import SubprocessRunner
from deskkit.platform.protocols import AdminGateway, Clock, CommandRunner
from deskkit.platform.system_probe import PsutilSystemProbe
from deskkit.profile import ProfileStore
from deskkit.services.backup import BackupService
from deskkit.services.cleanup import CleanupService
from deskkit.services.install import InstallService
from deskkit.services.report import ReportService
from deskkit.services.schedule import ScheduleService
from deskkit.services.startup import StartupService


@dataclass(frozen=True)
class Context:
    paths: AppPaths
    catalog: Catalog
    profile_store: ProfileStore
    installer: InstallService
    cleanup: CleanupService
    report: ReportService
    startup: StartupService
    backup: BackupService
    schedule: ScheduleService
    clock: Clock
    admin: AdminGateway
    runner: CommandRunner
    open_folder: Callable[[Path], None]
    version: str


def resolve_cli_argv() -> list[str]:
    if getattr(sys, "frozen", False):
        exe = Path(sys.executable).resolve()
        sibling = exe.parent.parent / "DeskKit-cli" / "DeskKit-cli.exe"
        if sibling.is_file():
            return [str(sibling)]
        if exe.name.lower() == "deskkit-cli.exe":
            return [str(exe)]
        raise ScheduleError("Не найден DeskKit-cli.exe рядом с установкой.")
    return [sys.executable, "-m", "deskkit"]


def build_context() -> Context:
    if sys.platform != "win32":
        raise UnsupportedOSError("DeskKit работает только в Windows.")
    from deskkit.platform.windows import WindowsPlatform

    home = Path.home()
    env = os.environ
    profile_path = profile_path_from_env(env, home)
    log_path = log_path_from_env(env, home)
    paths = AppPaths(profile_path=profile_path, log_path=log_path, log_dir=log_path.parent)
    setup_logging(log_path, verbose=False)
    runner = SubprocessRunner()
    platform = WindowsPlatform(runner)
    roots = cleanup_roots_from_env(env, home)
    files = LocalFileOps()
    user_startup, common_startup = startup_folders_from_env(env, home)

    class _Clock:
        def now(self) -> datetime:
            return datetime.now().astimezone()

    clock = _Clock()
    catalog = Catalog()
    winget = platform.resolve_winget()
    profile_store = ProfileStore(profile_path)
    install = InstallService(catalog, runner, winget)
    cleanup = CleanupService(roots, files, platform, clock)
    report = ReportService(PsutilSystemProbe(), platform, clock)
    startup = StartupService(platform, platform, user_startup, common_startup)
    backup = BackupService(files, clock)
    cli_prefix = resolve_cli_argv()
    schedule = ScheduleService(runner, cli_prefix)

    return Context(
        paths=paths,
        catalog=catalog,
        profile_store=profile_store,
        installer=install,
        cleanup=cleanup,
        report=report,
        startup=startup,
        backup=backup,
        schedule=schedule,
        clock=clock,
        admin=platform,
        runner=runner,
        open_folder=platform.open_folder,
        version=__version__,
    )
