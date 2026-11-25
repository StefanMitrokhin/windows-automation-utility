from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.ui.presenters import ProfilePresenter
from deskkit.ui.strings import BTN_APPLY_INSTALL, BTN_PROFILE_INIT, PROFILE_HINT

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


class ProfileScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: ProfilePresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        customtkinter.CTkLabel(self, text=PROFILE_HINT).pack(anchor="w", padx=12, pady=8)
        self._path = customtkinter.CTkEntry(self)
        self._path.pack(fill="x", padx=12, pady=4)
        self._text = customtkinter.CTkTextbox(self, height=260)
        self._text.pack(fill="both", expand=True, padx=12, pady=8)
        customtkinter.CTkButton(self, text=BTN_PROFILE_INIT, command=self._init).pack(pady=4)
        customtkinter.CTkButton(self, text=BTN_APPLY_INSTALL, command=lambda: None).pack(pady=4)

    def _init(self) -> None:
        try:
            self._presenter.init_default()
            self.refresh()
        except Exception as exc:
            self._host.notify(str(exc))

    def refresh(self) -> None:
        self._path.delete(0, "end")
        self._path.insert(0, str(self._presenter.path()))
        self._text.delete("1.0", "end")
        self._text.insert("1.0", self._presenter.text())
