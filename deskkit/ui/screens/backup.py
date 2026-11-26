from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

import customtkinter

from deskkit.cancel import CancellationToken
from deskkit.errors import DeskKitError, ValidationError
from deskkit.models import BackupResult, BackupSettings, ScheduleSettings, ScheduleStatus
from deskkit.text import backup_preview_text, backup_result_text
from deskkit.ui.presenters import BackupPresenter, can_execute
from deskkit.ui.screen_state import launch_control_state
from deskkit.ui.strings import (
    BACKUP_PLAIN_HINT,
    BTN_ADD_FOLDER,
    BTN_BACKUP_NOW,
    BTN_BROWSE,
    BTN_DELETE_SCHEDULE,
    BTN_PREVIEW,
    BTN_REMOVE,
    BTN_SAVE_SCHEDULE,
    CONFIRM_TITLE,
    FREQ_LABELS,
    SCHEDULE_LOGIN_HINT,
    WEEKDAYS,
)

if TYPE_CHECKING:
    from deskkit.ui.app import ScreenHost

FREQ_BY_LABEL = {label: key for key, label in FREQ_LABELS}
WEEKDAY_BY_LABEL = {label: key for key, label in WEEKDAYS}
SCHEDULE_REMOVE_TEXT = "Задача будет удалена, если она есть."


