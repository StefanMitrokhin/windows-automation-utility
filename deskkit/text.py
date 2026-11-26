from __future__ import annotations

from collections.abc import Sequence

from deskkit.models import (
    BackupPreview,
    BackupResult,
    CleanupPreview,
    CleanupResult,
    CleanupTargetId,
    InstallPreview,
    InstallReport,
    InstallScope,
    InstallStatus,
    Profile,
    StartupEntry,
    StartupSource,
    SystemSnapshot,
)


def format_bytes(num: int) -> str:
    if num < 0:
        raise ValueError("Отрицательный размер.")
    units = ("Б", "КБ", "МБ", "ГБ", "ТБ")
    value = float(num)
    for unit in units:
        if value < 1024 or unit == "ТБ":
            if unit == "Б":
                return f"{int(value)} {unit}"
            return f"{value:.1f}".replace(".", ",") + f" {unit}"
        value /= 1024
    return f"{value:.1f}".replace(".", ",") + " ТБ"


def confirmation_footer() -> str:
    return "Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено."


def install_scope_label(scope: InstallScope) -> str:
    if scope == InstallScope.USER:
        return "для текущего пользователя"
    return "как решит winget"


def install_preview_text(preview: InstallPreview, *, include_footer: bool) -> str:
    lines: list[str] = []
    if not preview.winget_found:
        lines.extend(["winget не найден. Установка не начнётся.", ""])
    lines.append(f"Будет установлено: {len(preview.package_ids)}")
    lines.append(f"Область: {install_scope_label(preview.scope)}")
    for index, (name, package_id) in enumerate(
        zip(preview.names, preview.package_ids, strict=True), start=1
    ):
        lines.append(f"{index}. {name} ({package_id})")
    if include_footer:
        lines.append(confirmation_footer())
    return "\n".join(lines) + "\n"


def _install_status_tail(item_message: str, status: InstallStatus) -> str:
    if status == InstallStatus.SUCCESS:
        return "установлено"
    if status == InstallStatus.SKIPPED_INSTALLED:
        return "уже установлен, пропуск"
    if status == InstallStatus.ADMIN_REQUIRED:
        return "нужны права администратора"
    return f"ошибка: {item_message}"


def install_report_text(report: InstallReport) -> str:
    total = len(report.items)
    lines: list[str] = []
    for index, item in enumerate(report.items, start=1):
        tail = _install_status_tail(item.message, item.status)
        lines.append(f"[{index}/{total}] {item.name} — {tail}")
    if report.dry_run:
        lines.append("Режим просмотра: команды winget не запускались.")
    elif report.cancelled:
        lines.append("Остановлено.")
    else:
        installed = sum(1 for i in report.items if i.status == InstallStatus.SUCCESS)
        skipped = sum(1 for i in report.items if i.status == InstallStatus.SKIPPED_INSTALLED)
        failed = sum(1 for i in report.items if i.status == InstallStatus.FAILED)
        lines.append(f"Готово: установлено {installed}, пропущено {skipped}, ошибок {failed}")
    return "\n".join(lines) + "\n"


def cleanup_target_label(target: CleanupTargetId) -> str:
    labels = {
        CleanupTargetId.USER_TEMP: "Временные файлы пользователя",
        CleanupTargetId.WINDOWS_TEMP: "Временные файлы Windows",
        CleanupTargetId.RECYCLE_BIN: "Корзина",
        CleanupTargetId.CHROME_CACHE: "Кэш Google Chrome",
        CleanupTargetId.EDGE_CACHE: "Кэш Microsoft Edge",
        CleanupTargetId.FIREFOX_CACHE: "Кэш Firefox",
    }
    return labels[target]


def cleanup_preview_text(preview: CleanupPreview, *, include_footer: bool) -> str:
    lines: list[str] = []
    lines.append(f"К очистке: {format_bytes(preview.total_bytes)} в {preview.total_files} файлах")
    for target in preview.targets:
        label = cleanup_target_label(target.target)
        if target.absent:
            lines.append(f"{label}: папка не найдена, пропуск")
        else:
            lines.append(f"{label}: {target.file_count} файлов, {format_bytes(target.byte_count)}")
        for warning in target.warnings:
            lines.append(f"Предупреждение: {warning}")
    if include_footer:
        lines.append(confirmation_footer())
    return "\n".join(lines) + "\n"


def cleanup_result_text(result: CleanupResult) -> str:
    if result.dry_run:
        text = cleanup_preview_text(result.preview, include_footer=True)
        return text + "Режим просмотра: файлы не удалялись.\n"
    lines = [
        f"Удалено файлов: {result.deleted_files}",
        f"Освобождено: {format_bytes(result.freed_bytes)}",
        f"Пропущено занятых файлов: {result.skipped_locked}",
    ]
    lines.extend(f"Ошибка: {err}" for err in result.errors)
    return "\n".join(lines) + "\n"


