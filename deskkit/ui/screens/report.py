from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter

from deskkit.cancel import CancellationToken
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
        customtkinter.CTkLabel(self, text="Отчёт", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        self._progress = customtkinter.CTkProgressBar(self)
        self._progress.pack_forget()
        self._output = customtkinter.CTkTextbox(self, height=200)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)
        row = customtkinter.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        self._collect_btn = customtkinter.CTkButton(row, text=BTN_COLLECT, command=self._collect)
        self._collect_btn.pack(side="left", padx=4)
        self._html = customtkinter.CTkButton(
            row, text=BTN_SAVE_HTML, state="disabled", command=self._save_html
        )
        self._html.pack(side="left", padx=4)
        self._xlsx = customtkinter.CTkButton(
            row, text=BTN_SAVE_XLSX, state="disabled", command=self._save_xlsx
        )
        self._xlsx.pack(side="left", padx=4)

    def _collect(self) -> None:
        def task(_cancel: CancellationToken) -> SystemSnapshot:
            return self._presenter.collect()

        self._host.run_task(
            task,
            lambda snap: self._show(snap),
            self._host.notify,
        )

    def on_busy(self, busy: bool) -> None:
        if busy:
            self._progress.pack(fill="x", padx=12, pady=4, before=self._output)
            if hasattr(self._progress, "start"):
                self._progress.start()
            else:
                self._progress.set(0.5)
            self._collect_btn.configure(state="disabled")
        else:
            if hasattr(self._progress, "stop"):
                self._progress.stop()
            self._progress.pack_forget()
            self._collect_btn.configure(state="normal")

    def _show(self, snapshot: SystemSnapshot) -> None:
        self._snapshot = snapshot
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", self._presenter.summary(snapshot))
        self._output.configure(state="disabled")
        self._html.configure(state="normal")
        self._xlsx.configure(state="normal")

    def _timestamp(self) -> str:
        if self._snapshot:
            return self._snapshot.collected_at.strftime("%Y%m%d-%H%M%S")
        return "report"

    def _save_html(self) -> None:
        if not self._snapshot:
            return
        initial = f"DeskKit-report-{self._timestamp()}.html"
        path = self._host.pick_save(".html", initial)
        if path:
            self._presenter.save_html(self._snapshot, Path(path))
            self._host.notify(f"Сохранено: {path}")

    def _save_xlsx(self) -> None:
        if not self._snapshot:
            return
        initial = f"DeskKit-report-{self._timestamp()}.xlsx"
        path = self._host.pick_save(".xlsx", initial)
        if path:
            self._presenter.save_xlsx(self._snapshot, Path(path))
            self._host.notify(f"Сохранено: {path}")

    def refresh(self) -> None:
        pass
