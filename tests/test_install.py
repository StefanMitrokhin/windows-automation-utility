from __future__ import annotations

import pytest

from deskkit.cancel import CancellationToken
from deskkit.catalog import Catalog
from deskkit.errors import ConfirmationRequired, ValidationError, WingetNotFoundError
from deskkit.models import CommandResult, InstallScope, InstallStatus
from deskkit.services.install import ALREADY_INSTALLED_CODES, InstallService
from tests.fakes import FakeRunner


def _service(winget: str | None = "winget.exe") -> tuple[InstallService, FakeRunner]:
    runner = FakeRunner()
    return InstallService(Catalog(), runner, winget), runner


def test_preview_does_not_call_runner() -> None:
    svc, runner = _service()
    preview = svc.preview(["7zip.7zip"], InstallScope.USER)
    assert not runner.calls
    assert preview.names[0] == "7-Zip"


def test_unknown_id() -> None:
    svc, _ = _service()
    with pytest.raises(ValidationError):
        svc.preview(["nope"], InstallScope.USER)


def test_empty_ids() -> None:
    svc, _ = _service()
    with pytest.raises(ValidationError) as exc:
        svc.apply([], InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken())
    assert str(exc.value) == "Не выбрано ни одной программы."


def test_dry_run() -> None:
    svc, runner = _service()
    report = svc.apply(
        ["7zip.7zip"], InstallScope.USER, dry_run=True, confirmed=False, cancel=CancellationToken()
    )
    assert not runner.calls
    assert report.dry_run


def test_confirmation_required() -> None:
    svc, runner = _service()
    with pytest.raises(ConfirmationRequired):
        svc.apply(
            ["7zip.7zip"],
            InstallScope.USER,
            dry_run=False,
            confirmed=False,
            cancel=CancellationToken(),
        )
    assert not runner.calls


def test_success() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    report = svc.apply(
        ["7zip.7zip"], InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert report.items[0].status == InstallStatus.SUCCESS
    assert "--no-upgrade" in " ".join(runner.calls[0][0])


def test_already_installed_codes() -> None:
    for code in ALREADY_INSTALLED_CODES:
        svc, runner = _service()
        runner.enqueue(CommandResult((), code, "", "", False, False))
        report = svc.apply(
            ["7zip.7zip"],
            InstallScope.USER,
            dry_run=False,
            confirmed=True,
            cancel=CancellationToken(),
        )
        assert report.items[0].status == InstallStatus.SKIPPED_INSTALLED


def test_retry_once_without_scope() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), -1978335216, "", "", False, False))
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    svc.apply(
        ["7zip.7zip"], InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert len(runner.calls) == 2
    assert "--scope" not in " ".join(runner.calls[1][0])


def test_no_retry_when_auto() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), -1978335216, "", "", False, False))
    report = svc.apply(
        ["7zip.7zip"], InstallScope.AUTO, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert len(runner.calls) == 1
    assert report.items[0].status == InstallStatus.FAILED


def test_admin_code() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), -1978335207, "", "", False, False))
    report = svc.apply(
        ["7zip.7zip"], InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert report.items[0].status == InstallStatus.ADMIN_REQUIRED


def test_timeout_message() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), None, "", "", True, False))
    report = svc.apply(
        ["7zip.7zip"], InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken()
    )
    assert "превышено время ожидания" in report.items[0].message


def test_cancel_between_packages() -> None:
    svc, runner = _service()
    token = CancellationToken()

    def on_call(_args):
        token.cancel()

    runner.on_call = on_call
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    report = svc.apply(
        ["7zip.7zip", "VideoLAN.VLC"],
        InstallScope.USER,
        dry_run=False,
        confirmed=True,
        cancel=token,
    )
    assert report.cancelled
    assert len(runner.calls) == 1


def test_winget_missing(context) -> None:
    svc, _ = _service(winget=None)
    with pytest.raises(WingetNotFoundError) as exc:
        svc.apply(
            ["7zip.7zip"],
            InstallScope.USER,
            dry_run=False,
            confirmed=True,
            cancel=CancellationToken(),
        )
    assert str(exc.value).startswith("Не найден winget.")

    from dataclasses import replace

    from deskkit.cli.main import run

    ctx = replace(context, installer=svc)
    assert run(["install", "run", "--id", "7zip.7zip", "--yes"], context=ctx) == 1


def test_order_preserved() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    ids = ["7zip.7zip", "VideoLAN.VLC", "Google.Chrome"]
    svc.apply(ids, InstallScope.USER, dry_run=False, confirmed=True, cancel=CancellationToken())
    called = [call[0][call[0].index("--id") + 1] for call in runner.calls]
    assert called == ids


def test_partial_failure_keeps_success() -> None:
    svc, runner = _service()
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    runner.enqueue(CommandResult((), 1, "e", "", False, False))
    report = svc.apply(
        ["7zip.7zip", "VideoLAN.VLC"],
        InstallScope.USER,
        dry_run=False,
        confirmed=True,
        cancel=CancellationToken(),
    )
    assert report.items[0].status == InstallStatus.SUCCESS
    assert report.items[1].status == InstallStatus.FAILED
