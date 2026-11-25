from __future__ import annotations

import pytest

from deskkit.errors import ConfirmationRequired, ValidationError
from deskkit.models import InstallPreview, InstallScope, StartupEntry, StartupSource
from deskkit.ui.presenters import (
    BackupPresenter,
    HomePresenter,
    InstallPresenter,
    ReportPresenter,
    StartupPresenter,
    can_execute,
)
from deskkit.ui.strings import CONFIRM_LEAD, NAV


def test_can_execute() -> None:
    assert can_execute(False) is True
    assert can_execute(True) is False


def test_home_status_winget_missing(context) -> None:
    from deskkit.models import CommandResult

    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    from dataclasses import replace

    from deskkit.services.install import InstallService

    installer = InstallService(context.catalog, context.runner, None)
    ctx = replace(context, installer=installer)
    status = HomePresenter(ctx).status()
    assert status.winget_found is False
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    context.runner.enqueue(CommandResult((), 1, "", "", False, False))
    assert HomePresenter(context).status().winget_found is True


def test_install_confirmation_has_lead_and_name(context, tmp_path) -> None:
    from deskkit.cancel import CancellationToken

    presenter = InstallPresenter(context)
    assert presenter.packages()
    preview = InstallPreview(("7zip.7zip",), ("7-Zip",), InstallScope.USER, True)
    text = presenter.confirmation(preview)
    assert CONFIRM_LEAD in text and "7-Zip" in text
    preview2 = presenter.preview(("7zip.7zip",), InstallScope.USER)
    presenter.execute(
        ("7zip.7zip",),
        InstallScope.USER,
        dry_run=True,
        confirmed=False,
        cancel=CancellationToken(),
    )
    assert presenter.confirmation(preview2)
    rp = ReportPresenter(context)
    snap = rp.collect()
    rp.save_html(snap, tmp_path / "r.html")
    rp.save_xlsx(snap, tmp_path / "r.xlsx")
    entry = StartupEntry("hkcu_run|Z", StartupSource.HKCU_RUN, "Z", "cmd", True, False)
    sp = StartupPresenter(context)
    sp.confirmation(entry, "disable")
    sp.elevate()
    src = tmp_path / "s"
    src.mkdir()
    (src / "a").write_bytes(b"1")
    bp = BackupPresenter(context)
    bprev = bp.preview([src], tmp_path / "d", 5)
    bp.confirmation(bprev)
    from deskkit.models import ScheduleSettings

    assert bp.schedule_text(ScheduleSettings(True, "weekly", "MON", "09:00"))


def test_profile_init_refuses_second(context, tmp_path) -> None:
    import json
    from dataclasses import replace

    from deskkit.cancel import CancellationToken
    from deskkit.profile import ProfileStore
    from deskkit.ui.presenters import ProfilePresenter

    store = ProfileStore(tmp_path / "profile.json")
    ctx = replace(
        context,
        profile_store=store,
        paths=replace(context.paths, profile_path=tmp_path / "profile.json"),
    )
    presenter = ProfilePresenter(ctx)
    assert presenter.path() == tmp_path / "profile.json"
    assert presenter.load()
    presenter.text()
    presenter.init_default()
    export_path = tmp_path / "ex.json"
    presenter.export_to(export_path)
    import_file = tmp_path / "import.json"
    import_file.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "install": {
                    "package_ids": ["7zip.7zip"],
                    "scope": "user",
                },
            }
        ),
        encoding="utf-8",
    )
    assert presenter.parse_file(import_file)
    corrupt = tmp_path / "corrupt.json"
    corrupt.write_text("{not json", encoding="utf-8")
    with pytest.raises(ValidationError, match="повреждён"):
        presenter.parse_file(corrupt)
    with pytest.raises(ConfirmationRequired):
        presenter.import_from(import_file, confirmed=False)
    presenter.import_from(import_file, confirmed=True)
    presenter.apply_install(dry_run=True, confirmed=False, cancel=CancellationToken())
    with pytest.raises(ValidationError):
        presenter.init_default()


def test_strings_nav_complete() -> None:
    expected = {"home", "install", "cleanup", "report", "startup", "backup", "profile", "logs"}
    assert set(NAV) == expected
    assert all(NAV.values())
