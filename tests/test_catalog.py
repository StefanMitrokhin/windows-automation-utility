from __future__ import annotations

import pytest

from deskkit.catalog import CATALOG, Catalog
from deskkit.errors import ValidationError


def test_count_and_unique_ids() -> None:
    assert len(CATALOG) == 15
    assert len({p.id for p in CATALOG}) == 15


def test_presets_match_table() -> None:
    catalog = Catalog()
    assert catalog.ids_for_preset("home") == (
        "7zip.7zip",
        "VideoLAN.VLC",
        "Google.Chrome",
        "Telegram.TelegramDesktop",
        "SumatraPDF.SumatraPDF",
    )
    assert catalog.ids_for_preset("office") == (
        "7zip.7zip",
        "Google.Chrome",
        "Telegram.TelegramDesktop",
        "LibreOffice.LibreOffice",
        "Adobe.Acrobat.Reader.64-bit",
        "Zoom.Zoom",
    )
    assert catalog.ids_for_preset("dev") == (
        "7zip.7zip",
        "Git.Git",
        "Microsoft.VisualStudioCode",
        "Python.Python.3.12",
        "Notepad++.Notepad++",
    )


def test_unknown_id() -> None:
    with pytest.raises(ValidationError) as exc:
        Catalog().get("missing")
    assert str(exc.value).startswith("Неизвестная программа:")


def test_unknown_preset() -> None:
    with pytest.raises(ValidationError) as exc:
        Catalog().ids_for_preset("missing")
    assert str(exc.value).startswith("Неизвестный набор:")
