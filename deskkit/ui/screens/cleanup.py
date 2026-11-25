from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.cancel import CancellationToken
from deskkit.errors import ValidationError
from deskkit.models import CleanupResult, CleanupTargetId
from deskkit.text import cleanup_preview_text, cleanup_result_text, cleanup_target_label
from deskkit.ui.presenters import CleanupPresenter, can_execute
from deskkit.ui.strings import (
    BTN_CANCEL_ACTION,
    BTN_ELEVATE,
    BTN_EXECUTE,
    BTN_PREVIEW,
    CONFIRM_TITLE,
    TEMP_AGE_HINT,
    WINDOWS_TEMP_HINT,
)

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost

CLEANUP_NO_PROFILE_SAVE = "Этот запуск не переписывает файл настроек."


class CleanupScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: CleanupPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        self._targets_seeded = False
        self._vars: dict[CleanupTargetId, customtkinter.BooleanVar] = {}
        customtkinter.CTkLabel(self, text="Очистка", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        customtkinter.CTkLabel(
            self,
            text=CLEANUP_NO_PROFILE_SAVE,
            font=("Segoe UI", 13),
            text_color=("gray30", "gray70"),
            justify="left",
        ).pack(anchor="w", padx=12, pady=4)
        for target in CleanupTargetId:
            row = customtkinter.CTkFrame(self, fg_color="transparent")
            row.pack(fill="x", padx=12, pady=2)
            var = customtkinter.BooleanVar(value=False)
            customtkinter.CTkCheckBox(row, text=cleanup_target_label(target), variable=var).pack(
                side="left"
            )
            self._vars[target] = var
            if target in (CleanupTargetId.USER_TEMP, CleanupTargetId.WINDOWS_TEMP):
                customtkinter.CTkLabel(
                    row,
                    text=TEMP_AGE_HINT,
                    font=("Segoe UI", 11),
                    text_color=("gray30", "gray70"),
                ).pack(side="left", padx=8)
            if target == CleanupTargetId.WINDOWS_TEMP:
                customtkinter.CTkLabel(
                    self,
                    text=WINDOWS_TEMP_HINT,
                    font=("Segoe UI", 11),
                    text_color=("gray30", "gray70"),
                    justify="left",
                ).pack(anchor="w", padx=24, pady=(0, 4))
        self._progress = customtkinter.CTkProgressBar(self)
        self._progress.pack_forget()
        self._output = customtkinter.CTkTextbox(self, height=160)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)
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
        customtkinter.CTkButton(row, text=BTN_ELEVATE, command=self._host.request_elevation).pack(
            side="left", padx=4
        )

    def _targets(self) -> tuple[CleanupTargetId, ...]:
        return tuple(target for target, var in self._vars.items() if var.get())

    def _preview(self) -> None:
        try:
            preview = self._presenter.preview(self._targets())
        except ValidationError as exc:
            self._host.notify(str(exc))
            return
        self._set(cleanup_preview_text(preview, include_footer=False))

    def _execute(self) -> None:
        if self._host.view_only() or not can_execute(self._host.view_only()):
            self._host.notify("Включён режим просмотра.")
            return
        targets = self._targets()
        try:
            preview = self._presenter.preview(targets)
        except ValidationError as exc:
            self._host.notify(str(exc))
            return
        if not self._host.ask(CONFIRM_TITLE, self._presenter.confirmation(preview)):
            self._host.notify("Действие отменено.")
            return

        def task(cancel: CancellationToken) -> CleanupResult:
            return self._presenter.execute(
                targets,
                dry_run=False,
                confirmed=True,
                cancel=cancel,
            )

        self._host.run_task(
            task, lambda result: self._set(cleanup_result_text(result)), self._host.notify
        )

    def on_busy(self, busy: bool) -> None:
        if busy:
            self._progress.pack(fill="x", padx=12, pady=4, before=self._output)
            if hasattr(self._progress, "start"):
                self._progress.start()
            else:
                self._progress.set(0.5)
            self._execute_btn.configure(state="disabled")
        else:
            if hasattr(self._progress, "stop"):
                self._progress.stop()
            self._progress.pack_forget()
            execute_state = "disabled" if self._host.view_only() else "normal"
            self._execute_btn.configure(state=execute_state)

    def _set(self, text: str) -> None:
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)
        self._output.configure(state="disabled")

    def refresh(self) -> None:
        if not self._targets_seeded:
            profile = self._presenter._context.profile_store.load()
            for target, var in self._vars.items():
                var.set(target in profile.cleanup.targets)
            self._targets_seeded = True
        execute_state = "disabled" if self._host.view_only() else "normal"
        self._execute_btn.configure(state=execute_state)