def report_summary_text(snapshot: SystemSnapshot) -> str:
    lines = [
        f"Компьютер: {snapshot.hostname}",
        (f"Система: {snapshot.os_name} {snapshot.os_version} сборка {snapshot.os_build}"),
    ]
    cpu_line = (
        f"Процессор: {snapshot.cpu_model} "
        f"({snapshot.cpu_physical} физ. / {snapshot.cpu_logical} лог.)"
    )
    if snapshot.cpu_freq_mhz is not None:
        cpu_line += f" {snapshot.cpu_freq_mhz:.0f} МГц"
    lines.append(cpu_line)
    lines.append(
        "Память: "
        f"{format_bytes(snapshot.ram_available_bytes)} свободно из "
        f"{format_bytes(snapshot.ram_total_bytes)}"
    )
    lines.append("Диски:")
    for disk in snapshot.disks:
        if disk.available:
            lines.append(
                f"{disk.mountpoint} {format_bytes(disk.free_bytes)} свободно из "
                f"{format_bytes(disk.total_bytes)}"
            )
        else:
            lines.append(f"{disk.mountpoint} нет данных")
    lines.append(f"Программ в списке: {len(snapshot.software)}")
    return "\n".join(lines) + "\n"


def startup_source_label(source: StartupSource) -> str:
    labels = {
        StartupSource.HKCU_RUN: "Реестр пользователя",
        StartupSource.HKLM_RUN: "Общий реестр",
        StartupSource.USER_STARTUP: "Папка пользователя",
        StartupSource.COMMON_STARTUP: "Общая папка",
    }
    return labels[source]


def startup_list_text(entries: Sequence[StartupEntry]) -> str:
    if not entries:
        return "Автозагрузка пуста.\n"
    lines: list[str] = []
    for entry in entries:
        enabled = "Вкл" if entry.enabled else "Выкл"
        lines.append(
            f"{entry.id}\t{enabled}\t{startup_source_label(entry.source)}\t"
            f"{entry.name}\t{entry.command}"
        )
    return "\n".join(lines) + "\n"


def startup_action_text(entry: StartupEntry, action: str) -> str:
    lines: list[str]
    if action == "enable":
        lines = [
            f"Включить автозагрузку: {entry.name}",
            f"Источник: {startup_source_label(entry.source)}",
            f"Команда: {entry.command}",
            "Запись вернётся туда, откуда была убрана.",
        ]
    else:
        lines = [
            f"Выключить автозагрузку: {entry.name}",
            f"Источник: {startup_source_label(entry.source)}",
            f"Команда: {entry.command}",
            "Запись не удаляется. Её можно включить обратно.",
        ]
    return "\n".join(lines)


def backup_preview_text(preview: BackupPreview, *, include_footer: bool) -> str:
    rotate = ", ".join(preview.rotate_names) if preview.rotate_names else "нет"
    lines = [
        f"Архив: {preview.archive_name}",
        f"Куда: {preview.destination}",
        f"Папок: {len(preview.sources)}",
        f"Файлов: {preview.file_count}",
        f"Размер до сжатия: {format_bytes(preview.byte_count)}",
        f"Будут удалены старые архивы: {rotate}",
    ]
    for warning in preview.warnings:
        lines.append(f"Предупреждение: {warning}")
    if include_footer:
        lines.append(confirmation_footer())
    return "\n".join(lines) + "\n"


def backup_result_text(result: BackupResult) -> str:
    if result.dry_run:
        text = backup_preview_text(result.preview, include_footer=True)
        return text + "Режим просмотра: архив не создавался.\n"
    lines = [
        f"Создан архив: {result.archive_path}",
        f"Файлов в архиве: {result.written_files}",
    ]
    return "\n".join(lines) + "\n"


def schedule_preview_text(argv: Sequence[str]) -> str:
    command = " ".join(argv)
    return (
        "Будет выполнена команда:\n"
        f"{command}\n"
        "Задача: \\DeskKit\\Backup\n"
        "Пароль не сохраняется. Копия пойдёт, когда вы вошли в Windows.\n"
    )


def profile_summary_text(profile: Profile) -> str:
    import json

    from deskkit.profile import profile_to_mapping

    data = profile_to_mapping(profile)
    return json.dumps(data, ensure_ascii=False, indent=2) + "\n"


def output_tail(stdout: str, stderr: str, lines: int = 20) -> str:
    combined = (stderr + "\n" + stdout).strip().splitlines()
    non_empty = [line for line in combined if line.strip()]
    tail = non_empty[-lines:]
    return "\n".join(tail)
