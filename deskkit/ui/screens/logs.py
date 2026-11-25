from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.ui.presenters import LogsPresenter
from deskkit.ui.strings import BTN_OPEN_LOG_DIR, BTN_REFRESH

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


class LogsScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: LogsPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        customtkinter.CTkLabel(self, text="Журнал", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        self._text = customtkinter.CTkTextbox(self)
        self._text.pack(fill="both", expand=True, padx=12, pady=8)
        row = customtkinter.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        customtkinter.CTkButton(row, text=BTN_REFRESH, command=self.refresh).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(
            row,
            text=BTN_OPEN_LOG_DIR,
            command=lambda: self._host.open_folder(self._presenter.directory()),
        ).pack(side="left", padx=4)

    def refresh(self) -> None:
        self._text.delete("1.0", "end")
        self._text.insert("1.0", self._presenter.text())
