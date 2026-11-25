from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.models import InstallReport, InstallScope, InstallStatus
from deskkit.text import install_preview_text, install_report_text
from deskkit.ui.presenters import InstallPresenter, can_execute
from deskkit.ui.strings import (
    BTN_CANCEL_ACTION,
    BTN_ELEVATE,
    BTN_EXECUTE,
    BTN_PREVIEW,
    CONFIRM_TITLE,
    EMPTY_SELECTION,
    PRESETS,
    SCOPE_LABELS,
)

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost

INSTALL_SCOPE_HINT = (
    "Сначала установка идёт для текущего пользователя. "
    "Если такой сборки нет, DeskKit повторит её без указания области, "
    "и Windows может запросить права."
)
PRESET_BY_LABEL = {label: key for key, label in PRESETS}
PRESET_LABELS = [label for _, label in PRESETS]


class InstallScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: InstallPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        self._checks: dict[str, customtkinter.BooleanVar] = {}
        customtkinter.CTkLabel(self, text="Установка", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        self._segment = customtkinter.CTkSegmentedButton(
            self,
            values=PRESET_LABELS,
            command=self._on_preset,
        )
        self._segment.set("Свой выбор")
        self._segment.pack(fill="x", padx=12, pady=8)
        scope_row = customtkinter.CTkFrame(self, fg_color="transparent")
        scope_row.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkLabel(scope_row, text="Область:").pack(side="left", padx=(0, 8))
        self._scope = customtkinter.StringVar(value=SCOPE_LABELS[0][1])
        self._scope_label_to_key = {label: key for key, label in SCOPE_LABELS}
        customtkinter.CTkOptionMenu(
            scope_row,
            variable=self._scope,
            values=[label for _, label in SCOPE_LABELS],
        ).pack(side="left")
        frame = customtkinter.CTkScrollableFrame(self, height=220)
        frame.pack(fill="both", expand=True, padx=12, pady=8)
        for package in presenter.packages():
            var = customtkinter.BooleanVar(value=False)
            customtkinter.CTkCheckBox(
                frame, text=f"{package.name} — {package.summary}", variable=var
            ).pack(anchor="w")
            self._checks[package.id] = var
        customtkinter.CTkLabel(
            self,
            text=INSTALL_SCOPE_HINT,
            font=("Segoe UI", 13),
            text_color=("gray30", "gray70"),
            justify="left",
            wraplength=560,
        ).pack(anchor="w", padx=12, pady=4)
        self._progress = customtkinter.CTkProgressBar(self)
        self._progress.pack(fill="x", padx=12, pady=4)
        self._progress.pack_forget()
        self._output = customtkinter.CTkTextbox(self, height=160)
        self._output.pack(fill="x", padx=12, pady=8)
        row = customtkinter.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)
        self._preview_btn = customtkinter.CTkButton(row, text=BTN_PREVIEW, command=self._preview)
        self._preview_btn.pack(side="left", padx=4)
        self._execute_btn = customtkinter.CTkButton(row, text=BTN_EXECUTE, command=self._execute)
        self._execute_btn.pack(side="left", padx=4)
        self._stop_btn = customtkinter.CTkButton(
            row, text=BTN_CANCEL_ACTION, command=self._host.stop_task
        )
        self._stop_btn.pack(side="left", padx=4)
        self._elevate_btn = customtkinter.CTkButton(
            row, text=BTN_ELEVATE, command=self._host.request_elevation
        )
        self._elevate_btn.pack_forget()

    def _scope_enum(self) -> InstallScope:
        key = self._scope_label_to_key[self._scope.get()]
        return InstallScope.USER if key == "user" else InstallScope.AUTO

    def _on_preset(self, value: str) -> None:
        key = PRESET_BY_LABEL.get(value, "custom")
        if key == "custom":
            return
        ids = set(self._presenter._context.catalog.ids_for_preset(key))
        for pid, var in self._checks.items():
            var.set(pid in ids)

    def _selected(self) -> tuple[str, ...]:
        return tuple(pid for pid, var in self._checks.items() if var.get())

    def _preview(self) -> None:
        ids = self._selected()
        if not ids:
            self._host.notify(EMPTY_SELECTION)
            return
        preview = self._presenter.preview(ids, self._scope_enum())
        self._set_output(install_preview_text(preview, include_footer=False))

    def _execute(self) -> None:
        if self._host.view_only() or not can_execute(self._host.view_only()):
            self._host.notify("Включён режим просмотра.")
            return
        ids = self._selected()
        if not ids:
            self._host.notify(EMPTY_SELECTION)
            return
        scope = self._scope_enum()
        preview = self._presenter.preview(ids, scope)
        if not self._host.ask(CONFIRM_TITLE, self._presenter.confirmation(preview)):
            self._host.notify("Действие отменено.")
            return
        cancel = self._host.cancel_token()

        def task() -> InstallReport:
            return self._presenter.execute(ids, scope, dry_run=False, confirmed=True, cancel=cancel)

        def done(report: InstallReport) -> None:
            self._set_output(install_report_text(report))
            needs_admin = any(item.status == InstallStatus.ADMIN_REQUIRED for item in report.items)
            if needs_admin:
                self._elevate_btn.pack(side="left", padx=4)
            else:
                self._elevate_btn.pack_forget()

        self._host.run_task(task, done, self._host.notify)

    def on_busy(self, busy: bool) -> None:
        if busy:
            self._progress.pack(fill="x", padx=12, pady=4, before=self._output)
            if hasattr(self._progress, "start"):
                self._progress.start()
            else:
                self._progress.set(0.5)
        else:
            if hasattr(self._progress, "stop"):
                self._progress.stop()
            self._progress.pack_forget()

    def _set_output(self, text: str) -> None:
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)
        self._output.configure(state="disabled")

    def refresh(self) -> None:
        execute_state = "disabled" if self._host.view_only() else "normal"
        self._execute_btn.configure(state=execute_state)
