from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter

from deskkit.errors import DeskKitError, ValidationError
from deskkit.models import InstallReport, InstallStatus
from deskkit.text import install_preview_text, install_report_text, profile_summary_text
from deskkit.ui.presenters import ProfilePresenter, can_execute
from deskkit.ui.strings import (
    BTN_APPLY_INSTALL,
    BTN_PROFILE_EXPORT,
    BTN_PROFILE_IMPORT,
    BTN_PROFILE_INIT,
    CONFIRM_TITLE,
    PROFILE_HINT,
)

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost


class ProfileScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: ProfilePresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        customtkinter.CTkLabel(self, text="Профиль", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        customtkinter.CTkLabel(
            self,
            text=PROFILE_HINT,
            font=("Segoe UI", 13),
            text_color=("gray30", "gray70"),
            justify="left",
        ).pack(anchor="w", padx=12, pady=4)
        self._path = customtkinter.CTkEntry(self)
        self._path.pack(fill="x", padx=12, pady=4)
        self._text = customtkinter.CTkTextbox(self, height=260)
        self._text.pack(fill="both", expand=True, padx=12, pady=8)
        row1 = customtkinter.CTkFrame(self, fg_color="transparent")
        row1.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkButton(row1, text=BTN_PROFILE_INIT, command=self._init).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(row1, text=BTN_PROFILE_IMPORT, command=self._import).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(row1, text=BTN_PROFILE_EXPORT, command=self._export).pack(
            side="left", padx=4
        )
        self._apply_btn = customtkinter.CTkButton(
            row1, text=BTN_APPLY_INSTALL, command=self._apply_install
        )
        self._apply_btn.pack(side="left", padx=4)

    def _init(self) -> None:
        try:
            self._presenter.init_default()
            self.refresh()
        except ValidationError as exc:
            self._host.notify(str(exc))

    def _import(self) -> None:
        path = self._host.pick_open()
        if not path:
            return
        try:
            profile = self._presenter.parse_file(Path(path))
        except (DeskKitError, ValidationError, OSError) as exc:
            self._host.notify(str(exc))
            return
        body = profile_summary_text(profile)
        if not self._host.ask(CONFIRM_TITLE, body):
            return
        try:
            self._presenter.import_from(Path(path), confirmed=True)
            self.refresh()
        except DeskKitError as exc:
            self._host.notify(str(exc))

    def _export(self) -> None:
        path = self._host.pick_save(".json", "deskkit-profile.json")
        if not path:
            return
        try:
            self._presenter.export_to(Path(path))
            self._host.notify(f"Сохранено: {path}")
        except OSError as exc:
            self._host.notify(str(exc))

    def _apply_install(self) -> None:
        if self._host.view_only() or not can_execute(self._host.view_only()):
            self._host.notify("Включён режим просмотра.")
            return
        profile = self._presenter.load()
        preview = self._presenter._context.installer.preview(
            profile.install.package_ids,
            profile.install.scope,
        )
        from deskkit.ui.strings import CONFIRM_LEAD

        confirm_body = CONFIRM_LEAD + "\n\n" + install_preview_text(preview, include_footer=False)
        if not self._host.ask(CONFIRM_TITLE, confirm_body):
            self._host.notify("Действие отменено.")
            return

        def task() -> InstallReport:
            return self._presenter.apply_install(
                dry_run=False,
                confirmed=True,
                cancel=self._host.cancel_token(),
            )

        def done(report: InstallReport) -> None:
            text = install_report_text(report)
            if any(item.status == InstallStatus.ADMIN_REQUIRED for item in report.items):
                text += "\n" + "Требуются права администратора."
            self._host.notify(text[:200])

        self._host.run_task(task, done, self._host.notify)

    def refresh(self) -> None:
        self._path.configure(state="normal")
        self._path.delete(0, "end")
        self._path.insert(0, str(self._presenter.path()))
        self._path.configure(state="disabled")
        self._text.configure(state="normal")
        self._text.delete("1.0", "end")
        self._text.insert("1.0", self._presenter.text())
        self._text.configure(state="disabled")
        apply_state = "disabled" if self._host.view_only() else "normal"
        self._apply_btn.configure(state=apply_state)
