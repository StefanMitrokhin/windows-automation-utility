from __future__ import annotations

import sys

import pytest

from deskkit.errors import ScheduleError
from deskkit.models import InstallScope, ScheduleSettings
from deskkit.platform.commands import (
    quote_task_tr,
    schtasks_create_args,
    subprocess_kwargs,
    winget_install_args,
)


def test_winget_args_user() -> None:
    args = winget_install_args("winget", "7zip.7zip", InstallScope.USER)
    assert "--scope" in args and "user" in args
    assert "--no-upgrade" in args
    assert "--source" in args and "winget" in args
    assert "--exact" in args
    assert "--disable-interactivity" in args
    assert "--override" not in args


def test_winget_args_auto() -> None:
    args = winget_install_args("winget", "7zip.7zip", InstallScope.AUTO)
    assert "--scope" not in args


def test_schtasks_weekly() -> None:
    schedule = ScheduleSettings(True, "weekly", "MON", "09:00")
    args = schtasks_create_args(r"\DeskKit\Backup", "tr", schedule)
    joined = " ".join(args)
    assert "/SC" in args and "WEEKLY" in args
    assert "/D" in args and "MON" in args
    assert "/ST" in args and "09:00" in args
    assert "/RL" in args and "LIMITED" in args
    assert "/IT" in args
    assert "/F" in args
    assert "/RU" not in joined and "SYSTEM" not in joined


def test_schtasks_daily() -> None:
    schedule = ScheduleSettings(True, "daily", "MON", "09:00")
    args = schtasks_create_args("DeskKit Backup", "tr", schedule)
    assert "/SC" in args and "DAILY" in args
    assert "/D" not in args


def test_tr_too_long() -> None:
    with pytest.raises(ScheduleError):
        quote_task_tr(["x" * 300])


def test_subprocess_kwargs_platform() -> None:
    if sys.platform == "win32":
        assert subprocess_kwargs() == {"creationflags": 0x08000000}
    else:
        assert subprocess_kwargs() == {}
