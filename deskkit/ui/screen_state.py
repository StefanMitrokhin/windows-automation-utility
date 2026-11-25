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
