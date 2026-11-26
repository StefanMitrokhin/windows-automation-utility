from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from deskkit.__main__ import dispatch
from deskkit.cli.main import run
from deskkit.models import BackupSettings, ScheduleSettings
from deskkit.profile import default_profile


def test_version_dispatch(capsys, tmp_path, monkeypatch) -> None:
    import sys

    import pytest

    from deskkit.app_context import build_context, resolve_cli_argv
    from deskkit.errors import UnsupportedOSError

    assert dispatch(["--version"]) == 0
    assert capsys.readouterr().out == "DeskKit 0.1.0\n"
    assert resolve_cli_argv() == [sys.executable, "-m", "deskkit"]
    if sys.platform != "win32":
        with pytest.raises(UnsupportedOSError):
            build_context()
    monkeypatch.setattr(sys, "frozen", True, raising=False)
    install_root = tmp_path / "install"
    exe = install_root / "App" / "DeskKit.exe"
    exe.parent.mkdir(parents=True)
    exe.write_bytes(b"")
    monkeypatch.setattr(sys, "executable", str(exe))
    cli = install_root / "DeskKit-cli" / "DeskKit-cli.exe"
    cli.parent.mkdir(parents=True)
    cli.write_bytes(b"")
    assert resolve_cli_argv() == [str(cli)]
    cli_exe = tmp_path / "deskkit-cli.exe"
    cli_exe.write_bytes(b"")
    monkeypatch.setattr(sys, "executable", str(cli_exe))
    assert resolve_cli_argv() == [str(cli_exe)]
    lone = tmp_path / "DeskKit-gui.exe"
    lone.write_bytes(b"")
    monkeypatch.setattr(sys, "executable", str(lone))
    from deskkit.errors import ScheduleError

    with pytest.raises(ScheduleError):
        resolve_cli_argv()


def test_help(context, tmp_path) -> None:
    assert run(["--help"], context=context) == 0
    assert run([], context=context) == 0
    profile_path = tmp_path / "custom-profile.json"
    assert (
        run(
            ["--profile", str(profile_path), "profile", "path"],
            context=context,
        )
        == 0
    )


def test_install_list(context, monkeypatch, capsys) -> None:
    before = set(sys.modules)
    code = run(["install", "list"], context=context)
    after = set(sys.modules)
    assert code == 0
    out = capsys.readouterr().out
    assert "7zip.7zip" in out and "7-Zip" in out
    assert "customtkinter" not in after - before
    assert "tkinter" not in after - before


def test_install_preview_exit_3(context, capsys) -> None:
    code = run(["install", "preview", "--id", "7zip.7zip"], context=context)
    out = capsys.readouterr().out
    assert code == 3
    assert "7-Zip" in out and "Чтобы выполнить" in out
    assert not context.runner.calls
    assert run(["install", "preview", "--preset", "home"], context=context) == 3


def test_install_dry_run_exit_0(context) -> None:
    code = run(["install", "run", "--id", "7zip.7zip", "--dry-run"], context=context)
    assert code == 0
    assert not context.runner.calls


def test_install_yes(context) -> None:
    from deskkit.models import CommandResult

    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    code = run(["install", "run", "--id", "7zip.7zip", "--yes"], context=context)
    assert code == 0
    assert len(context.runner.calls) == 1
    context.runner.enqueue(CommandResult((), 1, "fail", "", False, False))
    assert run(["install", "run", "--id", "7zip.7zip", "--yes"], context=context) == 1
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    for _ in range(15):
        context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    assert run(["install", "run", "--preset", "home", "--yes"], context=context) == 0


def test_preset_and_id_conflict(context, capsys) -> None:
    code = run(
        ["install", "run", "--preset", "home", "--id", "7zip.7zip"],
        context=context,
    )
    assert code == 2
    assert "не оба сразу" in capsys.readouterr().err


def test_clean_preview_exit_3(context, capsys) -> None:
    code = run(["clean", "preview"], context=context)
    assert code == 3


