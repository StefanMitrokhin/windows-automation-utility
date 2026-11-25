from __future__ import annotations

import sys

if sys.platform != "win32":
    raise ImportError("deskkit.platform.windows is Windows-only")

import ctypes
import os
import shutil
import subprocess
import winreg
from collections.abc import Sequence
from pathlib import Path

from deskkit.errors import DeskKitError
from deskkit.models import ElevationResult, Hive, RegKind, RegValue, SoftwareEntry
from deskkit.platform.protocols import CommandRunner

_RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"
_UNINSTALL_HKLM = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"
_UNINSTALL_HKLM32 = r"SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall"
_UNINSTALL_HKCU = r"SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall"

SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004

_HIVE_CONST = {
    Hive.HKCU: winreg.HKEY_CURRENT_USER,
    Hive.HKLM: winreg.HKEY_LOCAL_MACHINE,
}
_ACCESS = winreg.KEY_READ | 0x0100
_WRITE = winreg.KEY_SET_VALUE | 0x0100


class WindowsPlatform:
    def __init__(self, runner: CommandRunner) -> None:
        self._runner = runner

    def is_admin(self) -> bool:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())

    def relaunch_elevated(self, argv: Sequence[str]) -> ElevationResult:
        params = subprocess.list2cmdline(list(argv))
        code = ctypes.windll.shell32.ShellExecuteW(None, "runas", sys.executable, params, None, 1)
        if code > 32:
            return ElevationResult(True, "")
        return ElevationResult(False, "Повышение прав отменено.")

    def resolve_winget(self) -> str | None:
        found = shutil.which("winget")
        if found:
            return found
        local = os.environ.get("LOCALAPPDATA", "")
        if local:
            candidate = Path(local) / "Microsoft" / "WindowsApps" / "winget.exe"
            if candidate.is_file():
                return str(candidate)
        return None

    def query(self) -> tuple[int, int]:
        return self.query_recycle_bin()

    def empty(self) -> None:
        self.empty_recycle_bin()

    def query_recycle_bin(self) -> tuple[int, int]:
        class SHQUERYRBINFO(ctypes.Structure):
            _fields_ = [
                ("cbSize", ctypes.c_ulong),
                ("i64Size", ctypes.c_longlong),
                ("i64NumItems", ctypes.c_longlong),
            ]

        info = SHQUERYRBINFO()
        info.cbSize = ctypes.sizeof(SHQUERYRBINFO)
        code = ctypes.windll.shell32.SHQueryRecycleBinW(None, ctypes.byref(info))
        if code != 0:
            raise DeskKitError("Не удалось прочитать корзину.")
        return int(info.i64Size), int(info.i64NumItems)

    def empty_recycle_bin(self) -> None:
        flags = SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND
        code = ctypes.windll.shell32.SHEmptyRecycleBinW(None, None, flags)
        if code not in (0, 0x8000FFFF):
            raise DeskKitError("Не удалось очистить корзину.")

    def list_installed(self) -> tuple[SoftwareEntry, ...]:
        entries: list[SoftwareEntry] = []
        seen: set[tuple[str, str]] = set()
        for hive, subkey in (
            (winreg.HKEY_LOCAL_MACHINE, _UNINSTALL_HKLM),
            (winreg.HKEY_LOCAL_MACHINE, _UNINSTALL_HKLM32),
            (winreg.HKEY_CURRENT_USER, _UNINSTALL_HKCU),
        ):
            try:
                with winreg.OpenKey(hive, subkey, 0, _ACCESS) as key:
                    count = winreg.QueryInfoKey(key)[0]
                    for index in range(count):
                        sub = winreg.EnumKey(key, index)
                        with winreg.OpenKey(key, sub, 0, _ACCESS) as app_key:
                            name = _read_optional(app_key, "DisplayName")
                            if not name:
                                continue
                            if _read_optional(app_key, "SystemComponent") == "1":
                                continue
                            version = _read_optional(app_key, "DisplayVersion")
                            publisher = _read_optional(app_key, "Publisher")
                            install_date = _read_optional(app_key, "InstallDate")
                            key_pair = (name.casefold(), version)
                            if key_pair in seen:
                                continue
                            seen.add(key_pair)
                            entries.append(
                                SoftwareEntry(
                                    name=name,
                                    version=version,
                                    publisher=publisher,
                                    install_date=install_date,
                                )
                            )
            except OSError:
                continue
        entries.sort(key=lambda e: e.name.casefold())
        return tuple(entries)

    def list_values(self, hive: Hive, key: str) -> tuple[RegValue, ...]:
        try:
            with winreg.OpenKey(_HIVE_CONST[hive], key, 0, _ACCESS) as handle:
                count = winreg.QueryInfoKey(handle)[1]
                values: list[RegValue] = []
                for index in range(count):
                    name, data, kind = winreg.EnumValue(handle, index)
                    if kind == winreg.REG_SZ:
                        reg_kind = RegKind.SZ
                        text = str(data)
                    elif kind == winreg.REG_EXPAND_SZ:
                        reg_kind = RegKind.EXPAND_SZ
                        text = str(data)
                    else:
                        reg_kind = RegKind.OTHER
                        text = ""
                    values.append(RegValue(name=name, data=text, kind=reg_kind))
                return tuple(values)
        except FileNotFoundError:
            return ()

    def set_string(self, hive: Hive, key: str, name: str, data: str) -> None:
        with winreg.CreateKeyEx(_HIVE_CONST[hive], key, 0, _WRITE) as handle:
            winreg.SetValueEx(handle, name, 0, winreg.REG_SZ, data)

    def delete_value(self, hive: Hive, key: str, name: str) -> None:
        with winreg.OpenKey(_HIVE_CONST[hive], key, 0, _WRITE) as handle:
            winreg.DeleteValue(handle, name)

    def open_folder(self, path: Path) -> None:
        os.startfile(str(path))


def _read_optional(key: winreg.HkeyType, name: str) -> str:
    try:
        value, _ = winreg.QueryValueEx(key, name)
        return str(value) if value is not None else ""
    except OSError:
        return ""
