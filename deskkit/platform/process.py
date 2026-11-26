from __future__ import annotations

import subprocess
import threading
from collections.abc import Sequence

from deskkit.models import CommandResult
from deskkit.platform.commands import subprocess_kwargs


class SubprocessRunner:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._process: subprocess.Popen[str] | None = None
        self._cancelled = False

    def run(self, args: Sequence[str], timeout_s: float) -> CommandResult:
        self._cancelled = False
        with self._lock:
            proc = subprocess.Popen(
                list(args),
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="replace",
                **subprocess_kwargs(),
            )
            self._process = proc
        try:
            stdout, stderr = proc.communicate(timeout=timeout_s)
            exit_code = proc.returncode
            cancelled = self._cancelled
            with self._lock:
                self._process = None
            return CommandResult(
                args=tuple(args),
                exit_code=exit_code,
                stdout=stdout,
                stderr=stderr,
                timed_out=False,
                cancelled=cancelled,
            )
        except subprocess.TimeoutExpired:
            proc.kill()
            stdout, stderr = proc.communicate()
            with self._lock:
                self._process = None
            return CommandResult(
                args=tuple(args),
                exit_code=None,
                stdout=stdout,
                stderr=stderr,
                timed_out=True,
                cancelled=False,
            )

    def terminate(self) -> None:
        with self._lock:
            proc = self._process
        if proc is not None and proc.poll() is None:
            self._cancelled = True
            proc.kill()
