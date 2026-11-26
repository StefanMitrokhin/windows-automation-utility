from __future__ import annotations

import html
from pathlib import Path

from openpyxl import Workbook
from openpyxl.styles import Font

from deskkit import __version__
from deskkit.models import SystemSnapshot
from deskkit.platform.protocols import Clock, SoftwareGateway, SystemGateway
from deskkit.text import format_bytes


class ReportService:
    def __init__(
        self,
        system: SystemGateway,
        software: SoftwareGateway,
        clock: Clock,
    ) -> None:
        self._system = system
        self._software = software
        self._clock = clock

    def collect(self) -> SystemSnapshot:
        snapshot = self._system.snapshot_base()
        programs = self._software.list_installed()
        return SystemSnapshot(
            collected_at=snapshot.collected_at,
            hostname=snapshot.hostname,
            os_name=snapshot.os_name,
            os_version=snapshot.os_version,
            os_build=snapshot.os_build,
            machine=snapshot.machine,
            cpu_model=snapshot.cpu_model,
            cpu_physical=snapshot.cpu_physical,
            cpu_logical=snapshot.cpu_logical,
            cpu_freq_mhz=snapshot.cpu_freq_mhz,
            ram_total_bytes=snapshot.ram_total_bytes,
            ram_available_bytes=snapshot.ram_available_bytes,
            disks=snapshot.disks,
            software=programs,
        )

    def render_html(self, snapshot: SystemSnapshot) -> str:
        ram_text = (
            f"{format_bytes(snapshot.ram_available_bytes)} свободно из "
            f"{format_bytes(snapshot.ram_total_bytes)}"
        )
        cpu_text = (
            f"{html.escape(snapshot.cpu_model)} ({snapshot.cpu_physical} физ. / "
            f"{snapshot.cpu_logical} лог.)"
        )
        if snapshot.cpu_freq_mhz is not None:
            cpu_text += f" {snapshot.cpu_freq_mhz:.0f} МГц"
        disk_rows = []
        for disk in snapshot.disks:
            if disk.available:
                disk_rows.append(
                    "<tr>"
                    f"<td>{html.escape(disk.mountpoint)}</td>"
                    f"<td>{html.escape(format_bytes(disk.total_bytes))}</td>"
                    f"<td>{html.escape(format_bytes(disk.free_bytes))}</td>"
                    "</tr>"
                )
            else:
                disk_rows.append(
                    f"<tr><td>{html.escape(disk.mountpoint)}</td><td>нет данных</td><td></td></tr>"
                )
        software_rows = []
        if snapshot.software:
            for entry in snapshot.software:
                software_rows.append(
                    "<tr>"
                    f"<td>{html.escape(entry.name)}</td>"
                    f"<td>{html.escape(entry.version)}</td>"
                    f"<td>{html.escape(entry.publisher)}</td>"
                    f"<td>{html.escape(entry.install_date)}</td>"
                    "</tr>"
                )
        else:
            software_rows.append(
                "<tr><td>Программы не найдены</td><td></td><td></td><td></td></tr>"
            )
        return f"""<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Отчёт DeskKit</title>
<style>
body {{ font-family: Segoe UI, sans-serif; margin: 24px; color: #1a1a1a; }}
h1 {{ font-size: 22px; }}
h2 {{ font-size: 18px; margin-top: 28px; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #cccccc; padding: 6px 8px; text-align: left; vertical-align: top; }}
th {{ background: #1f6aa5; color: #ffffff; }}
</style>
</head>
<body>
<h1>Отчёт DeskKit</h1>
<p>Собран локально {snapshot.collected_at:%Y-%m-%d %H:%M}. Никуда не отправляется.</p>
<h2>Система</h2>
<table>
<tr><th>Параметр</th><th>Значение</th></tr>
<tr><td>Компьютер</td><td>{html.escape(snapshot.hostname)}</td></tr>
<tr><td>Система</td><td>{html.escape(snapshot.os_name)} {html.escape(snapshot.os_version)}</td></tr>
<tr><td>Сборка</td><td>{html.escape(snapshot.os_build)}</td></tr>
<tr><td>Разрядность</td><td>{html.escape(snapshot.machine)}</td></tr>
<tr><td>Процессор</td><td>{cpu_text}</td></tr>
<tr><td>Память</td><td>{html.escape(ram_text)}</td></tr>
</table>
<h2>Диски</h2>
<table>
<tr><th>Том</th><th>Всего</th><th>Свободно</th></tr>
{"".join(disk_rows)}
</table>
<h2>Установленные программы</h2>
<table>
<tr><th>Имя</th><th>Версия</th><th>Издатель</th><th>Дата</th></tr>
{"".join(software_rows)}
</table>
<p>DeskKit {html.escape(__version__)}. Отчёт описывает только этот компьютер.</p>
</body>
</html>
"""

    def write_html(self, snapshot: SystemSnapshot, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(self.render_html(snapshot), encoding="utf-8")

    def write_xlsx(self, snapshot: SystemSnapshot, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        wb = Workbook()
        ws_system = wb.active
        ws_system.title = "Система"
        ws_system.append(["Параметр", "Значение"])
        ws_system.append(["Компьютер", snapshot.hostname])
        ws_system.append(["Система", f"{snapshot.os_name} {snapshot.os_version}"])
        ws_system.append(["Сборка", snapshot.os_build])
        ws_system.append(["Разрядность", snapshot.machine])
        cpu = f"{snapshot.cpu_model} ({snapshot.cpu_physical} физ. / {snapshot.cpu_logical} лог.)"
        if snapshot.cpu_freq_mhz is not None:
            cpu += f" {snapshot.cpu_freq_mhz:.0f} МГц"
        ws_system.append(["Процессор", cpu])
        ws_system.append(
            [
                "Память",
                (
                    f"{format_bytes(snapshot.ram_available_bytes)} свободно из "
                    f"{format_bytes(snapshot.ram_total_bytes)}"
                ),
            ]
        )
        for row in ws_system.iter_rows(min_row=1, max_row=1):
            for cell in row:
                cell.font = Font(bold=True)
        ws_system.freeze_panes = "A2"
        ws_system.column_dimensions["A"].width = 28
        ws_system.column_dimensions["B"].width = 36

        ws_disks = wb.create_sheet("Диски")
        ws_disks.append(
            [
                "Диск",
                "Том",
                "Файловая система",
                "Всего байт",
                "Занято байт",
                "Свободно байт",
                "Всего",
                "Свободно",
            ]
        )
        for disk in snapshot.disks:
            if disk.available:
                ws_disks.append(
                    [
                        disk.device,
                        disk.mountpoint,
                        disk.fstype,
                        disk.total_bytes,
                        disk.used_bytes,
                        disk.free_bytes,
                        format_bytes(disk.total_bytes),
                        format_bytes(disk.free_bytes),
                    ]
                )
            else:
                ws_disks.append(
                    [
                        disk.device,
                        disk.mountpoint,
                        disk.fstype,
                        0,
                        0,
                        0,
                        "нет данных",
                        "",
                    ]
                )
        for row in ws_disks.iter_rows(min_row=1, max_row=1):
            for cell in row:
                cell.font = Font(bold=True)
        for col in ws_disks.columns:
            ws_disks.column_dimensions[col[0].column_letter].width = 36
        ws_disks.column_dimensions["A"].width = 28

        ws_programs = wb.create_sheet("Программы")
        ws_programs.append(["Имя", "Версия", "Издатель", "Дата"])
        for entry in snapshot.software:
            ws_programs.append([entry.name, entry.version, entry.publisher, entry.install_date])
        for row in ws_programs.iter_rows(min_row=1, max_row=1):
            for cell in row:
                cell.font = Font(bold=True)
        ws_programs.column_dimensions["A"].width = 28
        for col in ("B", "C", "D"):
            ws_programs.column_dimensions[col].width = 36

        wb.save(path)
