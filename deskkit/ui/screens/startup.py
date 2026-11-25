from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.models import StartupEntry
from deskkit.ui.presenters import StartupPresenter
from deskkit.ui.strings import BTN_ELEVATE, ELEVATE_HINT

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
        self._frame = customtkinter.CTkScrollableFrame(self)
        self._frame.pack(fill="both", expand=True, padx=12, pady=8)
        customtkinter.CTkLabel(self, text=ELEVATE_HINT).pack(anchor="w", padx=12)
        customtkinter.CTkButton(self, text=BTN_ELEVATE, command=self._host.request_elevation).pack(
            pady=4
        )

    def refresh(self) -> None:
        for child in self._frame.winfo_children():
            child.destroy()
        entries = self._presenter.entries()
        if not entries:
            customtkinter.CTkLabel(self._frame, text="Автозагрузка пуста.").pack(anchor="w")
            return
        for entry in entries:
            row = customtkinter.CTkFrame(self._frame)
            row.pack(fill="x", pady=2)
            customtkinter.CTkLabel(row, text=entry.name).pack(side="left")
            label = "Выкл" if not entry.enabled else "Вкл"
            customtkinter.CTkButton(
                row,
                text=label,
                command=lambda e=entry: self._toggle(e),
            ).pack(side="right")

    def _toggle(self, entry: StartupEntry) -> None:
        action = "enable" if not entry.enabled else "disable"
        if not self._host.ask("Подтверждение", self._presenter.confirmation(entry, action)):
            return
        if action == "disable":
            self._presenter.disable(entry.id, dry_run=False, confirmed=True)
        else:
            self._presenter.enable(entry.id, dry_run=False, confirmed=True)
        self.refresh()
