from __future__ import annotations

from collections.abc import Mapping
from pathlib import Path

from deskkit.models import CleanupRoots


def profile_path_from_env(env: Mapping[str, str], home: Path) -> Path:
    appdata = env.get("APPDATA", "").strip()
    if appdata:
        return Path(appdata) / "DeskKit" / "profile.json"
    return home / ".deskkit" / "profile.json"


def log_path_from_env(env: Mapping[str, str], home: Path) -> Path:
    local = env.get("LOCALAPPDATA", "").strip()
    if local:
        return Path(local) / "DeskKit" / "logs" / "deskkit.log"
    return home / ".deskkit" / "logs" / "deskkit.log"


def cleanup_roots_from_env(env: Mapping[str, str], home: Path) -> CleanupRoots:
    temp = env.get("TEMP", "").strip() or env.get("TMP", "").strip()
    user_temp = Path(temp) if temp else home / "AppData" / "Local" / "Temp"
    systemroot = env.get("SYSTEMROOT", "C:\\Windows").strip() or "C:\\Windows"
    windows_temp = Path(systemroot) / "Temp"
    local_root = env.get("LOCALAPPDATA", "").strip()
    local_base = Path(local_root) if local_root else home / "AppData" / "Local"
    return CleanupRoots(
        user_temp=user_temp,
        windows_temp=windows_temp,
        chrome_user_data=local_base / "Google" / "Chrome" / "User Data",
        edge_user_data=local_base / "Microsoft" / "Edge" / "User Data",
        firefox_profiles=local_base / "Mozilla" / "Firefox" / "Profiles",
    )


def startup_folders_from_env(env: Mapping[str, str], home: Path) -> tuple[Path, Path]:
    appdata = env.get("APPDATA", "").strip()
    user_startup = (
        Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
        if appdata
        else home
        / "AppData"
        / "Roaming"
        / "Microsoft"
        / "Windows"
        / "Start Menu"
        / "Programs"
        / "Startup"
    )
    programdata = env.get("PROGRAMDATA", "C:\\ProgramData").strip() or "C:\\ProgramData"
    common_startup = (
        Path(programdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    )
    return user_startup, common_startup
