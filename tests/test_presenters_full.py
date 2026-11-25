from __future__ import annotations

import json
from pathlib import Path

import pytest

from deskkit.cancel import CancellationToken
from deskkit.errors import ConfirmationRequired
from deskkit.models import CommandResult, InstallScope, ScheduleSettings
from deskkit.profile import default_profile
from deskkit.ui.presenters import (
    BackupPresenter,
    InstallPresenter,
    ProfilePresenter,
    StartupPresenter,
)


def test_presenter_remaining_methods(context, tmp_path: Path) -> None:
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    StartupPresenter(context).elevate()
    bp = BackupPresenter(context)
    settings = ScheduleSettings(True, "weekly", "MON", "09:00")
    with pytest.raises(ConfirmationRequired):
        bp.save_schedule(settings, confirmed=False)
    with pytest.raises(ConfirmationRequired):
        bp.remove_schedule(confirmed=False)
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    bp.remove_schedule(confirmed=True)
    pp = ProfilePresenter(context)
    path = tmp_path / "imp.json"
    path.write_text(
        json.dumps({"schema_version": 1}), encoding="utf-8"
    )  # invalid but parse test separate
    profile = default_profile()
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "install": {"package_ids": [], "scope": "user"},
                "cleanup": {"targets": ["user_temp"]},
                "backup": {
                    "sources": [],
                    "destination": None,
                    "keep_last": 5,
                    "schedule": {
                        "enabled": False,
                        "frequency": "weekly",
                        "weekday": "MON",
                        "time": "09:00",
                    },
                },
                "report": {"format": "html", "last_directory": None},
            }
        ),
        encoding="utf-8",
    )
    pp.parse_file(path)
    with pytest.raises(ConfirmationRequired):
        pp.import_from(path, confirmed=False)
    dest = tmp_path / "out"
    dest.mkdir()
    src = tmp_path / "src"
    src.mkdir()
    bp.execute([src], dest, 5, dry_run=True, confirmed=False, cancel=CancellationToken())
    ip = InstallPresenter(context)
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    ip.execute(
        ("7zip.7zip",), InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
