from __future__ import annotations

import pytest

from deskkit.errors import ValidationError
from deskkit.models import InstallPreview, InstallScope
from deskkit.ui.presenters import HomePresenter, InstallPresenter, can_execute
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


def test_install_confirmation_has_lead_and_name(context) -> None:
    preview = InstallPreview(("7zip.7zip",), ("7-Zip",), InstallScope.USER, True)
    text = InstallPresenter(context).confirmation(preview)
    assert CONFIRM_LEAD in text and "7-Zip" in text


def test_profile_init_refuses_second(context, tmp_path) -> None:
    from dataclasses import replace

    from deskkit.profile import ProfileStore
    from deskkit.ui.presenters import ProfilePresenter

    store = ProfileStore(tmp_path / "profile.json")
    ctx = replace(
        context,
        profile_store=store,
        paths=replace(context.paths, profile_path=tmp_path / "profile.json"),
    )
    presenter = ProfilePresenter(ctx)
    presenter.init_default()
    with pytest.raises(ValidationError):
        presenter.init_default()


def test_strings_nav_complete() -> None:
    expected = {"home", "install", "cleanup", "report", "startup", "backup", "profile", "logs"}
    assert set(NAV) == expected
    assert all(NAV.values())
