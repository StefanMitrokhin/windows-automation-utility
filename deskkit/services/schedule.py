from __future__ import annotations

import xml.etree.ElementTree as ET
from collections.abc import Sequence

from deskkit.errors import ConfirmationRequired, ScheduleError, ValidationError
from deskkit.models import ScheduleSettings, ScheduleStatus
from deskkit.platform.commands import (
    TASK_NAME_FALLBACK,
    TASK_NAME_PRIMARY,
    quote_task_tr,
    schtasks_create_args,
    schtasks_delete_args,
    schtasks_query_args,
)
from deskkit.platform.protocols import CommandRunner
from deskkit.text import output_tail

_NS = "http://schemas.microsoft.com/windows/2004/02/mit/task"
_DAY_MAP = {
    "Monday": "MON",
    "Tuesday": "TUE",
    "Wednesday": "WED",
    "Thursday": "THU",
    "Friday": "FRI",
    "Saturday": "SAT",
    "Sunday": "SUN",
}
_DAY_ORDER = ("Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday")


class ScheduleService:
    def __init__(self, runner: CommandRunner, cli_prefix: Sequence[str]) -> None:
        self._runner = runner
        self._cli_prefix = cli_prefix

    def status(self) -> ScheduleStatus:
        result = self._runner.run(schtasks_query_args(TASK_NAME_PRIMARY), 60.0)
        if result.exit_code == 0 and result.stdout.strip():
            return self._parse_xml(result.stdout, TASK_NAME_PRIMARY)
        fallback = self._runner.run(schtasks_query_args(TASK_NAME_FALLBACK), 60.0)
        if fallback.exit_code == 0 and fallback.stdout.strip():
            return self._parse_xml(fallback.stdout, TASK_NAME_FALLBACK)
        if result.exit_code != 0 and fallback.exit_code != 0:
            return ScheduleStatus(
                exists=False,
                enabled=False,
                frequency=None,
                weekday=None,
                time=None,
                task_name=None,
                warning=None,
            )
        return ScheduleStatus(
            exists=False,
            enabled=False,
            frequency=None,
            weekday=None,
            time=None,
            task_name=None,
            warning="Пустой ответ планировщика.",
        )

    def create_argv(self, schedule: ScheduleSettings) -> list[str]:
        tr = quote_task_tr(self._cli_prefix)
        return schtasks_create_args(TASK_NAME_PRIMARY, tr, schedule)

    def apply(self, schedule: ScheduleSettings, *, confirmed: bool) -> ScheduleStatus:
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")
        if not schedule.enabled:
            raise ValidationError("В профиле расписание выключено.")
        args = self.create_argv(schedule)
        result = self._runner.run(args, 60.0)
        if result.exit_code != 0:
            fallback_tr = quote_task_tr(self._cli_prefix)
            fallback_args = schtasks_create_args(TASK_NAME_FALLBACK, fallback_tr, schedule)
            fallback = self._runner.run(fallback_args, 60.0)
            if fallback.exit_code != 0:
                tail = output_tail(fallback.stdout, fallback.stderr)
                raise ScheduleError(f"Не удалось создать задачу планировщика. {tail}")
        return self.status()

    def remove(self, *, confirmed: bool) -> None:
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")
        for name in (TASK_NAME_PRIMARY, TASK_NAME_FALLBACK):
            self._runner.run(schtasks_delete_args(name), 60.0)

    def _parse_xml(self, xml_text: str, task_name: str) -> ScheduleStatus:
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError:
            raise ScheduleError("Не удалось прочитать задачу планировщика.") from None
        enabled_el = root.find(f".//{{{_NS}}}Settings/{{{_NS}}}Enabled")
        enabled = (
            enabled_el is not None
            and enabled_el.text is not None
            and enabled_el.text.lower() == "true"
        )
        trigger = root.find(f".//{{{_NS}}}CalendarTrigger")
        time_val: str | None = None
        frequency: str | None = None
        weekday: str | None = None
        warning: str | None = None
        if trigger is not None:
            boundary = trigger.find(f"{{{_NS}}}StartBoundary")
            if boundary is not None and boundary.text and "T" in boundary.text:
                time_val = boundary.text.split("T", maxsplit=1)[1][:5]
            if trigger.find(f"{{{_NS}}}ScheduleByDay") is not None:
                frequency = "daily"
            elif trigger.find(f"{{{_NS}}}ScheduleByWeek") is not None:
                frequency = "weekly"
                days_parent = trigger.find(f".//{{{_NS}}}DaysOfWeek")
                found: list[str] = []
                if days_parent is not None:
                    for day_name in _DAY_ORDER:
                        if days_parent.find(f"{{{_NS}}}{day_name}") is not None:
                            found.append(_DAY_MAP[day_name])
                if found:
                    weekday = found[0]
                if len(found) > 1:
                    warning = "В задаче несколько дней, профиль хранит один."
        return ScheduleStatus(
            exists=True,
            enabled=enabled,
            frequency=frequency,
            weekday=weekday,
            time=time_val,
            task_name=task_name,
            warning=warning,
        )
