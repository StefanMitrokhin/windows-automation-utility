from __future__ import annotations

import sys

import pytest

pytestmark = pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")


def test_is_admin_returns_bool() -> None:
    from deskkit.platform.process import SubprocessRunner
    from deskkit.platform.windows import WindowsPlatform

    assert isinstance(WindowsPlatform(SubprocessRunner()).is_admin(), bool)


def test_resolve_winget_type() -> None:
    from deskkit.platform.process import SubprocessRunner
    from deskkit.platform.windows import WindowsPlatform

    result = WindowsPlatform(SubprocessRunner()).resolve_winget()
    assert result is None or isinstance(result, str)


def test_query_recycle_bin_readonly() -> None:
    from deskkit.errors import DeskKitError
    from deskkit.platform.process import SubprocessRunner
    from deskkit.platform.windows import WindowsPlatform

    platform = WindowsPlatform(SubprocessRunner())
    try:
        size, count = platform.query()
        assert size >= 0 and count >= 0
    except DeskKitError:
        pass
