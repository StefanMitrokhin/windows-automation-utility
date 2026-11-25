from __future__ import annotations

import pytest

from deskkit.errors import ConfirmationRequired, ValidationError
from deskkit.models import CommandResult, ScheduleSettings
from deskkit.services.schedule import ScheduleService
from tests.fakes import FakeRunner

WEEKLY_XML = """<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Settings>
    <Enabled>true</Enabled>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-19T09:00:00</StartBoundary>
      <ScheduleByWeek>
        <DaysOfWeek>
          <Monday />
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
</Task>
"""

DAILY_XML = WEEKLY_XML.replace(
    """<ScheduleByWeek>
        <DaysOfWeek>
          <Monday />
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>""",
    "<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>",
)


def test_parse_weekly_xml() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 0, WEEKLY_XML, "", False, False))
    status = ScheduleService(runner, ["deskkit-cli"]).status()
    assert status.exists
    assert status.frequency == "weekly"
    assert status.weekday == "MON"
    assert status.time == "09:00"
    assert status.enabled is True


def test_parse_daily_xml() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 0, DAILY_XML, "", False, False))
    status = ScheduleService(runner, ["deskkit-cli"]).status()
    assert status.frequency == "daily"
    assert status.weekday is None


def test_missing_task() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 1, "", "", False, False))
    runner.enqueue(CommandResult((), 1, "", "", False, False))
    status = ScheduleService(runner, ["deskkit-cli"]).status()
    assert status.exists is False


def test_fallback_name() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 1, "", "", False, False))
    runner.enqueue(CommandResult((), 0, WEEKLY_XML, "", False, False))
    status = ScheduleService(runner, ["deskkit-cli"]).status()
    assert status.task_name == "DeskKit Backup"


def test_create_uses_primary_name() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    runner.enqueue(CommandResult((), 0, WEEKLY_XML, "", False, False))
    schedule = ScheduleSettings(True, "weekly", "MON", "09:00")
    ScheduleService(runner, ["deskkit-cli"]).apply(schedule, confirmed=True)
    assert r"\DeskKit\Backup" in " ".join(runner.calls[0][0])


def test_create_requires_confirmation() -> None:
    runner = FakeRunner()
    with pytest.raises(ConfirmationRequired):
        ScheduleService(runner, ["deskkit-cli"]).apply(
            ScheduleSettings(True, "weekly", "MON", "09:00"), confirmed=False
        )
    assert not runner.calls


def test_disabled_schedule_rejected() -> None:
    runner = FakeRunner()
    with pytest.raises(ValidationError) as exc:
        ScheduleService(runner, ["deskkit-cli"]).apply(
            ScheduleSettings(False, "weekly", "MON", "09:00"), confirmed=True
        )
    assert str(exc.value) == "В профиле расписание выключено."


def test_remove_deletes_both() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 1, "", "", False, False))
    runner.enqueue(CommandResult((), 1, "", "", False, False))
    ScheduleService(runner, ["deskkit-cli"]).remove(confirmed=True)
    assert len(runner.calls) == 2


def test_empty_stdout_warning() -> None:
    runner = FakeRunner()
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    runner.enqueue(CommandResult((), 0, "", "", False, False))
    status = ScheduleService(runner, ["deskkit-cli"]).status()
    assert status.warning == "Пустой ответ планировщика."


def test_argv_has_no_ru_or_system() -> None:
    argv = ScheduleService(FakeRunner(), ["deskkit-cli"]).create_argv(
        ScheduleSettings(True, "weekly", "MON", "09:00")
    )
    joined = " ".join(argv)
    assert "/RU" not in joined and "SYSTEM" not in joined
