from __future__ import annotations

from pathlib import Path

from deskkit.paths import (
    cleanup_roots_from_env,
    log_path_from_env,
    profile_path_from_env,
    startup_folders_from_env,
)


def test_profile_path_windows_env() -> None:
    env = {"APPDATA": r"C:\Users\A\AppData\Roaming"}
    path = profile_path_from_env(env, Path("/home"))
    assert path.name == "profile.json" and "DeskKit" in path.parts


def test_profile_path_fallback_without_appdata() -> None:
    assert profile_path_from_env({}, Path("/home")) == Path("/home/.deskkit/profile.json")


def test_log_path_uses_localappdata() -> None:
    env = {"LOCALAPPDATA": r"C:\Users\A\AppData\Local"}
    path = log_path_from_env(env, Path("/home"))
    assert path.parts[-3:] == ("DeskKit", "logs", "deskkit.log")


def test_cleanup_roots_from_env() -> None:
    env = {
        "TEMP": r"C:\Temp",
        "SYSTEMROOT": r"C:\Windows",
        "LOCALAPPDATA": r"C:\Users\A\AppData\Local",
    }
    roots = cleanup_roots_from_env(env, Path("/home"))
    assert str(roots.user_temp).replace("\\", "/").endswith("C:/Temp")
    assert "Windows" in str(roots.windows_temp) and str(roots.windows_temp).endswith("Temp")
    assert roots.chrome_user_data.parts[-3:] == ("Google", "Chrome", "User Data")


def test_startup_folders() -> None:
    env = {
        "APPDATA": r"C:\Users\A\AppData\Roaming",
        "PROGRAMDATA": r"C:\ProgramData",
    }
    user, common = startup_folders_from_env(env, Path("/home"))
    assert "Start Menu" in str(user) and str(user).endswith("Startup")
    assert "Start Menu" in str(common) and str(common).endswith("Startup")
