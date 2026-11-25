from __future__ import annotations

import json
import os
import shutil
import zipfile
from collections.abc import Mapping, Sequence
from datetime import datetime
from pathlib import Path

from deskkit.models import FileEntry, ZipMember
from deskkit.safety import is_reparse_point, safe_arcname


class LocalFileOps:
    def walk_files(self, root: Path) -> tuple[FileEntry, ...]:
        if not root.exists():
            return ()
        tz = datetime.now().astimezone().tzinfo
        entries: list[FileEntry] = []
        for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
            current = Path(dirpath)
            dirnames[:] = [
                name
                for name in dirnames
                if not (is_reparse_point(current / name) or (current / name).is_symlink())
            ]
            for filename in filenames:
                path = current / filename
                if path.is_symlink() or is_reparse_point(path):
                    entries.append(
                        FileEntry(
                            path=path,
                            size=0,
                            modified_at=datetime.now(tz=tz),
                            is_symlink=True,
                            is_reparse=True,
                            unreadable=False,
                            error=None,
                        )
                    )
                    continue
                try:
                    stat = path.stat()
                    mtime = datetime.fromtimestamp(stat.st_mtime, tz=tz)
                    entries.append(
                        FileEntry(
                            path=path,
                            size=stat.st_size,
                            modified_at=mtime,
                            is_symlink=False,
                            is_reparse=False,
                            unreadable=False,
                            error=None,
                        )
                    )
                except (OSError, PermissionError) as exc:
                    entries.append(
                        FileEntry(
                            path=path,
                            size=0,
                            modified_at=datetime.now(tz=tz),
                            is_symlink=False,
                            is_reparse=False,
                            unreadable=True,
                            error=str(exc),
                        )
                    )
        return tuple(entries)

    def delete_file(self, path: Path) -> None:
        path.unlink()

    def remove_dir_if_empty(self, path: Path) -> bool:
        try:
            path.rmdir()
        except OSError:
            return False
        return True

    def disk_free(self, path: Path) -> int:
        return shutil.disk_usage(path).free

    def create_zip(
        self,
        archive: Path,
        members: Sequence[ZipMember],
        manifest: Mapping[str, object],
    ) -> None:
        partial = archive.with_suffix(archive.suffix + ".partial")
        try:
            with zipfile.ZipFile(
                partial, mode="w", compression=zipfile.ZIP_DEFLATED, compresslevel=6
            ) as zf:
                for member in members:
                    safe_arcname(member.arcname)
                    zf.write(member.source, member.arcname)
                payload = json.dumps(manifest, ensure_ascii=False, indent=2)
                zf.writestr("deskkit-manifest.json", payload)
            os.replace(partial, archive)
        except Exception:
            partial.unlink(missing_ok=True)
            raise

    def replace(self, src: Path, dst: Path) -> None:
        os.replace(src, dst)

    def remove_file(self, path: Path) -> None:
        path.unlink(missing_ok=True)
