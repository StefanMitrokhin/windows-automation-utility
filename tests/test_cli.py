from __future__ import annotations

import json
import sys
from dataclasses import replace
from pathlib import Path

from deskkit.__main__ import dispatch
from deskkit.cli.main import run
from deskkit.models import BackupSettings, ScheduleSettings
from deskkit.profile import default_profile


def test_version_dispatch(capsys) -> None:
    assert dispatch(["--version"]) == 0
    assert capsys.readouterr().out == "DeskKit 0.1.0\n"


def test_help(context) -> None:
    assert run(["--help"], context=context) == 0


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
    assert run(["startup", "list"], context=context) == 0


def test_startup_disable_without_yes(context) -> None:
    from deskkit.models import Hive, RegKind, RegValue

    context.startup._registry.data[
        (Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")
    ] = {"OneDrive": RegValue("OneDrive", "x", RegKind.SZ)}
    code = run(["startup", "disable", "--id", "hkcu_run|OneDrive"], context=context)
    assert code == 3
    assert not context.startup._registry.events


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


def test_backup_source_without_dest(context, capsys) -> None:
    assert run(["backup", "preview", "--source", str(Path("/tmp/s"))], context=context) == 2


def test_profile_init_and_show(context, capsys, tmp_path) -> None:
    context = replace(context, paths=replace(context.paths, profile_path=tmp_path / "profile.json"))
    context = replace(context, profile_store=type(context.profile_store)(tmp_path / "profile.json"))
    assert run(["profile", "init"], context=context) == 0
    assert run(["profile", "show"], context=context) == 0
    assert '"schema_version": 1' in capsys.readouterr().out


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
    path.write_text(json.dumps({"schema_version": 1}), encoding="utf-8")
    old = context.profile_store.load()
    assert run(["profile", "import", str(path)], context=context) == 3
    assert context.profile_store.load() == old


def test_verbose_does_not_crash(context) -> None:
    assert run(["-v", "install", "list"], context=context) == 0


def test_dispatch_gui_rejects_extra() -> None:
    assert dispatch(["gui", "x"]) == 4


def test_unknown_command(context) -> None:
    assert run(["nope"], context=context) == 2


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