def test_clean_yes(context, tmp_path, capsys) -> None:
    tmp_path.joinpath("Temp").mkdir(parents=True, exist_ok=True)
    code = run(["clean", "run", "--target", "user_temp", "--yes"], context=context)
    assert code == 0
    assert run(["clean", "run", "--yes"], context=context) == 0


def test_report_show(context, capsys) -> None:
    code = run(["report", "show"], context=context)
    assert code == 0
    assert "OFFICE-PC" in capsys.readouterr().out


def test_report_save_html(context, tmp_path) -> None:
    path = tmp_path / "r.html"
    assert run(["report", "save", str(path)], context=context) == 0
    assert "<html" in path.read_text(encoding="utf-8")


def test_report_save_bad_suffix(context, capsys) -> None:
    assert run(["report", "save", "a.txt"], context=context) == 2


def test_startup_list(context) -> None:
    from deskkit.models import Hive, RegKind, RegValue

    assert run(["startup", "list"], context=context) == 0
    context.startup._registry.data[
        (Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
    ] = {
        "KeepMe": RegValue("KeepMe", "cmd", RegKind.SZ),
        "PreviewMe": RegValue("PreviewMe", "cmd", RegKind.SZ),
    }
    assert (
        run(
            ["startup", "disable", "--id", "hkcu_run|PreviewMe", "--dry-run"],
            context=context,
        )
        == 0
    )
    assert run(["startup", "disable", "--id", "missing|x"], context=context) == 1
    assert (
        run(
            ["startup", "disable", "--id", "hkcu_run|KeepMe", "--yes"],
            context=context,
        )
        == 0
    )


def test_startup_disable_without_yes(context) -> None:
    from deskkit.models import Hive, RegKind, RegValue, StartupEntry, StartupSource
    from deskkit.ui.presenters import StartupPresenter

    context.startup._registry.data[
        (Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
    ] = {"OneDrive": RegValue("OneDrive", "x", RegKind.SZ)}
    code = run(["startup", "disable", "--id", "hkcu_run|OneDrive"], context=context)
    assert code == 3
    assert not context.startup._registry.events
    entry = StartupEntry("hkcu_run|OneDrive", StartupSource.HKCU_RUN, "OneDrive", "x", True, False)
    sp = StartupPresenter(context)
    assert sp.confirmation(entry, "disable")
    sp.disable("hkcu_run|OneDrive", dry_run=True, confirmed=False)


def test_backup_run_from_profile(context, tmp_path) -> None:

    src = tmp_path / "src"
    src.mkdir()
    (src / "f").write_bytes(b"x")
    dest = tmp_path / "dest"
    profile = replace(
        default_profile(),
        backup=BackupSettings(
            sources=(str(src),),
            destination=str(dest),
            keep_last=5,
            schedule=ScheduleSettings(False, "weekly", "MON", "09:00"),
        ),
    )
    context.profile_store.save(profile)
    assert run(["backup", "run", "--yes"], context=context) == 0
    assert list(dest.glob("DeskKit-backup-*.zip"))


def test_backup_source_without_dest(context, capsys, tmp_path) -> None:
    assert run(["backup", "preview", "--source", str(Path("/tmp/s"))], context=context) == 2
    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "dest"
    assert (
        run(
            ["backup", "preview", "--source", str(src), "--dest", str(dest)],
            context=context,
        )
        == 3
    )


def test_profile_init_and_show(context, capsys, tmp_path) -> None:
    context = replace(context, paths=replace(context.paths, profile_path=tmp_path / "profile.json"))
    context = replace(context, profile_store=type(context.profile_store)(tmp_path / "profile.json"))
    assert run(["profile", "init"], context=context) == 0
    assert run(["profile", "show"], context=context) == 0
    assert '"schema_version": 1' in capsys.readouterr().out
    from deskkit.models import InstallScope, InstallSettings

    profile = replace(
        context.profile_store.load(),
        install=InstallSettings(("7zip.7zip",), InstallScope.USER),
    )
    context.profile_store.save(profile)
    assert run(["profile", "apply-install", "--dry-run"], context=context) == 0
    exists = tmp_path / "exists.json"
    exists.write_text("{}", encoding="utf-8")
    assert run(["profile", "export", str(exists)], context=context) == 1


def test_profile_init_twice(context, capsys, tmp_path) -> None:
    from deskkit.profile import ProfileStore

    store = ProfileStore(tmp_path / "profile.json")
    context = replace(
        context,
        paths=replace(context.paths, profile_path=tmp_path / "profile.json"),
        profile_store=store,
    )
    run(["profile", "init"], context=context)
    code = run(["profile", "init"], context=context)
    assert code == 1
    assert "Профиль уже есть." in capsys.readouterr().err


def test_profile_import_requires_yes(context, tmp_path) -> None:
    path = tmp_path / "p.json"
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "install": {"package_ids": ["7zip.7zip"], "scope": "user"},
            }
        ),
        encoding="utf-8",
    )
    old = context.profile_store.load()
    assert run(["profile", "import", str(path)], context=context) == 3
    assert context.profile_store.load() == old
    assert run(["profile", "import", str(path), "--dry-run"], context=context) == 0
    assert run(["profile", "import", str(path), "--yes"], context=context) == 0
    assert context.profile_store.load().install.package_ids == ("7zip.7zip",)


