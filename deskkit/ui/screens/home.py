from __future__ import annotations

import customtkinter

from deskkit.ui.strings import SAFETY_LINES


class HomeScreen(customtkinter.CTkFrame):
    def __init__(self, parent, presenter, host) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        customtkinter.CTkLabel(self, text="Обзор", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=8
        )
        customtkinter.CTkLabel(
            self, text="Настройка и обслуживание этого компьютера", font=("Segoe UI", 13)
        ).pack(anchor="w", padx=12)
        self._text = customtkinter.CTkTextbox(self, height=220)
        self._text.pack(fill="both", expand=True, padx=12, pady=8)
        for line in SAFETY_LINES:
            customtkinter.CTkLabel(self, text=line, anchor="w").pack(anchor="w", padx=12)

    def refresh(self) -> None:
        status = self._presenter.status()
        lines = [
            f"winget: {'найден' if status.winget_found else 'не найден'}",
            status.winget_path or "",
            f"Профиль: {'найден' if status.profile_exists else 'ещё не создан'}",
            f"Расписание: {'включено' if status.schedule_enabled else 'выключено'}",
            status.last_log_line,
        ]
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", "\n".join(lines))
        self._text.configure(state="disabled")
