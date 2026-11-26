from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.errors import AdminRequiredError, DeskKitError
from deskkit.models import StartupEntry
from deskkit.text import startup_source_label
from deskkit.ui.presenters import StartupPresenter, can_execute
from deskkit.ui.strings import BTN_ELEVATE, CONFIRM_TITLE, ELEVATE_HINT

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


class StartupScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: StartupPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        customtkinter.CTkLabel(self, text="Автозагрузка", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        self._elevate_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        self._elevate_frame.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkLabel(self._elevate_frame, text=ELEVATE_HINT).pack(anchor="w")
        customtkinter.CTkButton(
            self._elevate_frame, text=BTN_ELEVATE, command=self._host.request_elevation
        ).pack(anchor="w", pady=4)
        self._frame = customtkinter.CTkScrollableFrame(self)
        self._frame.pack(fill="both", expand=True, padx=12, pady=8)

    def refresh(self) -> None:
        if self._host.is_admin():
            self._elevate_frame.pack_forget()
        else:
            self._elevate_frame.pack(fill="x", padx=12, pady=4, before=self._frame)
        for child in self._frame.winfo_children():
            child.destroy()
        entries = self._presenter.entries()
        if not entries:
            customtkinter.CTkLabel(self._frame, text="Автозагрузка пуста.").pack(anchor="w")
            return
        view_only = self._host.view_only()
        for entry in entries:
            self._add_row(entry, view_only)

    def _add_row(self, entry: StartupEntry, view_only: bool) -> None:
        row = customtkinter.CTkFrame(self._frame)
        row.pack(fill="x", pady=4)
        customtkinter.CTkLabel(row, text=entry.name, width=120, anchor="w").pack(
            side="left", padx=4
        )
        badge = "Вкл" if entry.enabled else "Выкл"
        customtkinter.CTkLabel(row, text=badge, width=40).pack(side="left", padx=4)
        customtkinter.CTkLabel(row, text=startup_source_label(entry.source), anchor="w").pack(
            side="left", padx=4
        )
        cmd = entry.command
        if len(cmd) > 80:
            cmd = cmd[:79] + "…"
        customtkinter.CTkLabel(row, text=cmd, anchor="w").pack(side="left", padx=4, fill="x")
        action = "Включить" if not entry.enabled else "Выключить"
        needs_admin = entry.needs_admin and not self._host.is_admin()
        state = "disabled" if view_only or needs_admin else "normal"
        customtkinter.CTkButton(
            row,
            text=action,
            state=state,
            command=lambda e=entry, a=action: self._toggle(e, a),
        ).pack(side="right", padx=4)

    def _toggle(self, entry: StartupEntry, action_label: str) -> None:
        if self._host.view_only() or not can_execute(self._host.view_only()):
            self._host.notify("Включён режим просмотра.")
            return
        action = "enable" if action_label == "Включить" else "disable"
        if not self._host.ask(CONFIRM_TITLE, self._presenter.confirmation(entry, action)):
            return
        try:
            if action == "disable":
                self._presenter.disable(entry.id, dry_run=False, confirmed=True)
            else:
                self._presenter.enable(entry.id, dry_run=False, confirmed=True)
        except (AdminRequiredError, DeskKitError) as exc:
            self._host.notify(str(exc))
        self.refresh()