def test_verbose_does_not_crash(context, tmp_path, capsys) -> None:
    from deskkit.models import CommandResult, Hive, RegKind, RegValue

    assert run(["-v", "install", "list"], context=context) == 0
    assert run(["install", "preview", "--id", "7zip.7zip", "--dry-run"], context=context) == 0
    assert run(["clean", "preview", "--dry-run"], context=context) == 0
    src = tmp_path / "src"
    src.mkdir()
    dest = tmp_path / "dest"
    assert (
        run(
            [
                "backup",
                "preview",
                "--source",
                str(src),
                "--dest",
                str(dest),
                "--dry-run",
            ],
            context=context,
        )
        == 0
    )
    assert run(["backup", "unschedule"], context=context) == 3
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    assert run(["backup", "unschedule", "--yes"], context=context) == 0
    assert run(["backup", "schedule", "--dry-run"], context=context) == 0
    assert run(["profile", "path"], context=context) == 0
    context.startup._registry.data[
        (Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
    ] = {"Item": RegValue("Item", "cmd", RegKind.SZ)}
    context.runner.enqueue(CommandResult((), 0, "", "", False, False))
    assert run(["startup", "enable", "--id", "hkcu_run|Item"], context=context) == 3
    export = tmp_path / "out.json"
    assert run(["profile", "export", str(export)], context=context) == 0
    assert export.is_file()
    assert run(["report", "save", str(tmp_path / "r.xlsx")], context=context) == 0


def test_dispatch_gui_rejects_extra() -> None:
    assert dispatch(["gui", "x"]) == 4


def test_unknown_command(context) -> None:
    assert run(["nope"], context=context) == 2
    assert run(["install", "run", "--yes"], context=context) == 1
    assert run(["install"], context=context) == 2


def test_schedule_disabled_profile(context, capsys) -> None:
    profile = replace(default_profile())
    context.profile_store.save(profile)
    code = run(["backup", "schedule", "--yes"], context=context)
    assert code == 1
    assert "выключено" in capsys.readouterr().err


def test_dry_run_wins_over_yes(context, tmp_path) -> None:
    f = tmp_path / "Temp" / "stay.bin"
    f.parent.mkdir(parents=True, exist_ok=True)
    f.write_bytes(b"x")
    code = run(
        ["clean", "run", "--target", "user_temp", "--dry-run", "--yes"],
        context=context,
    )
    assert code == 0
    assert f.exists()
