from __future__ import annotations

from deskkit.cancel import CancellationToken


def test_is_cancelled_flag() -> None:
    token = CancellationToken()
    assert token.is_cancelled() is False
    token.cancel()
    assert token.is_cancelled() is True
