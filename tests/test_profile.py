from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from deskkit.errors import ProfileVersionError, ValidationError
from deskkit.models import CleanupTargetId, InstallScope, InstallSettings
from deskkit.profile import ProfileStore, default_profile, profile_from_mapping, profile_to_mapping


def test_default_values() -> None:
    profile = default_profile()
    assert CleanupTargetId.WINDOWS_TEMP not in profile.cleanup.targets
    assert profile.backup.keep_last == 5
    assert profile.backup.schedule.enabled is False
    assert profile.backup.schedule.weekday == "MON"
    assert profile.backup.schedule.time == "09:00"


def test_roundtrip(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profile.json")
    profile = replace(
        default_profile(),
        install=InstallSettings(package_ids=("7zip.7zip",), scope=InstallScope.USER),
    )
    store.save(profile)
    assert store.load() == profile


def test_missing_file_does_not_create(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profile.json")
    assert store.load() == default_profile()
    assert not store.path.exists()


def test_unknown_keys_ignored() -> None:
    data = profile_to_mapping(default_profile())
    data["telemetry"] = True
    profile_from_mapping(data)


def test_bad_schema_version() -> None:
    data = profile_to_mapping(default_profile())
    data["schema_version"] = 2
    with pytest.raises(ProfileVersionError):
        profile_from_mapping(data)


def test_unknown_package() -> None:
    data = profile_to_mapping(default_profile())
    data["install"]["package_ids"] = ["nope"]
    with pytest.raises(ValidationError):
        profile_from_mapping(data)


def test_unknown_target() -> None:
    data = profile_to_mapping(default_profile())
    data["cleanup"]["targets"] = ["nope"]
    with pytest.raises(ValidationError) as exc:
        profile_from_mapping(data)
    assert str(exc.value) == "Неизвестная цель очистки."


def test_bad_time() -> None:
    data = profile_to_mapping(default_profile())
    data["backup"]["schedule"]["time"] = "24:00"
    with pytest.raises(ValidationError):
        profile_from_mapping(data)
    data["backup"]["schedule"]["time"] = "9:00"
    with pytest.raises(ValidationError):
        profile_from_mapping(data)
    data["backup"]["schedule"]["time"] = "09:00"
    profile_from_mapping(data)


def test_bad_weekday() -> None:
    data = profile_to_mapping(default_profile())
    data["backup"]["schedule"]["weekday"] = "Monday"
    with pytest.raises(ValidationError):
        profile_from_mapping(data)
    data["backup"]["schedule"]["weekday"] = "MON"
    profile_from_mapping(data)


def test_keep_last_bounds() -> None:
    data = profile_to_mapping(default_profile())
    data["backup"]["keep_last"] = 0
    with pytest.raises(ValidationError):
        profile_from_mapping(data)
    data["backup"]["keep_last"] = 31
    with pytest.raises(ValidationError):
        profile_from_mapping(data)
    data["backup"]["keep_last"] = 1
    profile_from_mapping(data)
    data["backup"]["keep_last"] = 30
    profile_from_mapping(data)


def test_invalid_json(tmp_path: Path) -> None:
    path = tmp_path / "profile.json"
    path.write_text("{", encoding="utf-8")
    store = ProfileStore(path)
    with pytest.raises(ValidationError) as exc:
        store.load()
    assert str(exc.value) == "Файл профиля повреждён."


def test_sources_need_not_exist_at_load() -> None:
    data = profile_to_mapping(default_profile())
    data["backup"]["sources"] = [r"C:\Missing"]
    profile_from_mapping(data)


def test_bad_scope() -> None:
    data = profile_to_mapping(default_profile())
    data["install"]["scope"] = "broken"
    with pytest.raises(ValidationError) as exc:
        profile_from_mapping(data)
    assert str(exc.value) == "Неизвестная область установки."


def test_atomic_save_replaces(tmp_path: Path) -> None:
    store = ProfileStore(tmp_path / "profile.json")
    store.save(default_profile())
    assert not (tmp_path / "profile.json.tmp").exists()
    json.loads(store.path.read_text(encoding="utf-8"))
