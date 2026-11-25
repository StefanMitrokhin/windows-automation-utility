from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime

from deskkit.models import DiskInfo, SoftwareEntry, SystemSnapshot
from deskkit.services.report import ReportService
from deskkit.text import format_bytes, report_summary_text
from tests.fakes import FakeClock, FakeSoftware, FakeSystem


def _snapshot() -> SystemSnapshot:
    return SystemSnapshot(
        collected_at=datetime(2026, 1, 1, 12, 0, tzinfo=UTC),
        hostname="OFFICE-PC",
        os_name="Windows",
        os_version="11",
        os_build="1",
        machine="AMD64",
        cpu_model="CPU",
        cpu_physical=1,
        cpu_logical=2,
        cpu_freq_mhz=None,
        ram_total_bytes=1024,
        ram_available_bytes=512,
        disks=(DiskInfo("C:", "C:\\", "NTFS", 1024, 512, 512, True),),
        software=(SoftwareEntry("<script>", "1", "P", "20260101"),),
    )


def test_html_escapes_and_has_sections(tmp_path) -> None:
    service = ReportService(FakeSystem(), FakeSoftware(), FakeClock())
    html = service.render_html(_snapshot())
    assert "&lt;script&gt;" in html
    assert "Система" in html and "Диски" in html and "Установленные программы" in html
    assert "<script>" not in html


def test_html_utf8_note() -> None:
    service = ReportService(FakeSystem(), FakeSoftware(), FakeClock())
    assert "Никуда не отправляется." in service.render_html(_snapshot())


def test_empty_software_row() -> None:
    snap = replace(_snapshot(), software=())
    service = ReportService(FakeSystem(), FakeSoftware(), FakeClock())
    assert "Программы не найдены" in service.render_html(snap)


def test_xlsx_sheets_and_headers(tmp_path) -> None:
    from openpyxl import load_workbook

    service = ReportService(FakeSystem(), FakeSoftware(), FakeClock())
    out = tmp_path / "r.xlsx"
    service.write_xlsx(_snapshot(), out)
    wb = load_workbook(out)
    assert wb.sheetnames == ["Система", "Диски", "Программы"]
    assert wb["Программы"]["A1"].value == "Имя"


def test_xlsx_disk_bytes(tmp_path) -> None:
    from openpyxl import load_workbook

    service = ReportService(FakeSystem(), FakeSoftware(), FakeClock())
    out = tmp_path / "r.xlsx"
    service.write_xlsx(_snapshot(), out)
    wb = load_workbook(out)
    row = next(wb["Диски"].iter_rows(min_row=2, max_row=2))
    values = [cell.value for cell in row]
    assert 1024 in values
    assert format_bytes(1024) in values


def test_summary_contains_hostname() -> None:
    assert "OFFICE-PC" in report_summary_text(_snapshot())
