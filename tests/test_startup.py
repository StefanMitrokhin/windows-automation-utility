from __future__ import annotations

from pathlib import Path

import pytest

from deskkit.errors import AdminRequiredError, ConfirmationRequired, ValidationError
from deskkit.models import Hive, RegKind, RegValue, StartupSource
from deskkit.services.startup import StartupService
from tests.fakes import FakeAdmin, FakeRegistry


def _service(tmp_path: Path) -> tuple[StartupService, FakeRegistry, FakeAdmin]:
    registry = FakeRegistry()
    admin = FakeAdmin()
    user = tmp_path / "user"
    common = tmp_path / "common"
    user.mkdir()
    common.mkdir()
    return StartupService(registry, admin, user, common), registry, admin


def test_list_combines_sources(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "A": RegValue("A", "a.exe", RegKind.SZ)
    }
    registry.data[(Hive.HKLM, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "B": RegValue("B", "b.exe", RegKind.SZ)
    }
    (tmp_path / "user" / "U.lnk").write_bytes(b"")
    (tmp_path / "common" / "C.lnk").write_bytes(b"")
    entries = svc.list_entries()
    assert len(entries) == 4
    assert entries[0].source == StartupSource.HKCU_RUN


def test_id_format(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "OneDrive": RegValue("OneDrive", "x", RegKind.SZ)
    }
    assert svc.list_entries()[0].id == "hkcu_run|OneDrive"


def test_skip_non_string(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "A": RegValue("A", "", RegKind.OTHER)
    }
    assert not svc.list_entries()


def test_skip_pipe_in_name(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "a|b": RegValue("a|b", "x", RegKind.SZ)
    }
    assert not svc.list_entries()


def test_disable_hkcu_order(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "OneDrive": RegValue("OneDrive", "x", RegKind.SZ)
    }
    svc.disable("hkcu_run|OneDrive", dry_run=False, confirmed=True)
    assert registry.events[0].startswith("set")
    assert registry.events[1].startswith("delete")


def test_disable_rolls_back(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "OneDrive": RegValue("OneDrive", "x", RegKind.SZ)
    }
    registry.fail_delete.add(
        (Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run", "OneDrive")
    )
    with pytest.raises(Exception):
        svc.disable("hkcu_run|OneDrive", dry_run=False, confirmed=True)
    assert "OneDrive" not in registry.data.get(
        (Hive.HKCU, "Software\\StefanMitrokhin\\DeskKit\\DisabledStartup\\HKCU"),
        {},
    )


def test_enable_restores(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    disabled = "Software\\StefanMitrokhin\\DeskKit\\DisabledStartup\\HKCU"
    registry.data[(Hive.HKCU, disabled)] = {"OneDrive": RegValue("OneDrive", "x", RegKind.SZ)}
    svc.enable("hkcu_run|OneDrive", dry_run=False, confirmed=True)
    assert (
        "OneDrive"
        in registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")]
    )
    assert "OneDrive" not in registry.data.get((Hive.HKCU, disabled), {})


def test_hklm_requires_admin(tmp_path: Path) -> None:
    svc, registry, admin = _service(tmp_path)
    registry.data[(Hive.HKLM, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "B": RegValue("B", "x", RegKind.SZ)
    }
    admin.admin = False
    with pytest.raises(AdminRequiredError):
        svc.disable("hklm_run|B", dry_run=True, confirmed=False)
    assert not registry.events


def test_disable_shortcut(tmp_path: Path) -> None:
    svc, _, _ = _service(tmp_path)
    path = tmp_path / "user" / "Slack.lnk"
    path.write_bytes(b"")
    svc.disable("user_startup|Slack.lnk", dry_run=False, confirmed=True)
    assert (tmp_path / "user" / "Slack.lnk.deskkit-disabled").is_file()


def test_enable_shortcut(tmp_path: Path) -> None:
    svc, _, _ = _service(tmp_path)
    disabled = tmp_path / "user" / "Slack.lnk.deskkit-disabled"
    disabled.write_bytes(b"")
    svc.enable("user_startup|Slack.lnk.deskkit-disabled", dry_run=False, confirmed=True)
    assert (tmp_path / "user" / "Slack.lnk").is_file()


def test_dry_run_registry(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "A": RegValue("A", "x", RegKind.SZ)
    }
    entry = svc.disable("hkcu_run|A", dry_run=True, confirmed=False)
    assert entry.enabled is False
    assert not registry.events


def test_confirmation_required(tmp_path: Path) -> None:
    svc, registry, _ = _service(tmp_path)
    registry.data[(Hive.HKCU, "Software\\Microsoft\\Windows\\CurrentVersion\\Run")] = {
        "A": RegValue("A", "x", RegKind.SZ)
    }
    with pytest.raises(ConfirmationRequired):
        svc.disable("hkcu_run|A", dry_run=False, confirmed=False)
    assert not registry.events


def test_missing_entry(tmp_path: Path) -> None:
    svc, _, _ = _service(tmp_path)
    with pytest.raises(ValidationError) as exc:
        svc.disable("hkcu_run|missing", dry_run=False, confirmed=True)
    assert str(exc.value) == "Запись автозагрузки не найдена."
