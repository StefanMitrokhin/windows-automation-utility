from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter

from deskkit.models import SystemSnapshot
from deskkit.ui.presenters import ReportPresenter
from deskkit.ui.strings import BTN_COLLECT, BTN_SAVE_HTML, BTN_SAVE_XLSX

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


class ReportScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: ReportPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        self._snapshot: SystemSnapshot | None = None
        self._output = customtkinter.CTkTextbox(self, height=200)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)
        row = customtkinter.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        customtkinter.CTkButton(row, text=BTN_COLLECT, command=self._collect).pack(
            side="left", padx=4
        )
        self._html = customtkinter.CTkButton(
            row, text=BTN_SAVE_HTML, state="disabled", command=self._save_html
        )
        self._html.pack(side="left", padx=4)
        self._xlsx = customtkinter.CTkButton(
            row, text=BTN_SAVE_XLSX, state="disabled", command=self._save_xlsx
        )
        self._xlsx.pack(side="left", padx=4)

    def _collect(self) -> None:
        def task() -> SystemSnapshot:
            return self._presenter.collect()

        self._host.run_task(
            task,
            lambda snap: self._show(snap),
            self._host.notify,
        )

    def _show(self, snapshot: SystemSnapshot) -> None:
        self._snapshot = snapshot
        self._output.delete("1.0", "end")
        self._output.insert("1.0", self._presenter.summary(snapshot))
        self._html.configure(state="normal")
        self._xlsx.configure(state="normal")

    def _save_html(self) -> None:
        if not self._snapshot:
            return
        path = self._host.pick_save(".html", "DeskKit-report.html")
        if path:
            self._presenter.save_html(self._snapshot, Path(path))
            self._host.notify(f"Сохранено: {path}")

    def _save_xlsx(self) -> None:
        if not self._snapshot:
            return
        path = self._host.pick_save(".xlsx", "DeskKit-report.xlsx")
        if path:
            self._presenter.save_xlsx(self._snapshot, Path(path))
            self._host.notify(f"Сохранено: {path}")

    def refresh(self) -> None:
        pass
