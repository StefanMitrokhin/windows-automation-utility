from __future__ import annotations

from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path
from typing import Protocol

from deskkit.models import (
    CommandResult,
    ElevationResult,
    FileEntry,
    Hive,
    RegValue,
    SoftwareEntry,
    SystemSnapshot,
    ZipMember,
)


class CommandRunner(Protocol):
    def run(self, args: Sequence[str], timeout_s: float) -> CommandResult: ...
    def terminate(self) -> None: ...


class RegistryGateway(Protocol):
    def list_values(self, hive: Hive, key: str) -> tuple[RegValue, ...]: ...
    def set_string(self, hive: Hive, key: str, name: str, data: str) -> None: ...
    def delete_value(self, hive: Hive, key: str, name: str) -> None: ...


class RecycleBinGateway(Protocol):
    def query(self) -> tuple[int, int]: ...
    def empty(self) -> None: ...


class SoftwareGateway(Protocol):
    def list_installed(self) -> tuple[SoftwareEntry, ...]: ...


class SystemGateway(Protocol):
    def snapshot_base(self) -> SystemSnapshot: ...


class Clock(Protocol):
    def now(self) -> datetime: ...


class AdminGateway(Protocol):
    def is_admin(self) -> bool: ...
    def relaunch_elevated(self, argv: Sequence[str]) -> ElevationResult: ...


class FileOps(Protocol):
    def walk_files(self, root: Path) -> tuple[FileEntry, ...]: ...
    def delete_file(self, path: Path) -> None: ...
    def remove_dir_if_empty(self, path: Path) -> bool: ...
    def create_zip(
        self,
        archive: Path,
        members: Sequence[ZipMember],
        manifest: Mapping[str, object],
    ) -> None: ...
    def disk_free(self, path: Path) -> int: ...
    def replace(self, src: Path, dst: Path) -> None: ...
    def remove_file(self, path: Path) -> None: ...
