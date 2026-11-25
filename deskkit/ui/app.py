from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog
from typing import Protocol

import customtkinter

from deskkit import __version__
from deskkit.app_context import Context, build_context
from deskkit.cancel import CancellationToken
from deskkit.ui import theme
from deskkit.ui.presenters import (
    BackupPresenter,
    CleanupPresenter,
    HomePresenter,
    InstallPresenter,
    LogsPresenter,
    ProfilePresenter,
    ReportPresenter,
    StartupPresenter,
)
from deskkit.ui.screens.backup import BackupScreen
from deskkit.ui.screens.cleanup import CleanupScreen
from deskkit.ui.screens.home import HomeScreen
from deskkit.ui.screens.install import InstallScreen
from deskkit.ui.screens.logs import LogsScreen
from deskkit.ui.screens.profile import ProfileScreen
from deskkit.ui.screens.report import ReportScreen
from deskkit.ui.screens.startup import StartupScreen
from deskkit.ui.strings import ADMIN_OFF, ADMIN_ON, APP_TITLE, NAV, VIEW_ONLY
from deskkit.ui.widgets import TaskRunner, confirm


class ScreenHost(Protocol):
    def show(self, screen_id: str) -> None: ...
    def view_only(self) -> bool: ...
    def run_task(
        self,
        fn: Callable[[], object],
        on_ok: Callable[[object], None],
        on_err: Callable[[BaseException], None],
    ) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def notify(self, text: str) -> None: ...
    def ask(self, title: str, body: str) -> bool: ...
    def pick_directory(self) -> str | None: ...
    def pick_save(self, suffix: str, initial: str) -> str | None: ...
    def pick_open(self) -> str | None: ...
    def open_folder(self, path: Path) -> None: ...
    def request_elevation(self) -> None: ...


class DeskKitApp(customtkinter.CTk, ScreenHost):
    def __init__(self, context: Context) -> None:
        super().__init__()
        self._context = context
        self._cancel = CancellationToken()
        self._view_only = customtkinter.BooleanVar(value=False)
        self._busy = False
        self.title(APP_TITLE)
        icon = Path(__file__).resolve().parent.parent / "assets" / "icon.ico"
        if sys.platform == "win32" and icon.is_file():
            self.iconbitmap(default=str(icon))
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)
        self._sidebar = customtkinter.CTkFrame(self, width=220)
        self._sidebar.grid(row=0, column=0, sticky="nsew")
        customtkinter.CTkLabel(self._sidebar, text=APP_TITLE, font=("Segoe UI", 20)).pack(
            pady=(12, 0)
        )
        customtkinter.CTkLabel(self._sidebar, text=__version__, font=("Segoe UI", 12)).pack()
        self._nav_buttons: dict[str, customtkinter.CTkButton] = {}
        for key, label in NAV.items():
            btn = customtkinter.CTkButton(
                self._sidebar,
                text=label,
                anchor="w",
                height=36,
                command=lambda k=key: self.show(k),
            )
            btn.pack(fill="x", padx=12, pady=4)
            self._nav_buttons[key] = btn
        self._content = customtkinter.CTkFrame(self)
        self._content.grid(row=0, column=1, sticky="nsew")
        self._content.grid_columnconfigure(0, weight=1)
        self._content.grid_rowconfigure(0, weight=1)
        self._status = customtkinter.CTkFrame(self, height=40)
        self._status.grid(row=1, column=0, columnspan=2, sticky="ew")
        admin = ADMIN_ON if context.admin.is_admin() else ADMIN_OFF
        customtkinter.CTkLabel(self._status, text=admin).pack(side="left", padx=12)
        customtkinter.CTkSwitch(self._status, text=VIEW_ONLY, variable=self._view_only).pack(
            side="left", expand=True
        )
        self._hint = customtkinter.CTkLabel(self._status, text="")
        self._hint.pack(side="right", padx=12)
        self._runner = TaskRunner(self)
        self._screens = {
            "home": HomeScreen(self._content, HomePresenter(context), self),
            "install": InstallScreen(self._content, InstallPresenter(context), self),
            "cleanup": CleanupScreen(self._content, CleanupPresenter(context), self),
            "report": ReportScreen(self._content, ReportPresenter(context), self),
            "startup": StartupScreen(self._content, StartupPresenter(context), self),
            "backup": BackupScreen(self._content, BackupPresenter(context), self),
            "profile": ProfileScreen(self._content, ProfilePresenter(context), self),
            "logs": LogsScreen(self._content, LogsPresenter(context), self),
        }
        for screen in self._screens.values():
            screen.grid(row=0, column=0, sticky="nsew")
        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.show("home")

    def show(self, screen_id: str) -> None:
        for key, button in self._nav_buttons.items():
            button.configure(fg_color="#1f6aa5" if key == screen_id else None)
        self._screens[screen_id].tkraise()
        self._screens[screen_id].refresh()

    def view_only(self) -> bool:
        return self._view_only.get()

    def run_task(
        self,
        fn: Callable[[], object],
        on_ok: Callable[[object], None],
        on_err: Callable[[BaseException], None],
    ) -> None:
        self._runner.run_task(fn, on_ok, on_err)

    def set_busy(self, busy: bool) -> None:
        self._busy = busy

    def notify(self, text: str) -> None:
        self._hint.configure(text=text)

    def ask(self, title: str, body: str) -> bool:
        return confirm(self, title, body)

    def pick_directory(self) -> str | None:
        return filedialog.askdirectory()

    def pick_save(self, suffix: str, initial: str) -> str | None:
        return filedialog.asksaveasfilename(defaultextension=suffix, initialfile=initial)

    def pick_open(self) -> str | None:
        return filedialog.askopenfilename()

    def open_folder(self, path: Path) -> None:
        self._context.open_folder(path)

    def request_elevation(self) -> None:
        result = self._context.admin.relaunch_elevated([])
        if result.started:
            self.destroy()
        else:
            self.notify(result.message)

    def _on_close(self) -> None:
        if self._busy:
            if confirm(self, APP_TITLE, "Сейчас выполняется операция. Остановить и закрыть?"):
                self._cancel.cancel()
                self._context.runner.terminate()
                self.destroy()
            return
        self.destroy()


def run_gui(context: Context | None = None) -> None:
    if context is None:
        context = build_context()
    theme.apply_theme()
    app = DeskKitApp(context)
    app.mainloop()
