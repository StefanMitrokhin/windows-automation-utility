from __future__ import annotations

from collections.abc import Sequence
from datetime import timedelta
from pathlib import Path

from deskkit.cancel import CancellationToken
from deskkit.errors import CancelledError, ConfirmationRequired, DeskKitError, ValidationError
from deskkit.models import (
    CleanupPreview,
    CleanupResult,
    CleanupRoots,
    CleanupTargetId,
    CleanupTargetPreview,
    FileEntry,
)
from deskkit.platform.protocols import Clock, FileOps, RecycleBinGateway

TEMP_MIN_AGE = timedelta(hours=24)
BROWSER_CACHE_DIRS: tuple[str, ...] = ("Cache", "Code Cache", "GPUCache")
SKIP_CHROME_EDGE_DIRS: frozenset[str] = frozenset(
    {"System Profile", "ShaderCache", "GrShaderCache", "Crashpad", "BrowserMetrics"}
)


class CleanupService:
    def __init__(
        self,
        roots: CleanupRoots,
        files: FileOps,
        recycle: RecycleBinGateway,
        clock: Clock,
    ) -> None:
        self._roots = roots
        self._files = files
        self._recycle = recycle
        self._clock = clock

    def preview(self, targets: Sequence[CleanupTargetId]) -> CleanupPreview:
        if not targets:
            raise ValidationError("Не выбрана ни одна цель очистки.")
        previews = tuple(self._preview_target(t) for t in targets)
        return CleanupPreview(targets=previews)

    def apply(
        self,
        targets: Sequence[CleanupTargetId],
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> CleanupResult:
        preview = self.preview(targets)
        if dry_run:
            return CleanupResult(
                preview=preview,
                deleted_files=0,
                freed_bytes=0,
                skipped_locked=0,
                errors=(),
                dry_run=True,
                cancelled=False,
            )
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")

        deleted = 0
        freed = 0
        skipped_locked = 0
        errors: list[str] = []
        cancelled = False
        try:
            for target in targets:
                if target == CleanupTargetId.RECYCLE_BIN:
                    continue
                roots = self._roots_for(target)
                for root in roots:
                    deletable = self._deletable_files(root, target)
                    for entry in deletable:
                        cancel.raise_if_cancelled()
                        try:
                            if not self._path_in_root(entry.path, root):
                                continue
                            self._files.delete_file(entry.path)
                            deleted += 1
                            freed += entry.size
                        except (PermissionError, OSError) as exc:
                            skipped_locked += 1
                            errors.append(str(exc))
                    self._prune_empty_dirs(root, roots, cancel)
            if CleanupTargetId.RECYCLE_BIN in targets:
                try:
                    before = self._recycle.query()
                    self._recycle.empty()
                    freed += before[0]
                except DeskKitError as exc:
                    errors.append(str(exc))
        except CancelledError:
            cancelled = True

        return CleanupResult(
            preview=preview,
            deleted_files=deleted,
            freed_bytes=freed,
            skipped_locked=skipped_locked,
            errors=tuple(errors),
            dry_run=False,
            cancelled=cancelled,
        )

    def _preview_target(self, target: CleanupTargetId) -> CleanupTargetPreview:
        if target == CleanupTargetId.RECYCLE_BIN:
            warnings: list[str] = []
            try:
                size, count = self._recycle.query()
                return CleanupTargetPreview(
                    target=target,
                    roots=(),
                    file_count=count,
                    byte_count=size,
                    skipped_recent=0,
                    skipped_links=0,
                    unreadable=0,
                    warnings=(),
                    absent=False,
                )
            except DeskKitError as exc:
                warnings.append(str(exc))
                return CleanupTargetPreview(
                    target=target,
                    roots=(),
                    file_count=0,
                    byte_count=0,
                    skipped_recent=0,
                    skipped_links=0,
                    unreadable=0,
                    warnings=tuple(warnings),
                    absent=False,
                )

        roots = self._roots_for(target)
        if not roots:
            return CleanupTargetPreview(
                target=target,
                roots=(),
                file_count=0,
                byte_count=0,
                skipped_recent=0,
                skipped_links=0,
                unreadable=0,
                warnings=(),
                absent=True,
            )
        file_count = 0
        byte_count = 0
        skipped_recent = 0
        skipped_links = 0
        unreadable = 0
        warnings: list[str] = []
        root_labels = tuple(str(r) for r in roots)
        for root in roots:
            for entry in self._files.walk_files(root):
                if entry.is_symlink or entry.is_reparse:
                    skipped_links += 1
                    warnings.append(f"пропущена ссылка: {entry.path}")
                    continue
                if entry.unreadable:
                    unreadable += 1
                    warnings.append(f"нет доступа: {entry.path}")
                    continue
                if self._is_recent_temp(target, entry):
                    skipped_recent += 1
                    continue
                file_count += 1
                byte_count += entry.size
        return CleanupTargetPreview(
            target=target,
            roots=root_labels,
            file_count=file_count,
            byte_count=byte_count,
            skipped_recent=skipped_recent,
            skipped_links=skipped_links,
            unreadable=unreadable,
            warnings=tuple(warnings),
            absent=False,
        )

    def _roots_for(self, target: CleanupTargetId) -> tuple[Path, ...]:
        if target == CleanupTargetId.USER_TEMP:
            root = self._roots.user_temp
            return () if not root.exists() else (root,)
        if target == CleanupTargetId.WINDOWS_TEMP:
            root = self._roots.windows_temp
            return () if not root.exists() else (root,)
        if target == CleanupTargetId.CHROME_CACHE:
            return self._browser_roots(self._roots.chrome_user_data)
        if target == CleanupTargetId.EDGE_CACHE:
            return self._browser_roots(self._roots.edge_user_data)
        if target == CleanupTargetId.FIREFOX_CACHE:
            profiles = self._roots.firefox_profiles
            if not profiles.is_dir():
                return ()
            cache_roots: list[Path] = []
            for profile_dir in profiles.iterdir():
                if profile_dir.is_dir():
                    cache2 = profile_dir / "cache2"
                    if cache2.is_dir():
                        cache_roots.append(cache2)
            return tuple(cache_roots)
        return ()

    def _browser_roots(self, user_data: Path) -> tuple[Path, ...]:
        if not user_data.is_dir():
            return ()
        roots: list[Path] = []
        for child in user_data.iterdir():
            if not child.is_dir() or child.name in SKIP_CHROME_EDGE_DIRS:
                continue
            if any((child / name).is_dir() for name in BROWSER_CACHE_DIRS):
                for name in BROWSER_CACHE_DIRS:
                    cache_dir = child / name
                    if cache_dir.is_dir():
                        roots.append(cache_dir)
        return tuple(roots)

    def _is_recent_temp(self, target: CleanupTargetId, entry: FileEntry) -> bool:
        if target not in (CleanupTargetId.USER_TEMP, CleanupTargetId.WINDOWS_TEMP):
            return False
        return entry.modified_at > self._clock.now() - TEMP_MIN_AGE

    def _deletable_files(self, root: Path, target: CleanupTargetId) -> list[FileEntry]:
        result: list[FileEntry] = []
        for entry in self._files.walk_files(root):
            if entry.is_symlink or entry.is_reparse or entry.unreadable:
                continue
            if self._is_recent_temp(target, entry):
                continue
            result.append(entry)
        return result

    def _path_in_root(self, path: Path, root: Path) -> bool:
        try:
            return path.resolve().is_relative_to(root.resolve())
        except OSError:
            return False

    def _prune_empty_dirs(
        self, root: Path, all_roots: tuple[Path, ...], cancel: CancellationToken
    ) -> None:
        dirs: set[Path] = set()
        for entry in self._files.walk_files(root):
            dirs.add(entry.path.parent)
        for directory in sorted(dirs, key=lambda p: len(p.parts), reverse=True):
            cancel.raise_if_cancelled()
            if directory == root or directory in all_roots:
                continue
            self._files.remove_dir_if_empty(directory)
