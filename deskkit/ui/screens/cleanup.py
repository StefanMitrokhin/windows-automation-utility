from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit.models import CleanupResult, CleanupTargetId
from deskkit.text import cleanup_preview_text, cleanup_result_text, cleanup_target_label
from deskkit.ui.presenters import CleanupPresenter
from deskkit.ui.strings import BTN_EXECUTE, BTN_PREVIEW

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


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
        self._vars: dict[CleanupTargetId, customtkinter.BooleanVar] = {}
        for target in CleanupTargetId:
            var = customtkinter.BooleanVar(value=False)
            customtkinter.CTkCheckBox(self, text=cleanup_target_label(target), variable=var).pack(
                anchor="w", padx=12
            )
            self._vars[target] = var
        self._output = customtkinter.CTkTextbox(self, height=160)
        self._output.pack(fill="both", expand=True, padx=12, pady=8)
        customtkinter.CTkButton(self, text=BTN_PREVIEW, command=self._preview).pack(pady=4)
        customtkinter.CTkButton(self, text=BTN_EXECUTE, command=self._execute).pack(pady=4)

    def _targets(self) -> tuple[CleanupTargetId, ...]:
        return tuple(target for target, var in self._vars.items() if var.get())

    def _preview(self) -> None:
        preview = self._presenter.preview(self._targets())
        self._set(cleanup_preview_text(preview, include_footer=False))

    def _execute(self) -> None:
        preview = self._presenter.preview(self._targets())
        if not self._host.ask("Подтверждение", self._presenter.confirmation(preview)):
            return
        from deskkit.cancel import CancellationToken

        token = CancellationToken()

        def task() -> CleanupResult:
            return self._presenter.execute(
                self._targets(), dry_run=False, confirmed=True, cancel=token
            )

        self._host.run_task(
            task, lambda result: self._set(cleanup_result_text(result)), self._host.notify
        )

    def _set(self, text: str) -> None:
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)

    def refresh(self) -> None:
        pass
