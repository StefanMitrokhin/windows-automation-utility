from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.ui.presenters import BackupPresenter
from deskkit.ui.strings import BTN_BACKUP_NOW, BTN_PREVIEW

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


class BackupScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: BackupPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        self._sources: list[str] = []
        self._dest = customtkinter.CTkEntry(self)
        self._dest.pack(fill="x", padx=12, pady=8)
        self._output = customtkinter.CTkTextbox(self, height=160)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)
        customtkinter.CTkButton(self, text=BTN_PREVIEW, command=self._preview).pack(pady=4)
        customtkinter.CTkButton(self, text=BTN_BACKUP_NOW, command=self._run).pack(pady=4)

    def _preview(self) -> None:
        from pathlib import Path

        from deskkit.text import backup_preview_text

        preview = self._presenter.preview(
            [Path(s) for s in self._sources], Path(self._dest.get() or "."), 5
        )
        self._output.delete("1.0", "end")
        self._output.insert("1.0", backup_preview_text(preview, include_footer=False))

    def _run(self) -> None:
        pass

    def refresh(self) -> None:
        backup = self._presenter._context.profile_store.load().backup
        self._sources = list(backup.sources)
        if backup.destination:
            self._dest.delete(0, "end")
            self._dest.insert(0, backup.destination)
