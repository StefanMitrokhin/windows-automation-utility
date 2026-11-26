from __future__ import annotations

import sys
import threading
import time

from deskkit.platform.process import SubprocessRunner


def test_timeout_kills_process() -> None:
    runner = SubprocessRunner()
    result = runner.run(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        timeout_s=0.2,
    )
    assert result.timed_out is True
    assert result.exit_code is None


def test_terminate_sleeping_process() -> None:
    runner = SubprocessRunner()

    def terminate_later() -> None:
        time.sleep(0.5)
        runner.terminate()

    threading.Thread(target=terminate_later, daemon=True).start()
    start = time.monotonic()
    result = runner.run(
        [sys.executable, "-c", "import time; time.sleep(30)"],
        timeout_s=30.0,
    )
    assert time.monotonic() - start < 10
    assert result.cancelled is True
