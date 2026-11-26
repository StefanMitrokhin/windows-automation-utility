from __future__ import annotations

import subprocess
import sys
from collections.abc import Sequence

from deskkit.errors import ScheduleError
from deskkit.models import InstallScope, ScheduleSettings

WINGET_TIMEOUT_S: float = 1800.0
TASK_NAME_PRIMARY = r"\DeskKit\Backup"
TASK_NAME_FALLBACK = "DeskKit Backup"
SCHTASKS_TR_LIMIT = 260


def winget_install_args(winget_exe: str, package_id: str, scope: InstallScope) -> list[str]:
    args = [
        winget_exe,
        "install",
        "--id",
        package_id,
        "--exact",
        "--silent",
        "--accept-package-agreements",
        "--accept-source-agreements",
        "--disable-interactivity",
        "--no-upgrade",
        "--source",
        "winget",
    ]
    if scope == InstallScope.USER:
        args.extend(["--scope", "user"])
    return args


def quote_task_tr(cli_prefix: Sequence[str]) -> str:
    tr = subprocess.list2cmdline([*cli_prefix, "backup", "run", "--yes"])
    if len(tr) > SCHTASKS_TR_LIMIT:
        raise ScheduleError("Команда задачи длиннее 260 символов.")
    return tr


def schtasks_create_args(task_name: str, tr: str, schedule: ScheduleSettings) -> list[str]:
    args = ["schtasks", "/Create", "/TN", task_name, "/TR", tr]
    if schedule.frequency == "weekly":
        args.extend(["/SC", "WEEKLY", "/D", schedule.weekday, "/ST", schedule.time])
    else:
        args.extend(["/SC", "DAILY", "/ST", schedule.time])
    args.extend(["/RL", "LIMITED", "/IT", "/F"])
    return args


def schtasks_query_args(task_name: str) -> list[str]:
    return ["schtasks", "/Query", "/TN", task_name, "/XML"]


def schtasks_delete_args(task_name: str) -> list[str]:
    return ["schtasks", "/Delete", "/TN", task_name, "/F"]


def subprocess_kwargs() -> dict[str, int]:
    if sys.platform == "win32":
        return {"creationflags": 0x08000000}
    return {}
