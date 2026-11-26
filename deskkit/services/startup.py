from __future__ import annotations

import logging
from pathlib import Path

from deskkit.errors import AdminRequiredError, ConfirmationRequired, DeskKitError, ValidationError
from deskkit.models import Hive, RegKind, StartupEntry, StartupSource
from deskkit.platform.protocols import AdminGateway, RegistryGateway

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_DISABLED_HKCU = r"Software\StefanMitrokhin\DeskKit\DisabledStartup\HKCU"
_DISABLED_HKLM = r"Software\StefanMitrokhin\DeskKit\DisabledStartup\HKLM"

_LOG = logging.getLogger("deskkit.startup")
_SUFFIX = ".lnk.deskkit-disabled"


class StartupService:
    def __init__(
        self,
        registry: RegistryGateway,
        admin: AdminGateway,
        user_startup: Path,
        common_startup: Path,
    ) -> None:
        self._registry = registry
        self._admin = admin
        self._user_startup = user_startup
        self._common_startup = common_startup

    def list_entries(self) -> tuple[StartupEntry, ...]:
        entries: list[StartupEntry] = []
        entries.extend(
            self._list_registry(Hive.HKCU, StartupSource.HKCU_RUN, _RUN_KEY, _DISABLED_HKCU)
        )
        entries.extend(
            self._list_registry(
                Hive.HKLM, StartupSource.HKLM_RUN, _RUN_KEY, _DISABLED_HKLM, admin=True
            )
        )
        entries.extend(self._list_folder(self._user_startup, StartupSource.USER_STARTUP))
        entries.extend(
            self._list_folder(self._common_startup, StartupSource.COMMON_STARTUP, admin=True)
        )
        return tuple(entries)

    def disable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry:
        entry = self._find(entry_id)
        if not entry.enabled:
            raise ValidationError("Запись уже выключена.")
        if entry.needs_admin and not self._admin.is_admin():
            raise AdminRequiredError("Нужны права администратора.")
        if dry_run:
            return StartupEntry(
                id=entry.id,
                source=entry.source,
                name=entry.name,
                command=entry.command,
                enabled=False,
                needs_admin=entry.needs_admin,
            )
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")
        if entry.source in (StartupSource.HKCU_RUN, StartupSource.HKLM_RUN):
            hive = Hive.HKCU if entry.source == StartupSource.HKCU_RUN else Hive.HKLM
            backup_key = _DISABLED_HKCU if hive == Hive.HKCU else _DISABLED_HKLM
            self._registry.set_string(hive, backup_key, entry.name, entry.command)
            try:
                self._registry.delete_value(hive, _RUN_KEY, entry.name)
            except OSError:
                self._registry.delete_value(hive, backup_key, entry.name)
                raise DeskKitError("Не удалось выключить запись.") from None
        else:
            src = self._folder_for(entry.source) / entry.name
            dst = src.with_name(entry.name + ".deskkit-disabled")
            if dst.exists():
                raise DeskKitError("Не удалось выключить запись.")
            src.rename(dst)
        return StartupEntry(
            id=entry.id,
            source=entry.source,
            name=entry.name,
            command=entry.command,
            enabled=False,
            needs_admin=entry.needs_admin,
        )

    def enable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry:
        entry = self._find(entry_id)
        if entry.enabled:
            raise ValidationError("Запись уже включена.")
        if entry.needs_admin and not self._admin.is_admin():
            raise AdminRequiredError("Нужны права администратора.")
        if dry_run:
            return StartupEntry(
                id=entry.id,
                source=entry.source,
                name=entry.name,
                command=entry.command,
                enabled=True,
                needs_admin=entry.needs_admin,
            )
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")
        if entry.source in (StartupSource.HKCU_RUN, StartupSource.HKLM_RUN):
            hive = Hive.HKCU if entry.source == StartupSource.HKCU_RUN else Hive.HKLM
            backup_key = _DISABLED_HKCU if hive == Hive.HKCU else _DISABLED_HKLM
            self._registry.set_string(hive, _RUN_KEY, entry.name, entry.command)
            self._registry.delete_value(hive, backup_key, entry.name)
        else:
            folder = self._folder_for(entry.source)
            disabled_path = folder / entry.name
            if not disabled_path.is_file():
                raise DeskKitError("Не удалось включить запись.")
            if not entry.name.endswith(".deskkit-disabled"):
                raise DeskKitError("Не удалось включить запись.")
            enabled_name = entry.name[: -len(".deskkit-disabled")]
            disabled_path.rename(folder / enabled_name)
            entry = StartupEntry(
                id=entry.id,
                source=entry.source,
                name=enabled_name,
                command=entry.command,
                enabled=True,
                needs_admin=entry.needs_admin,
            )
            return entry
        return StartupEntry(
            id=entry.id,
            source=entry.source,
            name=entry.name,
            command=entry.command,
            enabled=True,
            needs_admin=entry.needs_admin,
        )

    def _find(self, entry_id: str) -> StartupEntry:
        for entry in self.list_entries():
            if entry.id == entry_id:
                return entry
        raise ValidationError("Запись автозагрузки не найдена.")

    def _list_registry(
        self,
        hive: Hive,
        source: StartupSource,
        run_key: str,
        disabled_key: str,
        *,
        admin: bool = False,
    ) -> list[StartupEntry]:
        run_values = {v.name: v for v in self._registry.list_values(hive, run_key)}
        disabled_values = {v.name: v for v in self._registry.list_values(hive, disabled_key)}
        names = set(run_values) | set(disabled_values)
        entries: list[StartupEntry] = []
        for name in sorted(names):
            if "|" in name:
                _LOG.debug("пропуск имени")
                continue
            if name in run_values and run_values[name].kind == RegKind.OTHER:
                _LOG.debug("пропуск типа %s", name)
                continue
            enabled = name in run_values and run_values[name].kind != RegKind.OTHER
            if enabled:
                command = run_values[name].data
            else:
                command = disabled_values[name].data if name in disabled_values else ""
            entries.append(
                StartupEntry(
                    id=f"{source.value}|{name}",
                    source=source,
                    name=name,
                    command=command,
                    enabled=enabled,
                    needs_admin=admin,
                )
            )
        return entries

    def _list_folder(
        self,
        folder: Path,
        source: StartupSource,
        *,
        admin: bool = False,
    ) -> list[StartupEntry]:
        if not folder.is_dir():
            return []
        entries: list[StartupEntry] = []
        for item in folder.iterdir():
            if not item.is_file():
                continue
            name = item.name
            if "|" in name:
                continue
            lower = name.lower()
            if lower.endswith(".lnk"):
                enabled = True
            elif lower.endswith(_SUFFIX.lower()):
                enabled = False
            else:
                continue
            entries.append(
                StartupEntry(
                    id=f"{source.value}|{name}",
                    source=source,
                    name=name,
                    command=str(item.resolve()),
                    enabled=enabled,
                    needs_admin=admin,
                )
            )
        return entries

    def _folder_for(self, source: StartupSource) -> Path:
        if source == StartupSource.USER_STARTUP:
            return self._user_startup
        return self._common_startup