class BackupScreen(customtkinter.CTkFrame):
    def __init__(
        self,
        parent: customtkinter.CTkFrame | customtkinter.CTk,
        presenter: BackupPresenter,
        host: ScreenHost,
    ) -> None:
        super().__init__(parent)
        self._presenter = presenter
        self._host = host
        self._sources: list[str] = []
        self._schedule_status_loaded = False
        self._selected_source: customtkinter.StringVar = customtkinter.StringVar(value="")
        customtkinter.CTkLabel(self, text="Копии", font=("Segoe UI", 20)).pack(
            anchor="w", padx=12, pady=(8, 0)
        )
        src_row = customtkinter.CTkFrame(self, fg_color="transparent")
        src_row.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkButton(src_row, text=BTN_ADD_FOLDER, command=self._add_folder).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(src_row, text=BTN_REMOVE, command=self._remove_folder).pack(
            side="left", padx=4
        )
        self._sources_frame = customtkinter.CTkScrollableFrame(self, height=100)
        self._sources_frame.pack(fill="x", padx=12, pady=4)
        dest_row = customtkinter.CTkFrame(self, fg_color="transparent")
        dest_row.pack(fill="x", padx=12, pady=4)
        self._dest = customtkinter.CTkEntry(dest_row)
        self._dest.pack(side="left", fill="x", expand=True, padx=(0, 8))
        customtkinter.CTkButton(dest_row, text=BTN_BROWSE, command=self._pick_dest).pack(
            side="left"
        )
        keep_row = customtkinter.CTkFrame(self, fg_color="transparent")
        keep_row.pack(fill="x", padx=12, pady=4)
        customtkinter.CTkLabel(keep_row, text="Хранить последних архивов (1–30)").pack(side="left")
        self._keep = customtkinter.CTkEntry(keep_row, width=80)
        self._keep.pack(side="left", padx=8)
        sched_frame = customtkinter.CTkFrame(self, fg_color="transparent")
        sched_frame.pack(fill="x", padx=12, pady=4)
        self._sched_enabled = customtkinter.BooleanVar(value=False)
        customtkinter.CTkSwitch(
            sched_frame, text="По расписанию", variable=self._sched_enabled
        ).pack(side="left", padx=4)
        self._freq = customtkinter.StringVar(value=FREQ_LABELS[1][1])
        customtkinter.CTkOptionMenu(
            sched_frame,
            variable=self._freq,
            values=[label for _, label in FREQ_LABELS],
            command=lambda _: self._sync_weekday_visibility(),
        ).pack(side="left", padx=4)
        self._weekday = customtkinter.StringVar(value=WEEKDAYS[0][1])
        self._weekday_menu = customtkinter.CTkOptionMenu(
            sched_frame,
            variable=self._weekday,
            values=[label for _, label in WEEKDAYS],
        )
        self._weekday_menu.pack(side="left", padx=4)
        self._time = customtkinter.CTkEntry(sched_frame, width=70)
        self._time.insert(0, "09:00")
        self._time.pack(side="left", padx=4)
        customtkinter.CTkLabel(
            self,
            text=SCHEDULE_LOGIN_HINT,
            font=("Segoe UI", 11),
            text_color=("gray30", "gray70"),
        ).pack(anchor="w", padx=12)
        customtkinter.CTkLabel(
            self,
            text=BACKUP_PLAIN_HINT,
            font=("Segoe UI", 11),
            text_color=("gray30", "gray70"),
            justify="left",
        ).pack(anchor="w", padx=12, pady=(0, 4))
        self._progress = customtkinter.CTkProgressBar(self)
        self._progress.pack_forget()
        self._output = customtkinter.CTkTextbox(self, height=120)
        self._output.pack(fill="x", padx=12, pady=8)
        self._status = customtkinter.CTkLabel(self, text="", anchor="w")
        self._status.pack(fill="x", padx=12)
        row = customtkinter.CTkFrame(self, fg_color="transparent")
        row.pack(fill="x", padx=12, pady=8)
        self._preview_btn = customtkinter.CTkButton(row, text=BTN_PREVIEW, command=self._preview)
        self._preview_btn.pack(side="left", padx=4)
        self._run_btn = customtkinter.CTkButton(row, text=BTN_BACKUP_NOW, command=self._run)
        self._run_btn.pack(side="left", padx=4)
        customtkinter.CTkButton(row, text=BTN_SAVE_SCHEDULE, command=self._save_schedule).pack(
            side="left", padx=4
        )
        customtkinter.CTkButton(row, text=BTN_DELETE_SCHEDULE, command=self._delete_schedule).pack(
            side="left", padx=4
        )

    def _sync_weekday_visibility(self) -> None:
        if self._freq.get() == FREQ_LABELS[0][1]:
            self._weekday_menu.pack_forget()
        else:
            self._weekday_menu.pack(side="left", padx=4)

    def _rebuild_sources(self) -> None:
        for child in self._sources_frame.winfo_children():
            child.destroy()
        for idx, path in enumerate(self._sources):
            customtkinter.CTkRadioButton(
                self._sources_frame,
                text=path,
                variable=self._selected_source,
                value=path,
                command=lambda p=path: self._selected_source.set(p),
            ).pack(anchor="w")
            if idx == 0:
                self._selected_source.set(path)

    def _add_folder(self) -> None:
        picked = self._host.pick_directory()
        if not picked:
            return
        if picked in self._sources:
            self._host.notify("Папка уже в списке.")
            return
        self._sources.append(picked)
        self._rebuild_sources()

    def _remove_folder(self) -> None:
        path = self._selected_source.get()
        if path and path in self._sources:
            self._sources.remove(path)
            self._rebuild_sources()

    def _pick_dest(self) -> None:
        picked = self._host.pick_directory()
        if picked:
            self._dest.delete(0, "end")
            self._dest.insert(0, picked)

    def _keep_last(self) -> int:
        try:
            return int(self._keep.get().strip())
        except ValueError as exc:
            raise ValidationError("Укажите число архивов от 1 до 30.") from exc

    def _schedule_settings(self) -> ScheduleSettings:
        freq = FREQ_BY_LABEL[self._freq.get()]
        weekday = WEEKDAY_BY_LABEL.get(self._weekday.get(), "MON")
        if freq == "daily":
            weekday = "MON"
        return ScheduleSettings(
            self._sched_enabled.get(),
            freq,
            weekday,
            self._time.get().strip() or "09:00",
        )

    def _paths(self) -> tuple[Path, ...]:
        return tuple(Path(s) for s in self._sources)

    def _dest_path(self) -> Path:
        return Path(self._dest.get().strip() or ".")

    def _write_profile(self) -> None:
        store = self._presenter._context.profile_store
        profile = store.load()
        backup = replace(
            profile.backup,
            sources=tuple(self._sources),
            destination=self._dest.get().strip() or None,
            keep_last=self._keep_last(),
            schedule=self._schedule_settings(),
        )
        store.save(replace(profile, backup=backup))

    def _preview(self) -> None:
        try:
            preview = self._presenter.preview(self._paths(), self._dest_path(), self._keep_last())
        except DeskKitError as exc:
            self._host.notify(str(exc))
            return
        self._set_output(backup_preview_text(preview, include_footer=False))

    def _run(self) -> None:
        if self._host.view_only() or not can_execute(self._host.view_only()):
            self._host.notify("Включён режим просмотра.")
            return
        try:
            preview = self._presenter.preview(self._paths(), self._dest_path(), self._keep_last())
        except DeskKitError as exc:
            self._host.notify(str(exc))
            return
        if not self._host.ask(CONFIRM_TITLE, self._presenter.confirmation(preview)):
            self._host.notify("Действие отменено.")
            return

        def task(cancel: CancellationToken) -> BackupResult:
            return self._presenter.execute(
                self._paths(),
                self._dest_path(),
                self._keep_last(),
                dry_run=False,
                confirmed=True,
                cancel=cancel,
            )

        self._host.run_task(
            task, lambda result: self._set_output(backup_result_text(result)), self._host.notify
        )

    def _save_schedule(self) -> None:
        try:
            self._presenter.preview(self._paths(), self._dest_path(), self._keep_last())
        except DeskKitError as exc:
            self._host.notify(str(exc))
            return
        settings = self._schedule_settings()
        if settings.enabled:
            text = self._presenter.schedule_text(settings)
            if not self._host.ask(CONFIRM_TITLE, text):
                self._host.notify("Действие отменено.")
                return
        else:
            if not self._host.ask(CONFIRM_TITLE, SCHEDULE_REMOVE_TEXT):
                self._host.notify("Действие отменено.")
                return
        self._write_profile()
        try:
            status = self._presenter.save_schedule(settings, confirmed=True)
            self._apply_schedule_status(status)
        except DeskKitError as exc:
            self._host.notify(str(exc))

    def _delete_schedule(self) -> None:
        if not self._host.ask(CONFIRM_TITLE, SCHEDULE_REMOVE_TEXT):
            return
        self._presenter.remove_schedule(confirmed=True)
        store = self._presenter._context.profile_store
        profile = store.load()
        schedule = replace(profile.backup.schedule, enabled=False)
        backup = replace(profile.backup, schedule=schedule)
        store.save(replace(profile, backup=backup))
        self._sched_enabled.set(False)
        self._update_schedule_status()

    def _apply_schedule_status(self, status: ScheduleStatus) -> None:
        extra = status.warning or ""
        if status.exists and status.task_name:
            extra = (extra + " " + status.task_name).strip()
        self._status.configure(text=extra)
        if status.warning:
            self._host.notify(status.warning)

    def _update_schedule_status(self) -> None:
        try:
            self._apply_schedule_status(self._presenter.schedule_status())
        except DeskKitError as exc:
            self._host.notify(str(exc))

    def sync_busy_progress(self, show_progress: bool) -> None:
        if show_progress:
            self._progress.pack(fill="x", padx=12, pady=4, before=self._output)
            if hasattr(self._progress, "start"):
                self._progress.start()
            else:
                self._progress.set(0.5)
        else:
            if hasattr(self._progress, "stop"):
                self._progress.stop()
            self._progress.pack_forget()

    def sync_launch_control(self) -> None:
        self._run_btn.configure(
            state=launch_control_state(view_only=self._host.view_only(), busy=self._host.is_busy())
        )

    def _set_output(self, text: str) -> None:
        self._output.configure(state="normal")
        self._output.delete("1.0", "end")
        self._output.insert("1.0", text)
        self._output.configure(state="disabled")

    def refresh(self) -> None:
        backup: BackupSettings = self._presenter._context.profile_store.load().backup
        self._sources = list(backup.sources)
        self._rebuild_sources()
        self._dest.delete(0, "end")
        if backup.destination:
            self._dest.insert(0, backup.destination)
        self._keep.delete(0, "end")
        self._keep.insert(0, str(backup.keep_last))
        self._sched_enabled.set(backup.schedule.enabled)
        freq_label = next(label for key, label in FREQ_LABELS if key == backup.schedule.frequency)
        self._freq.set(freq_label)
        day_label = next(
            (label for key, label in WEEKDAYS if key == backup.schedule.weekday),
            WEEKDAYS[0][1],
        )
        self._weekday.set(day_label)
        self._time.delete(0, "end")
        self._time.insert(0, backup.schedule.time)
        self._sync_weekday_visibility()
        if not self._schedule_status_loaded:
            self._update_schedule_status()
            self._schedule_status_loaded = True
        self.sync_launch_control()
