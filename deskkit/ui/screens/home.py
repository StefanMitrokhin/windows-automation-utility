from __future__ import annotations

from typing import TYPE_CHECKING

import customtkinter

from deskkit import __version__
from deskkit.ui.presenters import HomePresenter
from deskkit.ui.strings import SAFETY_LINES

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost

FOOTER = f"Stefan Mitrokhin · GitHub StefanMitrokhin · MIT · версия {__version__}"


class HomeScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: HomePresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        customtkinter.CTkLabel(self, text="Обзор", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        customtkinter.CTkLabel(
            self,
            text="Настройка и обслуживание этого компьютера",
            font=("Segoe UI", 13),
            text_color=("gray30", "gray70"),
        ).pack(anchor="w", padx=12, pady=(0, 8))
        grid = customtkinter.CTkFrame(self, fg_color="transparent")
        grid.pack(fill="x", padx=12, pady=8)
        grid.grid_columnconfigure((0, 1), weight=1, uniform="cards")
        grid.grid_rowconfigure((0, 1), weight=1)
        self._card_bodies: dict[str, customtkinter.CTkLabel] = {}
        card_defs = (
            ("programs", "Программы", "install", "К установке"),
            ("profile", "Профиль", "profile", "К профилю"),
            ("backup", "Копии", "backup", "К копиям"),
            ("rights", "Права", None, None),
        )
        for idx, (key, title, nav, btn_text) in enumerate(card_defs):
            frame = customtkinter.CTkFrame(grid)
            frame.grid(row=idx // 2, column=idx % 2, sticky="nsew", padx=6, pady=6)
            customtkinter.CTkLabel(frame, text=title, font=("Segoe UI", 14, "bold")).pack(
                anchor="w", padx=8, pady=(8, 4)
            )
            body = customtkinter.CTkLabel(frame, text="", anchor="w", justify="left")
            body.pack(anchor="w", padx=8, pady=4)
            self._card_bodies[key] = body
            if nav and btn_text:
                customtkinter.CTkButton(
                    frame,
                    text=btn_text,
                    command=lambda n=nav: self._host.show(n),
                ).pack(anchor="w", padx=8, pady=(0, 8))
            elif key == "rights":
                customtkinter.CTkLabel(
                    frame,
                    text="Для обычной работы права администратора не нужны.",
                    anchor="w",
                    justify="left",
                ).pack(anchor="w", padx=8, pady=(0, 8))

        for line in SAFETY_LINES:
            customtkinter.CTkLabel(self, text=line, anchor="w").pack(anchor="w", padx=12)
        customtkinter.CTkLabel(self, text=FOOTER, text_color=("gray30", "gray70")).pack(
            anchor="w", padx=12, pady=(8, 12)
        )

    def refresh(self) -> None:
        status = self._presenter.status()
        if status.winget_found:
            winget = f"winget: найден\n{status.winget_path}"
        else:
            winget = "winget: не найден"
        self._card_bodies["programs"].configure(text=winget)
        profile = "Файл настроек найден" if status.profile_exists else "Файл настроек ещё не создан"
        self._card_bodies["profile"].configure(text=profile)
        schedule_on = status.schedule_exists and status.schedule_enabled
        sched = "Расписание включено" if schedule_on else "Расписание выключено"
        self._card_bodies["backup"].configure(text=sched)
        rights = "Администратор" if status.is_admin else "Обычные права"
        self._card_bodies["rights"].configure(text=rights)
