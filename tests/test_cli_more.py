from __future__ import annotations

from dataclasses import replace

from deskkit.cli.main import run
from deskkit.models import (
    BackupSettings,
    CommandResult,
    ScheduleSettings,
)
from deskkit.profile import default_profile


def test_install_cancel_exit_4(context) -> None:
    def on_call(_args):
        context.runner.terminate()

    context.runner.on_call = on_call
    context.runner.enqueue(CommandResult((), None, "", "", False, True))
    code = run(["install", "run", "--id", "7zip.7zip", "--yes"], context=context)
    assert code == 4


def test_backup_schedule_dry(context) -> None:
    profile = replace(
        default_profile(),
        backup=BackupSettings(
            sources=("/x",),
            destination="/y",
            keep_last=5,
            schedule=ScheduleSettings(True, "weekly", "MON", "09:00"),
        ),
    )
    context.profile_store.save(profile)
    assert run(["backup", "schedule", "--dry-run"], context=context) == 0


def test_profile_import_yes(context, tmp_path) -> None:
    path = tmp_path / "p.json"
    data = {
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
    path.write_text(__import__("json").dumps(data), encoding="utf-8")
    assert run(["profile", "import", str(path), "--yes"], context=context) == 0


def test_clean_run_recycle(context) -> None:
    assert run(["clean", "run", "--target", "recycle_bin", "--yes"], context=context) == 0
