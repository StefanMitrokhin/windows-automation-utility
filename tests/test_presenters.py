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


def test_launch_control_state_table() -> None:
    from deskkit.ui.screen_state import launch_control_state

    assert launch_control_state(view_only=False, busy=False) == "normal"
    assert launch_control_state(view_only=True, busy=False) == "disabled"
    assert launch_control_state(view_only=False, busy=True) == "disabled"
    assert launch_control_state(view_only=True, busy=True) == "disabled"


def test_progress_indicator_only_on_current_screen() -> None:
    from deskkit.ui.screen_state import BusyUiSession, progress_indicator_visible

    assert progress_indicator_visible(app_busy=True, is_current_screen=True) is True
    assert progress_indicator_visible(app_busy=True, is_current_screen=False) is False
    assert progress_indicator_visible(app_busy=False, is_current_screen=True) is False

    ui = BusyUiSession(("install", "cleanup", "report"), current="install")
    ui.start_operation()
    assert ui.progress == {"install": True, "cleanup": False, "report": False}
    ui.show("cleanup")
    assert ui.progress == {"install": False, "cleanup": True, "report": False}
    assert ui.launch_state() == "disabled"
    ui.end_operation()
    assert all(not visible for visible in ui.progress.values())
    assert ui.launch_state() == "normal"


def test_busy_operation_switch_screen_clears_stale_progress() -> None:
    from deskkit.ui.screen_state import BusyUiSession

    ui = BusyUiSession(("install", "backup"), current="install")
    ui.start_operation()
    ui.show("backup")
    ui.show("install")
    ui.end_operation()
    assert ui.progress == {"install": False, "backup": False}


def test_launch_control_busy_survives_show_and_view_only_toggle() -> None:
    from deskkit.ui.screen_state import LaunchControlSession

    session = LaunchControlSession(view_only=False, busy=True)
    assert session.on_show() == "disabled"
    assert session.on_view_only_change(True) == "disabled"
    assert session.on_view_only_change(False) == "disabled"
    assert session.on_busy_change(False) == "normal"
    assert session.on_view_only_change(True) == "disabled"
    session.view_only = False
    session.busy = True
    assert session.on_show() == "disabled"
    assert session.on_busy_change(False) == "normal"


def test_run_task_stop_keeps_same_cancellation_token() -> None:
    """TaskDispatch (как DeskKitApp.run_task): stop отменяет токен задачи."""
    import threading
    import time

    from deskkit.cancel import CancellationToken
    from deskkit.ui.task_flow import TaskDispatch

    gate = threading.Event()
    notified: list[str] = []

    class FakeRunner:
        def __init__(self) -> None:
            self._busy = False

        def is_busy(self) -> bool:
            return self._busy

        def run_task(self, fn, on_ok, on_err) -> bool:
            if self._busy:
                return False
            self._busy = True

            def worker() -> None:
                try:
                    value = fn()
                except BaseException as exc:
                    on_err(exc)
                    return
                on_ok(value)

            threading.Thread(target=worker, daemon=True).start()
            return True

    runner = FakeRunner()
    dispatch = TaskDispatch()
    seen: list[bool] = []

    def work(cancel: CancellationToken) -> None:
        gate.wait(2)
        seen.append(cancel.is_cancelled())

    dispatch.run_task(runner, notified.append, work, lambda _: None, lambda _: None)
    token_before_stop = dispatch.cancel_token()
    dispatch.stop_task(lambda: None)
    assert dispatch.cancel_token() is token_before_stop
    gate.set()
    deadline = time.monotonic() + 2.0
    while time.monotonic() < deadline and not seen:
        time.sleep(0.001)
    assert seen == [True]


def test_run_task_while_busy_does_not_replace_cancel_token() -> None:
    """Повторный run_task при занятом runner не подменяет токен первой задачи."""
    import threading

    from deskkit.cancel import CancellationToken
    from deskkit.ui.task_flow import BUSY_TASK_MESSAGE, TaskDispatch

    gate = threading.Event()
    notified: list[str] = []

    class FakeRunner:
        def __init__(self) -> None:
            self._busy = False

        def is_busy(self) -> bool:
            return self._busy

        def run_task(self, fn, on_ok, on_err) -> bool:
            if self._busy:
                return False
            self._busy = True

            def worker() -> None:
                gate.wait(2)
                try:
                    value = fn()
                except BaseException as exc:
                    on_err(exc)
                    return
                on_ok(value)

            threading.Thread(target=worker, daemon=True).start()
            return True

    runner = FakeRunner()
    dispatch = TaskDispatch()
    terminate_calls = 0

    def work(cancel: CancellationToken) -> str:
        gate.wait(2)
        return "done" if not cancel.is_cancelled() else "stopped"

    dispatch.run_task(runner, notified.append, work, lambda _: None, lambda _: None)
    token_during_job = dispatch.cancel_token()
    dispatch.run_task(
        runner,
        notified.append,
        lambda _c: "second",
        lambda _: None,
        lambda _: None,
    )
    assert dispatch.cancel_token() is token_during_job
    assert BUSY_TASK_MESSAGE in notified

    def do_terminate() -> None:
        nonlocal terminate_calls
        terminate_calls += 1

    dispatch.stop_task(do_terminate)
    assert terminate_calls == 1
    gate.set()
    assert token_during_job.is_cancelled()
