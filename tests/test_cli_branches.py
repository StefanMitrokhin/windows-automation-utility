from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from deskkit.cli.main import run
from deskkit.models import CommandResult, Hive, InstallScope, InstallSettings, RegKind, RegValue
from deskkit.profile import default_profile


def test_report_save_xlsx(context, tmp_path: Path) -> None:
    path = tmp_path / "report.xlsx"
    assert run(["report", "save", str(path)], context=context) == 0
    assert path.is_file()


def test_install_preview_missing_selection(context) -> None:
    assert run(["install", "preview"], context=context) == 1


def test_install_scope_auto(context) -> None:
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    assert (
        run(["install", "run", "--id", "7zip.7zip", "--scope", "auto", "--yes"], context=context)
        == 0
    )


def test_startup_disable_dry_run(context) -> None:
    key = r"Software\Microsoft\Windows\CurrentVersion\Run"
    context.startup._registry.data[(Hive.HKCU, key)] = {
        "App": RegValue("App", "cmd", RegKind.SZ),
    }
    assert run(["startup", "disable", "--id", "hkcu_run|App", "--dry-run"], context=context) == 0


def test_startup_missing_entry(context) -> None:
    assert run(["startup", "disable", "--id", "hkcu_run|Missing", "--yes"], context=context) == 1


def test_backup_schedule_requires_yes(context) -> None:
    assert run(["backup", "schedule"], context=context) == 3


def test_backup_schedule_validation_error(context, capsys) -> None:
    code = run(["backup", "schedule", "--yes"], context=context)
    captured = capsys.readouterr()
    assert code == 1
    assert "расписание" in captured.err.lower()


def test_backup_unschedule_requires_yes(context) -> None:
    assert run(["backup", "unschedule"], context=context) == 3


def test_backup_unschedule_yes(context) -> None:
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    assert run(["backup", "unschedule", "--yes"], context=context) == 0


def test_backup_preview_exit_3(context, tmp_path: Path) -> None:
    dest = tmp_path / "dest"
    dest.mkdir()
    src = tmp_path / "src"
    src.mkdir()
    profile = replace(
        default_profile(),
        backup=replace(
            default_profile().backup,
            sources=(str(src),),
            destination=str(dest),
        ),
    )
    context.profile_store.save(profile)
    (src / "a.txt").write_text("x", encoding="utf-8")
    assert run(["backup", "preview"], context=context) == 3


def test_profile_path_command(context) -> None:
    assert run(["profile", "path"], context=context) == 0


def test_profile_export_conflict(context, tmp_path: Path) -> None:
    out = tmp_path / "out.json"
    out.write_text("{}", encoding="utf-8")
    assert run(["profile", "export", str(out)], context=context) == 1


def test_profile_import_dry_run(context, tmp_path: Path) -> None:
    path = tmp_path / "p.json"
    path.write_text(
        '{"schema_version":1,"install":{"package_ids":[],"scope":"user"},'
        '"cleanup":{"targets":["user_temp"]},"backup":{"sources":[],"destination":null,'
        '"keep_last":5,"schedule":{"enabled":false,"frequency":"weekly","weekday":"MON",'
        '"time":"09:00"}},"report":{"format":"html","last_directory":null}}',
        encoding="utf-8",
    )
    assert run(["profile", "import", str(path), "--dry-run"], context=context) == 0


def test_profile_apply_install_yes(context) -> None:
    context.profile_store.save(
        replace(
            default_profile(),
            install=InstallSettings(("7zip.7zip",), InstallScope.USER),
        )
    )
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    assert run(["profile", "apply-install", "--yes"], context=context) == 0


def test_cli_custom_profile_path(context, tmp_path: Path, capsys) -> None:
    custom = tmp_path / "alt.json"
    code = run(["--profile", str(custom), "profile", "path"], context=context)
    assert code == 0
    assert capsys.readouterr().out.strip() == str(custom)


def test_clean_default_targets_from_profile(context, tmp_path: Path) -> None:
    temp = Path(context.cleanup._roots.user_temp)  # type: ignore[attr-defined]
    temp.mkdir(parents=True, exist_ok=True)
    old = temp / "old.dat"
    old.write_bytes(b"x")
    import os

    os.utime(old, (0, 0))
    assert run(["clean", "preview"], context=context) == 3
