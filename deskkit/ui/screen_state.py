from __future__ import annotations

from typing import Literal

LaunchControlState = Literal["disabled", "normal"]


def launch_control_state(*, view_only: bool, busy: bool) -> LaunchControlState:
    if view_only or busy:
        return "disabled"
    return "normal"


class LaunchControlSession:
    """Модель состояния кнопки запуска для тестов (без tkinter)."""

    def __init__(self, *, view_only: bool = False, busy: bool = False) -> None:
        self.view_only = view_only
        self.busy = busy

    def control_state(self) -> LaunchControlState:
        return launch_control_state(view_only=self.view_only, busy=self.busy)

    def on_show(self) -> LaunchControlState:
        return self.control_state()

    def on_view_only_change(self, view_only: bool) -> LaunchControlState:
        self.view_only = view_only
        return self.control_state()

    def on_busy_change(self, busy: bool) -> LaunchControlState:
        self.busy = busy
        return self.control_state()


def progress_indicator_visible(*, app_busy: bool, is_current_screen: bool) -> bool:
    return app_busy and is_current_screen


class BusyUiSession:
    """Модель прогресса и кнопок запуска при смене экрана (без tkinter)."""

    def __init__(
        self,
        screen_ids: tuple[str, ...],
        *,
        current: str,
        view_only: bool = False,
        busy: bool = False,
    ) -> None:
        self.screen_ids = screen_ids
        self.current = current
        self.view_only = view_only
        self.busy = busy
        self.progress: dict[str, bool] = {sid: False for sid in screen_ids}

    def _sync_progress(self) -> None:
        for sid in self.screen_ids:
            self.progress[sid] = progress_indicator_visible(
                app_busy=self.busy,
                is_current_screen=sid == self.current,
            )

    def launch_state(self) -> LaunchControlState:
        return launch_control_state(view_only=self.view_only, busy=self.busy)

    def start_operation(self) -> None:
        self.busy = True
        self._sync_progress()

    def end_operation(self) -> None:
        self.busy = False
        self._sync_progress()

    def show(self, screen_id: str) -> LaunchControlState:
        self.current = screen_id
        self._sync_progress()
        return self.launch_state()

    def toggle_view_only(self, view_only: bool) -> LaunchControlState:
        self.view_only = view_only
        return self.launch_state()
