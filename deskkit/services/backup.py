from __future__ import annotations

import re
from collections.abc import Sequence
from pathlib import Path

from deskkit import __version__
from deskkit.cancel import CancellationToken
from deskkit.errors import CancelledError, ConfirmationRequired, ValidationError
from deskkit.models import BackupPreview, BackupResult, ZipMember
from deskkit.platform.protocols import Clock, FileOps
from deskkit.safety import destination_conflicts, ensure_absolute, is_denied_source, safe_arcname

ARCHIVE_RE = re.compile(r"^DeskKit-backup-\d{8}-\d{6}\.zip$")


class BackupService:
    def __init__(self, files: FileOps, clock: Clock) -> None:
        self._files = files
        self._clock = clock

    def preview(
        self,
        sources: Sequence[Path],
        destination: Path,
        keep_last: int,
    ) -> BackupPreview:
        sources, destination, keep_last = self._validate(sources, destination, keep_last)
        _members, skipped, byte_count, file_count = self._collect_members(
            sources, CancellationToken()
        )
        self._validate_space_for_dest(destination, byte_count)
        archive_name = self._archive_name()
        rotate = self._rotate_names_for_preview(destination, keep_last)
        return BackupPreview(
            sources=tuple(str(s) for s in sources),
            destination=str(destination),
            file_count=file_count,
            byte_count=byte_count,
            archive_name=archive_name,
            rotate_names=rotate,
            skipped=tuple(skipped),
            warnings=(),
        )

    def apply(
        self,
        sources: Sequence[Path],
        destination: Path,
        keep_last: int,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> BackupResult:
        sources, destination, keep_last = self._validate(sources, destination, keep_last)
        try:
            members, skipped, byte_count, file_count = self._collect_members(sources, cancel)
        except CancelledError:
            preview = BackupPreview(
                sources=tuple(str(s) for s in sources),
                destination=str(destination),
                file_count=0,
                byte_count=0,
                archive_name=self._archive_name(),
                rotate_names=(),
                skipped=(),
                warnings=(),
            )
            return BackupResult(
                preview=preview,
                archive_path=None,
                written_files=0,
                skipped=(),
                dry_run=False,
                cancelled=True,
            )
        self._validate_space_for_dest(destination, byte_count)
        preview = BackupPreview(
            sources=tuple(str(s) for s in sources),
            destination=str(destination),
            file_count=file_count,
            byte_count=byte_count,
            archive_name=self._archive_name(),
            rotate_names=self._rotate_names_for_preview(destination, keep_last),
            skipped=tuple(skipped),
            warnings=(),
        )
        if dry_run:
            return BackupResult(
                preview=preview,
                archive_path=None,
                written_files=0,
                skipped=tuple(skipped),
                dry_run=True,
                cancelled=False,
            )
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")

        cancelled = False
        archive_path: str | None = None
        try:
            destination.mkdir(parents=True, exist_ok=True)
            archive = destination / preview.archive_name
            manifest: dict[str, object] = {
                "app": "DeskKit",
                "version": __version__,
                "created_at": self._clock.now().isoformat(timespec="seconds"),
                "sources": [str(p) for p in sources],
                "files": [],
                "skipped": [
                    {"path": item, "reason": item.split(": ", maxsplit=1)[-1]} for item in skipped
                ],
            }
            file_records: list[dict[str, object]] = []
            zip_members: list[ZipMember] = []
            for member in members:
                cancel.raise_if_cancelled()
                zip_members.append(member)
                index = member.arcname.split("/", maxsplit=1)[0]
                source_index = int(index.split("-", maxsplit=1)[1])
                file_records.append(
                    {"path": member.arcname, "bytes": member.size, "source_index": source_index}
                )
            manifest["files"] = file_records
            self._files.create_zip(archive, zip_members, manifest)
            archive_path = str(archive)
            rotate = self._rotate_names_after_create(destination, keep_last, archive.name)
            for name in rotate:
                try:
                    self._files.remove_file(destination / name)
                except OSError:
                    skipped = list(skipped)
                    skipped.append(f"не удалось удалить старый архив: {name}")
        except CancelledError:
            cancelled = True
            archive_path = None

        return BackupResult(
            preview=preview,
            archive_path=archive_path,
            written_files=file_count if archive_path else 0,
            skipped=tuple(skipped),
            dry_run=False,
            cancelled=cancelled,
        )

    def _validate(
        self,
        sources: Sequence[Path],
        destination: Path,
        keep_last: int,
    ) -> tuple[tuple[Path, ...], Path, int]:
        if not sources:
            raise ValidationError("Не выбраны папки для копии.")
        if len(sources) > 20:
            raise ValidationError("Можно выбрать не больше 20 папок.")
        if keep_last < 1 or keep_last > 30:
            raise ValidationError("Хранить можно от 1 до 30 архивов.")
        normalized: list[Path] = []
        for src in sources:
            path = ensure_absolute(src)
            if is_denied_source(path):
                raise ValidationError(f"Эту папку копировать нельзя: {path}")
            if not path.is_dir():
                raise ValidationError(f"Папка не найдена: {path}")
            normalized.append(path)
        dest = ensure_absolute(destination)
        if destination_conflicts(normalized, dest):
            raise ValidationError("Папка назначения пересекается с копируемой.")
        return tuple(normalized), dest, keep_last

    def _collect_members(
        self,
        sources: Sequence[Path],
        cancel: CancellationToken,
    ) -> tuple[list[ZipMember], list[str], int, int]:
        members: list[ZipMember] = []
        skipped: list[str] = []
        byte_count = 0
        file_count = 0
        for index, root in enumerate(sources, start=1):
            cancel.raise_if_cancelled()
            for entry in self._files.walk_files(root):
                cancel.raise_if_cancelled()
                if entry.is_symlink or entry.is_reparse:
                    skipped.append(f"пропущена ссылка: {entry.path}")
                    continue
                if entry.unreadable:
                    skipped.append(f"нет доступа: {entry.path}")
                    continue
                rel = entry.path.relative_to(root).as_posix()
                arcname = safe_arcname(f"source-{index}/{rel}")
                members.append(ZipMember(source=entry.path, arcname=arcname, size=entry.size))
                byte_count += entry.size
                file_count += 1
        return members, skipped, byte_count, file_count

    def _archive_name(self) -> str:
        return "DeskKit-backup-" + self._clock.now().strftime("%Y%m%d-%H%M%S") + ".zip"

    def _matching_archives(self, destination: Path) -> list[str]:
        if not destination.is_dir():
            return []
        return sorted(
            (p.name for p in destination.iterdir() if p.is_file() and ARCHIVE_RE.match(p.name)),
            reverse=True,
        )

    def _rotate_names_for_preview(self, destination: Path, keep_last: int) -> tuple[str, ...]:
        names = self._matching_archives(destination)
        start = max(keep_last - 1, 0)
        return tuple(names[start:])

    def _rotate_names_after_create(
        self, destination: Path, keep_last: int, new_name: str
    ) -> tuple[str, ...]:
        names = self._matching_archives(destination)
        if new_name not in names:
            names.insert(0, new_name)
            names.sort(reverse=True)
        return tuple(names[keep_last:])

    def _validate_space_for_dest(self, destination: Path, byte_count: int) -> None:
        probe = destination if destination.exists() else destination.parent
        while not probe.exists() and probe != probe.parent:
            probe = probe.parent
        if not probe.exists():
            raise ValidationError("Не удалось проверить свободное место.")
        if self._files.disk_free(probe) < byte_count:
            raise ValidationError("Недостаточно места для копии.")
