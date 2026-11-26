from __future__ import annotations

import platform
from datetime import datetime

import psutil

from deskkit.models import DiskInfo, SystemSnapshot


class PsutilSystemProbe:
    def snapshot_base(self) -> SystemSnapshot:
        if platform.system() == "Windows":
            release, version, build, _ = platform.win32_ver()
            os_name = f"Windows {release}" if release else platform.system()
            os_version = version
            os_build = build
        else:
            os_name = platform.system()
            os_version = platform.release()
            os_build = platform.version()
        cpu_model = platform.processor() or "CPU"
        try:
            freq = psutil.cpu_freq()
            cpu_freq_mhz = freq.current if freq else None
        except RuntimeError:
            cpu_freq_mhz = None
        mem = psutil.virtual_memory()
        disks: list[DiskInfo] = []
        for part in psutil.disk_partitions(all=False):
            try:
                usage = psutil.disk_usage(part.mountpoint)
                disks.append(
                    DiskInfo(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype,
                        total_bytes=usage.total,
                        used_bytes=usage.used,
                        free_bytes=usage.free,
                        available=True,
                    )
                )
            except (PermissionError, OSError):
                disks.append(
                    DiskInfo(
                        device=part.device,
                        mountpoint=part.mountpoint,
                        fstype=part.fstype,
                        total_bytes=0,
                        used_bytes=0,
                        free_bytes=0,
                        available=False,
                    )
                )
        return SystemSnapshot(
            collected_at=datetime.now().astimezone(),
            hostname=platform.node(),
            os_name=os_name,
            os_version=os_version,
            os_build=os_build,
            machine=platform.machine(),
            cpu_model=cpu_model,
            cpu_physical=psutil.cpu_count(logical=False) or 0,
            cpu_logical=psutil.cpu_count(logical=True) or 0,
            cpu_freq_mhz=cpu_freq_mhz,
            ram_total_bytes=mem.total,
            ram_available_bytes=mem.available,
            disks=tuple(disks),
            software=(),
        )
