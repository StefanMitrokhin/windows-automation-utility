from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from deskkit.cancel import CancellationToken

BUSY_TASK_MESSAGE = "Дождитесь окончания операции."


class TaskRunnerLike(Protocol):
    def is_busy(self) -> bool: ...

    def run_task(
        self,
        fn: Callable[[], object],
        on_ok: Callable[[object], None],
        on_err: Callable[[BaseException], None],
    ) -> bool: ...


class TaskDispatch:
    """Логика run_task/stop_task для DeskKitApp без привязки к окну."""

    def __init__(self) -> None:
        self._cancel = CancellationToken()

    def cancel_token(self) -> CancellationToken:
        return self._cancel

    def run_task(
        self,
        runner: TaskRunnerLike,
        notify: Callable[[str], None],
        fn: Callable[[CancellationToken], object],
        on_ok: Callable[[object], None],
        on_err: Callable[[BaseException], None],
    ) -> None:
        if runner.is_busy():
            notify(BUSY_TASK_MESSAGE)
            return
        self._cancel = CancellationToken()
        token = self._cancel

        def worker() -> object:
            return fn(token)

        runner.run_task(worker, on_ok, on_err)

    def stop_task(self, terminate: Callable[[], None]) -> None:
        self._cancel.cancel()
        terminate()
