from __future__ import annotations

from collections.abc import Sequence

from deskkit.errors import ValidationError
from deskkit.models import Package

CATALOG: tuple[Package, ...] = (
    Package("7zip.7zip", "7-Zip", "Архиватор", ("home", "office", "dev")),
    Package("VideoLAN.VLC", "VLC", "Проигрыватель видео", ("home",)),
    Package("Google.Chrome", "Google Chrome", "Браузер", ("home", "office")),
    Package("Telegram.TelegramDesktop", "Telegram", "Мессенджер", ("home", "office")),
    Package("SumatraPDF.SumatraPDF", "SumatraPDF", "Просмотр PDF", ("home",)),
    Package("LibreOffice.LibreOffice", "LibreOffice", "Офисный пакет", ("office",)),
    Package("Adobe.Acrobat.Reader.64-bit", "Adobe Acrobat Reader", "Просмотр PDF", ("office",)),
    Package("Zoom.Zoom", "Zoom", "Видеозвонки", ("office",)),
    Package("Git.Git", "Git", "Система контроля версий", ("dev",)),
    Package("Microsoft.VisualStudioCode", "Visual Studio Code", "Редактор кода", ("dev",)),
    Package("Python.Python.3.12", "Python 3.12", "Интерпретатор Python", ("dev",)),
    Package("Notepad++.Notepad++", "Notepad++", "Текстовый редактор", ("dev",)),
    Package("Mozilla.Firefox", "Mozilla Firefox", "Браузер", ()),
    Package("Microsoft.PowerToys", "PowerToys", "Утилиты Microsoft", ()),
    Package("Yandex.Browser", "Яндекс Браузер", "Браузер", ()),
)


class Catalog:
    def __init__(self, packages: tuple[Package, ...] = CATALOG) -> None:
        self._packages = packages
        self._by_id = {p.id: p for p in packages}

    def packages(self) -> tuple[Package, ...]:
        return self._packages

    def get(self, package_id: str) -> Package:
        package = self._by_id.get(package_id)
        if package is None:
            raise ValidationError(f"Неизвестная программа: {package_id}")
        return package

    def ids_for_preset(self, preset: str) -> tuple[str, ...]:
        ids = tuple(p.id for p in self._packages if preset in p.presets)
        if not ids:
            raise ValidationError(f"Неизвестный набор: {preset}")
        return ids

    def require_ids(self, package_ids: Sequence[str]) -> tuple[Package, ...]:
        return tuple(self.get(pid) for pid in package_ids)
