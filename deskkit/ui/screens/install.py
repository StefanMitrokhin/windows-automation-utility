from __future__ import annotations

import customtkinter

from deskkit.models import InstallScope
from deskkit.text import install_preview_text, install_report_text
from deskkit.ui.presenters import can_execute
from deskkit.ui.strings import BTN_CANCEL_ACTION, BTN_EXECUTE, BTN_PREVIEW, EMPTY_SELECTION


class InstallScreen(customtkinter.CTkFrame):
    def __init__(self, parent, presenter, host) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        self._checks: dict[str, customtkinter.BooleanVar] = {}
        frame = customtkinter.CTkScrollableFrame(self)
        frame.pack(fill="both", expand=True, padx=12, pady=8)
        for package in presenter.packages():
            var = customtkinter.BooleanVar(value=False)
            customtkinter.CTkCheckBox(
                frame, text=f"{package.name} — {package.summary}", variable=var
            ).pack(anchor="w")
            self._checks[package.id] = var
        self._scope = customtkinter.StringVar(value="user")
        self._output = customtkinter.CTkTextbox(self, height=160)
        self._output.pack(fill="x", padx=12, pady=8)
        row = customtkinter.CTkFrame(self)
        row.pack(fill="x", padx=12, pady=8)
        customtkinter.CTkButton(row, text=BTN_PREVIEW, command=self._preview).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(row, text=BTN_EXECUTE, command=self._execute).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(row, text=BTN_CANCEL_ACTION, command=lambda: None).pack(
            side="left", padx=4
        )

    def _selected(self) -> tuple[str, ...]:
        return tuple(pid for pid, var in self._checks.items() if var.get())

    def _preview(self) -> None:
        ids = self._selected()
        if not ids:
            self._host.notify(EMPTY_SELECTION)
            return
        scope = InstallScope.USER if self._scope.get() == "user" else InstallScope.AUTO
        preview = self._presenter.preview(ids, scope)
        self._set_output(install_preview_text(preview, include_footer=False))

    def _execute(self) -> None:
        if self._host.view_only() or not can_execute(self._host.view_only()):
            self._host.notify("Включён режим просмотра.")
            return
        ids = self._selected()
        if not ids:
            self._host.notify(EMPTY_SELECTION)
            return
        scope = InstallScope.USER if self._scope.get() == "user" else InstallScope.AUTO
        preview = self._presenter.preview(ids, scope)
        if not self._host.ask("Подтверждение", self._presenter.confirmation(preview)):
            self._host.notify("Действие отменено.")
            return
        from deskkit.cancel import CancellationToken

        token = CancellationToken()

        def task():
            return self._presenter.execute(ids, scope, dry_run=False, confirmed=True, cancel=token)

        self._host.run_task(
            task, lambda report: self._set_output(install_report_text(report)), self._host.notify
        )

    def _set_output(self, text: str) -> None:
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)
        self._output.configure(state="disabled")

    def refresh(self) -> None:
        pass
