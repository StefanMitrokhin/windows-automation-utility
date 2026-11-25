from __future__ import annotations

import queue
import threading
from collections.abc import Callable

import customtkinter

from deskkit.ui.strings import BTN_ABORT, BTN_CONFIRM


def confirm(
    parent: customtkinter.CTk,
    title: str,
    body: str,
    *,
    no_text: str = BTN_ABORT,
    yes_text: str = BTN_CONFIRM,
) -> bool:
    result = {"value": False}
    dialog = customtkinter.CTkToplevel(parent)
    dialog.title(title)
    dialog.transient(parent)
    dialog.grab_set()
    textbox = customtkinter.CTkTextbox(dialog, width=520, height=260)
    textbox.pack(fill="both", expand=True, padx=12, pady=12)
    set_readonly(textbox)
    textbox.configure(state="normal")
    textbox.insert("1.0", body)
    textbox.configure(state="disabled")
    button_row = customtkinter.CTkFrame(dialog, fg_color="transparent")
    button_row.pack(fill="x", padx=12, pady=(0, 12))

    def on_no(_event: object = None) -> None:
        dialog.destroy()

    def on_yes() -> None:
        result["value"] = True
        dialog.destroy()

    no_btn = customtkinter.CTkButton(button_row, text=no_text, command=on_no)
    yes_btn = customtkinter.CTkButton(button_row, text=yes_text, command=on_yes)
    no_btn.pack(side="right", padx=6)
    yes_btn.pack(side="right", padx=6)
    dialog.protocol("WM_DELETE_WINDOW", on_no)
    dialog.bind("<Return>", on_no)
    dialog.bind("<Escape>", on_no)
    no_btn.focus_set()
    dialog.wait_window()
    return result["value"]


def set_readonly(textbox: customtkinter.CTkTextbox) -> None:
    textbox.configure(state="disabled")


class TaskRunner:
    def __init__(self, host: object) -> None:
        self._host = host
        self._queue: queue.Queue[
            tuple[Callable[[], object], Callable[[object], None], Callable[[BaseException], None]]
        ] = queue.Queue()
        self._busy = False

    def run_task(
        self,
        fn: Callable[[], object],
        on_ok: Callable[[object], None],
        on_err: Callable[[BaseException], None],
    ) -> None:
        if self._busy:
            self._host.notify("Дождитесь окончания операции.")  # type: ignore[attr-defined]
            return
        self._busy = True
        self._host.set_busy(True)  # type: ignore[attr-defined]

        def worker() -> None:
            try:
                value = fn()
            except BaseException as exc:
                self._host.after(  # type: ignore[attr-defined]
                    100, lambda e=exc: self._finish_err(e, on_err)
                )
                return
            self._host.after(  # type: ignore[attr-defined]
                100, lambda: self._finish_ok(value, on_ok)
            )

        threading.Thread(target=worker, daemon=True).start()

    def _finish_ok(self, value: object, on_ok: Callable[[object], None]) -> None:
        self._busy = False
        self._host.set_busy(False)  # type: ignore[attr-defined]
        on_ok(value)

    def _finish_err(self, exc: BaseException, on_err: Callable[[BaseException], None]) -> None:
        self._busy = False
        self._host.set_busy(False)  # type: ignore[attr-defined]
        on_err(exc)
