from __future__ import annotations

import json

from deskkit.cli.main import run
from deskkit.models import CommandResult


def test_profile_export_path(context, tmp_path) -> None:
    out = tmp_path / "export.json"
    assert run(["profile", "export", str(out)], context=context) == 0
    json.loads(out.read_text(encoding="utf-8"))


def test_install_failed_exit_code(context) -> None:
    context.runner.enqueue(CommandResult((), 1, "err", "err", False, False))
    assert run(["install", "run", "--id", "7zip.7zip", "--yes"], context=context) == 1


def test_install_admin_exit_code(context) -> None:
    context.runner.enqueue(CommandResult((), -1978335207, "", "", False, False))
    code = run(["install", "run", "--id", "7zip.7zip", "--yes"], context=context)
    assert code == 1


def test_profile_apply_install_dry(context) -> None:
    from dataclasses import replace

    from deskkit.models import InstallScope, InstallSettings
    from deskkit.profile import default_profile

    context.profile_store.save(
        replace(
            default_profile(),
            install=InstallSettings(("7zip.7zip",), InstallScope.USER),
        )
    )
    assert run(["profile", "apply-install", "--dry-run"], context=context) == 0


def test_startup_enable_yes(context) -> None:
    from deskkit.models import Hive, RegKind, RegValue

    disabled = "Software\\StefanMitrokhin\\DeskKit\\DisabledStartup\\HKCU"
    context.startup._registry.data[(Hive.HKCU, disabled)] = {"X": RegValue("X", "cmd", RegKind.SZ)}
    assert run(["startup", "enable", "--id", "hkcu_run|X", "--yes"], context=context) == 0


def test_backup_unschedule_dry(context, capsys) -> None:
    assert run(["backup", "unschedule", "--dry-run"], context=context) == 0
    assert "будет удалена" in capsys.readouterr().out.lower() or "Задача" in capsys.readouterr().out
