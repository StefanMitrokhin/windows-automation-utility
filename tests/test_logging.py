from __future__ import annotations

from logging.handlers import RotatingFileHandler
from pathlib import Path

from deskkit.logging_setup import read_log_tail, setup_logging


def test_creates_file(context, tmp_path: Path) -> None:
    log_path = tmp_path / "deskkit.log"
    logger = setup_logging(log_path, verbose=False)
    logger.info("проверка")
    for handler in logger.handlers:
        handler.flush()
    assert "проверка" in log_path.read_text(encoding="utf-8")

    from deskkit.ui.presenters import LogsPresenter

    lp = LogsPresenter(context)
    assert lp.directory() == context.paths.log_dir
    assert lp.text()


def test_rotation_settings(tmp_path: Path) -> None:
    logger = setup_logging(tmp_path / "log", verbose=False)
    handler = next(h for h in logger.handlers if isinstance(h, RotatingFileHandler))
    assert handler.maxBytes == 1_000_000
    assert handler.backupCount == 5
    duplicate = setup_logging(tmp_path / "log", verbose=True)
    assert duplicate is logger


def test_missing_tail(tmp_path: Path) -> None:
    assert read_log_tail(tmp_path / "missing") == "Журнал пока пуст."


def test_verbose_enables_debug_on_stderr(tmp_path: Path) -> None:
    import logging

    logger = setup_logging(tmp_path / "log", verbose=True)
    stream = next(h for h in logger.handlers if isinstance(h, logging.StreamHandler))
    assert stream.level == logging.DEBUG
