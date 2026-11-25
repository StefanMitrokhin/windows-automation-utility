# DeskKit — план реализации

Статус документа: это единственный артефакт планирования. Продуктового кода здесь нет. Блоки `toml`, `python`, `iss`, `yaml` и `text` ниже — точный текст будущих файлов или точный контракт, который реализация копирует без переименований.

Исполнитель (Composer) реализует этот план дословно.

- Не добавлять возможности, экраны, команды, зависимости и файлы, которых нет в дереве из раздела 2.
- Не менять зафиксированные версии, имена классов, сигнатуры, коды выхода, тексты, которые тесты сравнивают целиком, и идентификаторы winget.
- Не менять этот файл во время реализации.
- Если внутри одного раздела два абзаца расходятся, верным считается тот, что ниже. Если расходятся сигнатура в разделе 5 и пример в разделе 7, верной считается сигнатура, а пример приводится к ней.
- Комментарии в коде — только там, где план прямо просит комментарий. Докстринги публичных классов и функций — на английском, одна строка, без пересказа типов. Идентификаторы — на английском. Все строки, которые видит пользователь, — на русском и только из `deskkit/ui/strings.py` либо из функций `deskkit/text.py`, перечисленных в разделе 5.
- В каждом файле пакета `deskkit/` первая строка кода: `from __future__ import annotations`.
- Аннотации типов обязательны на всех функциях и методах пакета `deskkit/`. `Any` не использовать. Для свободного JSON-словаря тип `dict[str, object]`.
- Запрещены `shell=True`, `os.system`, `eval`, `exec`, `pickle`, `subprocess` со строковой командой, сетевые библиотеки и любые запросы, кроме процесса `winget`, который запускает сам Windows.

Продукт v1 собирается одним разработчиком как портфолио: настройка и обслуживание Windows для дома и небольшого офиса. Автор — Стефан Митрохин, GitHub `Stephanchik`. Репозиторий: `https://github.com/Stephanchik/windows-automation-utility`. Лицензия уже лежит в `LICENSE` (MIT, Copyright (c) 2026 Stephanchik) и не переписывается.

---

## 1. Цели и вне рамок

### 1.1. Цели v1

DeskKit — локальная программа для Windows 10 64-bit и Windows 11 64-bit. Она делает шесть вещей:

1. Ставит программы из фиксированного каталога через `winget` (наборы «Дом», «Офис», «Разработка» и ручные галочки).
2. Показывает, сколько места занимают временные файлы, корзина и кэш трёх браузеров, и удаляет это только после подтверждения.
3. Собирает отчёт о CPU, RAM, дисках, версии ОС и установленных программах и сохраняет его в один файл HTML или Excel.
4. Показывает автозагрузку (два ключа Run и две папки Startup) и выключает или включает запись обратно, не удаляя её безвозвратно.
5. Упаковывает выбранные папки в zip на другой диск или в другую папку и ставит одну задачу Планировщика Windows.
6. Хранит эти настройки в JSON, чтобы перенести файл на другой ПК и повторить установку программ.

Рядом с окном есть командная строка. Установщик — один `.exe` (PyInstaller + Inno Setup) с ярлыками, удалением и версией в свойствах файла. Сборка установщика идёт в GitHub Actions на `windows-latest` и прикрепляется к GitHub Release при теге `v*`.

Каждое действие, которое пишет на диск, ставит программы, меняет реестр, переименовывает ярлыки или создаёт задачу планировщика, сначала показывает состав операции. Без подтверждения запись не начинается. Права администратора не запрашиваются при старте.

### 1.2. Вне рамок v1

Реализация не делает следующее и не оставляет «заготовки на будущее» в коде (пустые меню, неиспользуемые кнопки, закомментированные вызовы):

- восстановление из zip, шифрование архива, инкрементные копии, теневые копии VSS, копии открытых файлов;
- чистку реестра, куки, пароли, историю, закладки, расширения браузеров, prefetch, гибернацию, WinSxS;
- обновление Windows, драйверов, BIOS, антивирус, брандмауэр, дефрагментацию, «ускорители»;
- управление службами, задачами планировщика чужих программ, RunOnce, групповыми политиками;
- разбор `.lnk` (цель ярлыка не читается; показывается имя файла);
- произвольный ввод id winget: ставится только id из каталога раздела 5;
- автообновление DeskKit, телеметрию, аккаунт, облако, PyPI-публикацию;
- кодовую подпись Authenticode (см. раздел 14);
- перевод интерфейса: язык один — русский. Отдельного механизма gettext нет;
- 32-bit Windows, Windows 7/8, Windows Server как цель поддержки;
- второй установщик, MSI, winget-манифест самого DeskKit, chocolatey.

### 1.3. Зафиксированные решения

Эти решения закрыты. Не выбирать заново.

| Решение | Значение |
| --- | --- |
| Имя в интерфейсе и установщике | DeskKit |
| Имя пакета Python | `deskkit` |
| Оконный exe | `DeskKit.exe` |
| Консольный exe | `DeskKit-cli.exe` |
| Версия | `0.1.0` |
| AppId Inno Setup | `{8F3C1A2E-6B47-4D91-9C5E-2A7F0B4D8E16}` |
| Имя задачи планировщика | сначала `\DeskKit\Backup`, если создать не удалось — `DeskKit Backup` |
| GUI | CustomTkinter `6.0.0` |
| Тема | `customtkinter.set_default_color_theme("blue")`, `set_appearance_mode("system")` |
| Шрифт | `("Segoe UI", размер)` |
| Окно | `1100x720`, `minsize(960, 640)` |
| Python | `>=3.11`, CI: 3.11 и 3.12 на Ubuntu, 3.12 на Windows |
| Установка программ | только источник `winget`, флаг `--no-upgrade`, область по умолчанию `user` |
| Временные файлы | не удалять изменённые за последние 24 часа |
| Корзина и кэш браузера | без фильтра по возрасту |
| Подтверждение в CLI | код выхода `3`, если нет `--yes` и нет `--dry-run` |
| `--dry-run` вместе с `--yes` | побеждает `--dry-run`, записи нет, код `0` |

Почему CustomTkinter, а не альтернативы:

- tkinter из стандартной библиотеки на Windows выглядит как утилита десятилетней давности. Для портфолио, которое увидит заказчик, этого мало.
- PySide6 даёт нативный вид Qt, но тянет десятки мегабайт, лицензию LGPL (её можно соблюсти, но это отдельная возня в установщике) и больше кода на те же шесть экранов. За неделю это съедает отчёт, копии и CI.
- CustomTkinter 6.0.0 поверх Tk даёт современное окно, тёмную и светлую схему от настройки Windows, и остаётся чистым Python. На Windows Tcl/Tk уже входит в официальный установщик Python, PyInstaller его забирает. Лицензия пакета 6.0.0 на PyPI — открытая (в метаданных указаны CC0 и классификатор MIT), библиотеку можно класть в установщик.

Интерфейс русский, потому что заказчик плана — домашний пользователь и небольшой офис, а README пишется для них по-русски. Имена команд CLI английские (`install`, `clean`, `report`, `startup`, `backup`, `profile`, `gui`), тексты ответов русские.

Два exe, а не один: оконная подсистема не отдаёт stdout в уже открытую консоль, консольная подсистема показывает чёрное окно при запуске с ярлыка и во время ночной копии. `DeskKit.exe` собирается с `console=False` и вешается на ярлыки. `DeskKit-cli.exe` собирается с `console=True`; им пользуются командная строка и Планировщик. Дублирование рантайма PyInstaller — принятая цена, чтобы не прятать чужое окно консоли. UPX не включать.

---

## 2. Точное дерево файлов

После реализации в репозитории есть только эти пути сверх уже существующих `.gitignore`, `LICENSE` и заменённого `README.md`. Пустых `__init__.py` достаточно там, где ниже не задано иное содержимое.

```text
pyproject.toml
README.md
.gitignore                                          # правка, не новый файл
deskkit/__init__.py
deskkit/__main__.py
deskkit/entry_gui.py
deskkit/entry_cli.py
deskkit/errors.py
deskkit/models.py
deskkit/cancel.py
deskkit/paths.py
deskkit/safety.py
deskkit/text.py
deskkit/logging_setup.py
deskkit/catalog.py
deskkit/profile.py
deskkit/app_context.py
deskkit/platform/__init__.py
deskkit/platform/protocols.py
deskkit/platform/commands.py
deskkit/platform/process.py
deskkit/platform/files.py
deskkit/platform/system_probe.py
deskkit/platform/windows.py
deskkit/services/__init__.py
deskkit/services/install.py
deskkit/services/cleanup.py
deskkit/services/report.py
deskkit/services/startup.py
deskkit/services/backup.py
deskkit/services/schedule.py
deskkit/cli/__init__.py
deskkit/cli/main.py
deskkit/ui/__init__.py
deskkit/ui/strings.py
deskkit/ui/theme.py
deskkit/ui/widgets.py
deskkit/ui/presenters.py
deskkit/ui/app.py
deskkit/ui/screens/__init__.py
deskkit/ui/screens/home.py
deskkit/ui/screens/install.py
deskkit/ui/screens/cleanup.py
deskkit/ui/screens/report.py
deskkit/ui/screens/startup.py
deskkit/ui/screens/backup.py
deskkit/ui/screens/profile.py
deskkit/ui/screens/logs.py
deskkit/assets/icon.png
deskkit/assets/icon.ico
installer/make_icon.py
installer/deskkit-gui.spec
installer/deskkit-cli.spec
installer/version_info.txt
installer/installer.iss
.github/workflows/ci.yml
.github/workflows/release.yml
tests/conftest.py
tests/fakes.py
tests/test_version.py
tests/test_paths.py
tests/test_safety.py
tests/test_text.py
tests/test_catalog.py
tests/test_profile.py
tests/test_commands.py
tests/test_process.py
tests/test_files.py
tests/test_cleanup.py
tests/test_report.py
tests/test_startup.py
tests/test_backup.py
tests/test_schedule.py
tests/test_install.py
tests/test_cli.py
tests/test_presenters.py
tests/test_logging.py
tests/test_windows_readonly.py
docs/PLAN.md
```

Каталог `installer/` не является пакетом Python: файла `installer/__init__.py` нет. Так он не затеняет сторонний модуль `packaging` при запуске из корня репозитория.

Папки `docs/screenshots/` в v1 нет. Её создаст автор после ручных снимков, не реализация.

Правка `.gitignore`: в блоке PyInstaller оставить `*.manifest` и `*.spec`, сразу под `*.spec` добавить две строки:

```gitignore
!installer/deskkit-gui.spec
!installer/deskkit-cli.spec
```

Других правок `.gitignore` нет.

---

## 3. Зависимости и pyproject.toml

Единственный файл зависимостей — `pyproject.toml` целиком вот такого содержания. Lock-файла нет. Версии не поднимать и не ослаблять до `>=`.

Прямые зависимости исполнения:

| Пакет | Версия | Зачем |
| --- | --- | --- |
| customtkinter | 6.0.0 | окно |
| psutil | 7.2.2 | CPU, RAM, диски |
| openpyxl | 3.1.5 | Excel |

Зависимости разработки (extra `dev`, их же ставит CI и релиз):

| Пакет | Версия | Зачем |
| --- | --- | --- |
| pytest | 9.2.0 | тесты |
| pytest-cov | 7.1.0 | порог покрытия |
| ruff | 0.17.6 | lint и формат |
| pyinstaller | 6.22.3 | exe, только Windows-релиз |
| pillow | 13.0.0 | один запуск `make_icon.py` |

Транзитивные пакеты (`darkdetect`, `packaging`, `et-xmlfile`, `altgraph`) не пинить и не импортировать из нашего кода. `pywin32`, `requests`, `click`, `typer`, `pydantic`, `jinja2` не добавлять.

Файл `pyproject.toml`:

```toml
[build-system]
requires = ["setuptools==84.2.1"]
build-backend = "setuptools.build_meta"

[project]
name = "deskkit"
version = "0.1.0"
description = "Настройка и обслуживание Windows для дома и небольшого офиса"
readme = "README.md"
requires-python = ">=3.11"
license = "MIT"
license-files = ["LICENSE"]
authors = [{ name = "Стефан Митрохин" }]
keywords = ["windows", "winget", "desktop", "automation"]
classifiers = [
  "Development Status :: 3 - Alpha",
  "Environment :: Win32 (MS Windows)",
  "License :: OSI Approved :: MIT License",
  "Operating System :: Microsoft :: Windows :: Windows 10",
  "Operating System :: Microsoft :: Windows :: Windows 11",
  "Programming Language :: Python :: 3.11",
  "Programming Language :: Python :: 3.12",
  "Topic :: System :: Systems Administration",
]
dependencies = [
  "customtkinter==6.0.0",
  "psutil==7.2.2",
  "openpyxl==3.1.5",
]

[project.optional-dependencies]
dev = [
  "pytest==9.2.0",
  "pytest-cov==7.1.0",
  "ruff==0.17.6",
  "pyinstaller==6.22.3",
  "pillow==13.0.0",
]

[project.scripts]
deskkit = "deskkit.__main__:main"

[project.urls]
Homepage = "https://github.com/Stephanchik/windows-automation-utility"
Issues = "https://github.com/Stephanchik/windows-automation-utility/issues"

[tool.setuptools.packages.find]
include = ["deskkit*"]

[tool.setuptools.package-data]
deskkit = ["assets/*"]

[tool.ruff]
target-version = "py311"
line-length = 100
extend-exclude = [
  "installer/deskkit-gui.spec",
  "installer/deskkit-cli.spec",
  "build",
  "dist",
]

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B", "SIM", "ANN", "RUF"]
ignore = []

[tool.ruff.lint.per-file-ignores]
"tests/**" = ["ANN"]

[tool.ruff.lint.isort]
known-first-party = ["deskkit"]

[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "-q --strict-markers --cov=deskkit --cov-report=term-missing --cov-fail-under=90"

[tool.coverage.run]
branch = true
source = ["deskkit"]
omit = [
  "deskkit/ui/app.py",
  "deskkit/ui/widgets.py",
  "deskkit/ui/theme.py",
  "deskkit/ui/screens/*",
  "deskkit/entry_gui.py",
  "deskkit/entry_cli.py",
  "deskkit/platform/windows.py",
  "deskkit/platform/system_probe.py",
]

[tool.coverage.report]
fail_under = 90
show_missing = true
exclude_lines = ["if __name__ == .__main__.:"]
```

Покрытие 90% считается по пакету за вычетом `omit`: окна, тонкий Win32-адаптер и зонд psutil на Linux не запускаются как реальные окна и реальный Win32. Их поведение задано разделом 5 и ручной приёмкой раздела 13. Порог один и тот же в `addopts` и в `coverage.report`, чтобы локальный `pytest` совпадал с CI.

Установка окружения для разработки:

```text
python -m pip install -e ".[dev]"
```

Команды проверки, они же приёмка каждого шага, где сказано «зелёный прогон»:

```text
ruff check .
ruff format --check .
pytest
```

`ruff format .` запускать при реализации, пока `--check` не станет чистым. Отдельного mypy нет.

---

## 4. Архитектура

Три слоя. Зависимости направлены только внутрь: UI и CLI знают сервисы, сервисы знают протоколы и модели, сервисы не знают CustomTkinter, argparse и `winreg`.

```text
entry_gui.py / entry_cli.py / __main__.py
        |                |
        v                v
   ui/app.py         cli/main.py
   ui/screens/*           |
   ui/presenters.py       |
        \                /
         v              v
          services/*
               |
               v
     platform/protocols.py  <--- Fake* в tests/fakes.py
               |
               v
     windows.py, process.py, files.py, system_probe.py
```

`app_context.build_context` — единственное место, которое на Windows собирает боевые реализации, а в тестах не вызывается. Тесты создают сервисы сами и передают подделки.

Поток любой записи:

1. Сервис строит preview-объект, не меняя систему. Preview можно звать сколько угодно раз.
2. Вызывающий передаёт `dry_run: bool` и `confirmed: bool`.
3. Если `dry_run` истинно, сервис возвращает результат с `dry_run=True` и ничего не пишет. `confirmed` при этом не важен.
4. Если `dry_run` ложно и `confirmed` ложно, сервис выбрасывает `ConfirmationRequired` до первой записи.
5. Если оба позволяют запись, сервис выполняет работу и между единицами (пакет, цель очистки, файл архива) вызывает `cancel.raise_if_cancelled()`.

Единицы отмены:

- установка — между пакетами, плюс `SubprocessRunner.terminate()` обрывает текущий `winget`;
- очистка — между файлами;
- архив — между файлами, до открытия zip и во время обхода;
- автозагрузка — одна запись на вызов, отмены посередине нет;
- планировщик — одна команда `schtasks` на вызов.

Потоки UI: сервис вызывается из `threading.Thread` через `TaskRunner` (раздел 6). В сервисах нет `tkinter` и нет ожидания UI. CLI вызывает сервисы синхронно в главном потоке.

Коды выхода процесса (и возвращаемые значения `dispatch` / `run`):

| Код | Когда |
| --- | --- |
| 0 | успех, в том числе сухой прогон и пропуск уже установленных пакетов, если ни один пакет не упал |
| 1 | `DeskKitError`, кроме подтверждения и отмены; частичный провал установки тоже 1 |
| 2 | ошибка argparse (его собственный `SystemExit`) |
| 3 | `ConfirmationRequired`: текст предварительного просмотра уже напечатан, изменений нет |
| 4 | `CancelledError` |

`build_context` на системе, где `sys.platform != "win32"`, выбрасывает `UnsupportedOSError` с текстом `DeskKit работает только в Windows.`. Тесты этот конструктор не вызывают. Импорт пакета `deskkit.services` на Linux обязан проходить и не обязан тянуть `tkinter`, `customtkinter`, `winreg`.

Журнал: `%LOCALAPPDATA%\DeskKit\logs\deskkit.log` на Windows и `~/.deskkit/logs/deskkit.log`, если переменной `LOCALAPPDATA` нет. Ротация 1_000_000 байт, 5 файлов, кодировка UTF-8. Уровень файла DEBUG, уровень stderr INFO, при `--verbose` stderr тоже DEBUG. В INFO не попадает содержимое чужих файлов и полный stdout winget (это DEBUG).

Профиль по умолчанию: `%APPDATA%\DeskKit\profile.json`, а без `APPDATA` — `~/.deskkit/profile.json`. Задача планировщика всегда читает профиль по этому пути, без длинных аргументов в `/TR`.

---

## 5. Модули, сигнатуры и поведение

Ниже перечислены все публичные типы и функции. Приватные помощники допустимы, если их имена начинаются с `_` и поведение снаружи не отличается от описанного. Не вводить вторые классы с тем же смыслом.

### 5.1. `deskkit/__init__.py`

```python
__version__ = "0.1.0"
```

### 5.2. `deskkit/errors.py`

```python
class DeskKitError(Exception):
    """Base error for expected failures."""

class ConfirmationRequired(DeskKitError):
    """Raised when a write was requested without confirmation."""

class CancelledError(DeskKitError):
    """Raised when the user cancelled between units of work."""

class ValidationError(DeskKitError):
    """Raised when input or a profile field is invalid."""

class ProfileVersionError(ValidationError):
    """Raised when schema_version is not 1."""

class AdminRequiredError(DeskKitError):
    """Raised when an HKLM startup change is attempted without admin rights."""

class UnsupportedOSError(DeskKitError):
    """Raised when the real Windows stack is built on another OS."""

class WingetNotFoundError(DeskKitError):
    """Raised when winget.exe cannot be resolved."""

class ScheduleError(DeskKitError):
    """Raised when a scheduled task cannot be created or parsed."""

class PathNotAllowedError(ValidationError):
    """Raised when a path is outside the allowed set."""
```

Тексты исключений — русские, их задают вызывающие через `raise ValidationError("...")`. Тексты, которые тесты проверяют целиком, приведены в разделе 10 рядом с тестом. Остальные тексты ошибок тоже русские, короткие, без трассировки.

### 5.3. `deskkit/models.py`

Все модели — `@dataclass(frozen=True)` кроме тех, где прямо сказано иное. Перечисления — `enum.Enum` со строковыми значениями.

```python
class InstallScope(enum.Enum):
    USER = "user"
    AUTO = "auto"

class InstallStatus(enum.Enum):
    SUCCESS = "success"
    SKIPPED_INSTALLED = "skipped_installed"
    ADMIN_REQUIRED = "admin_required"
    FAILED = "failed"

class CleanupTargetId(enum.Enum):
    USER_TEMP = "user_temp"
    WINDOWS_TEMP = "windows_temp"
    RECYCLE_BIN = "recycle_bin"
    CHROME_CACHE = "chrome_cache"
    EDGE_CACHE = "edge_cache"
    FIREFOX_CACHE = "firefox_cache"

class Hive(enum.Enum):
    HKCU = "HKCU"
    HKLM = "HKLM"

class StartupSource(enum.Enum):
    HKCU_RUN = "hkcu_run"
    HKLM_RUN = "hklm_run"
    USER_STARTUP = "user_startup"
    COMMON_STARTUP = "common_startup"

class RegKind(enum.Enum):
    SZ = "sz"
    EXPAND_SZ = "expand_sz"
    OTHER = "other"
```

Поля датаклассов:

```python
class Package:
    id: str
    name: str
    summary: str
    presets: tuple[str, ...]          # подмножество {"home", "office", "dev"}

class CommandResult:
    args: tuple[str, ...]
    exit_code: int | None
    stdout: str
    stderr: str
    timed_out: bool
    cancelled: bool

class InstallItemResult:
    package_id: str
    name: str
    status: InstallStatus
    exit_code: int | None
    message: str

class InstallPreview:
    package_ids: tuple[str, ...]
    names: tuple[str, ...]
    scope: InstallScope
    winget_found: bool

class InstallReport:
    items: tuple[InstallItemResult, ...]
    dry_run: bool
    cancelled: bool

class FileEntry:
    path: Path
    size: int
    modified_at: datetime          # timezone-aware
    is_symlink: bool
    is_reparse: bool
    unreadable: bool
    error: str | None

class CleanupTargetPreview:
    target: CleanupTargetId
    roots: tuple[str, ...]
    file_count: int
    byte_count: int
    skipped_recent: int
    skipped_links: int
    unreadable: int
    warnings: tuple[str, ...]
    absent: bool

class CleanupPreview:
    targets: tuple[CleanupTargetPreview, ...]

    @property
    def total_bytes(self) -> int: ...
    @property
    def total_files(self) -> int: ...

class CleanupResult:
    preview: CleanupPreview
    deleted_files: int
    freed_bytes: int
    skipped_locked: int
    errors: tuple[str, ...]
    dry_run: bool
    cancelled: bool

class DiskInfo:
    device: str
    mountpoint: str
    fstype: str
    total_bytes: int
    used_bytes: int
    free_bytes: int
    available: bool

class SoftwareEntry:
    name: str
    version: str
    publisher: str
    install_date: str

class SystemSnapshot:
    collected_at: datetime
    hostname: str
    os_name: str
    os_version: str
    os_build: str
    machine: str
    cpu_model: str
    cpu_physical: int
    cpu_logical: int
    cpu_freq_mhz: float | None
    ram_total_bytes: int
    ram_available_bytes: int
    disks: tuple[DiskInfo, ...]
    software: tuple[SoftwareEntry, ...]

class RegValue:
    name: str
    data: str
    kind: RegKind

class StartupEntry:
    id: str
    source: StartupSource
    name: str
    command: str
    enabled: bool
    needs_admin: bool

class ScheduleSettings:
    enabled: bool
    frequency: str                 # "daily" или "weekly"
    weekday: str                   # MON..SUN, при daily всё равно хранится
    time: str                      # "HH:MM"

class BackupPreview:
    sources: tuple[str, ...]
    destination: str
    file_count: int
    byte_count: int
    archive_name: str
    rotate_names: tuple[str, ...]
    skipped: tuple[str, ...]
    warnings: tuple[str, ...]

class BackupResult:
    preview: BackupPreview
    archive_path: str | None
    written_files: int
    skipped: tuple[str, ...]
    dry_run: bool
    cancelled: bool

class ScheduleStatus:
    exists: bool
    enabled: bool
    frequency: str | None
    weekday: str | None
    time: str | None
    task_name: str | None
    warning: str | None

class InstallSettings:
    package_ids: tuple[str, ...]
    scope: InstallScope

class CleanupSettings:
    targets: tuple[CleanupTargetId, ...]

class BackupSettings:
    sources: tuple[str, ...]
    destination: str | None
    keep_last: int
    schedule: ScheduleSettings

class ReportSettings:
    format: str                    # "html" или "xlsx"
    last_directory: str | None

class Profile:
    schema_version: int
    install: InstallSettings
    cleanup: CleanupSettings
    backup: BackupSettings
    report: ReportSettings

class ZipMember:
    source: Path
    arcname: str
    size: int

class ElevationResult:
    started: bool
    message: str

class CleanupRoots:
    user_temp: Path
    windows_temp: Path
    chrome_user_data: Path
    edge_user_data: Path
    firefox_profiles: Path

class AppPaths:
    profile_path: Path
    log_path: Path
    log_dir: Path
```

`CleanupPreview.total_bytes` суммирует `byte_count` целей. `total_files` суммирует `file_count`.

Идентификатор автозагрузки: `f"{source.value}|{name}"`. Имя со символом `|` в список не попадает (раздел 5.16).

### 5.4. `deskkit/cancel.py`

```python
class CancellationToken:
    def __init__(self) -> None: ...
    def cancel(self) -> None: ...
    def is_cancelled(self) -> bool: ...
    def raise_if_cancelled(self) -> None: ...
```

Внутри `threading.Event`. `raise_if_cancelled` бросает `CancelledError("Остановлено.")`, если событие установлено. Новый токен не отменён. Токен не сбрасывается.

### 5.5. `deskkit/paths.py`

Функции читают только переданный словарь `env`, не `os.environ` напрямую. `build_context` передаёт `os.environ`.

```python
def profile_path_from_env(env: Mapping[str, str], home: Path) -> Path: ...
def log_path_from_env(env: Mapping[str, str], home: Path) -> Path: ...
def cleanup_roots_from_env(env: Mapping[str, str], home: Path) -> CleanupRoots: ...
def startup_folders_from_env(env: Mapping[str, str]) -> tuple[Path, Path]: ...
```

Правила:

- `profile_path_from_env`: если в `env` есть непустой `APPDATA`, путь `Path(APPDATA) / "DeskKit" / "profile.json"`. Иначе `home / ".deskkit" / "profile.json"`.
- `log_path_from_env`: если есть непустой `LOCALAPPDATA`, `%LOCALAPPDATA%\DeskKit\logs\deskkit.log`. Иначе `home / ".deskkit" / "logs" / "deskkit.log"`. `AppPaths.log_dir` — родитель этого файла.
- `cleanup_roots_from_env`:
  - `user_temp` = `TEMP`, иначе `TMP`, иначе `home / "AppData" / "Local" / "Temp"`;
  - `windows_temp` = `Path(SYSTEMROOT или "C:\\Windows") / "Temp"`;
  - `chrome_user_data` = `LOCALAPPDATA или home/"AppData"/"Local"` / `Google/Chrome/User Data`;
  - `edge_user_data` = тот же корень / `Microsoft/Edge/User Data`;
  - `firefox_profiles` = тот же корень / `Mozilla/Firefox/Profiles`.
- `startup_folders_from_env` возвращает пару `(user_startup, common_startup)`:
  - user: `APPDATA / "Microsoft/Windows/Start Menu/Programs/Startup"`, если `APPDATA` нет — `home / "AppData/Roaming/Microsoft/Windows/Start Menu/Programs/Startup"`;
  - common: `PROGRAMDATA или "C:\\ProgramData"` / `Microsoft/Windows/Start Menu/Programs/Startup`.

Функции ничего не создают на диске.

### 5.6. `deskkit/safety.py`

```python
DENIED_PREFIXES: tuple[str, ...] = (
    "windows",
    "program files",
    "program files (x86)",
)

def ensure_absolute(path: Path) -> Path: ...
def is_drive_root(path: Path) -> bool: ...
def is_denied_source(path: Path) -> bool: ...
def destination_conflicts(sources: Sequence[Path], destination: Path) -> bool: ...
def safe_arcname(arcname: str) -> str: ...
def is_reparse_point(path: Path) -> bool: ...
```

Поведение:

- `ensure_absolute` принимает строку через `Path`. Разворачивает `~`. Если после `expanduser` путь не абсолютный — `PathNotAllowedError("Нужен полный путь.")`. Возвращает `path.expanduser()`, без обязательного `resolve`, чтобы несуществующий путь на другом ПК не ломал загрузку профиля.
- `is_drive_root`: истина, если `path` абсолютный и `path == Path(path.anchor)` (для `C:\`, `D:\`, `/`).
- `is_denied_source`: истина для корня диска и если первый компонент пути после якоря, в нижнем регистре, входит в `DENIED_PREFIXES`. То есть запрещены `C:\Windows`, `C:\Windows\System32`, `D:\Program Files\...`, `C:\Program Files (x86)`. Регистр не важен. `C:\Users\...` разрешён.
- `destination_conflicts`: истина, если после `resolve(strict=False)` назначение равно источнику, лежит внутри источника или источник лежит внутри назначения. Сравнение через `Path.is_relative_to`.
- `safe_arcname`: отвергает пустую строку, обратные слеши (вызывающий заранее переводит в `/`), абсолютный путь, префикс `/`, любой сегмент `.` или `..`. Возвращает ту же строку, если она годится. Иначе `PathNotAllowedError`.
- `is_reparse_point`: истина, если `path.is_symlink()`. Дополнительно на Windows, если у `stat()` есть `st_file_attributes` и бит `0x400` (`FILE_ATTRIBUTE_REPARSE_POINT`) установлен — тоже истина. Ошибку `OSError` не глотать: пусть вызовет вызывающий. Для несуществующего пути `is_symlink()` ложно, а `stat` бросит; вызывающий ловит это отдельно. В обходе файлов сначала проверять `DirEntry.is_symlink()` и не вызывать `stat` по ссылке.

### 5.7. `deskkit/text.py`

Единственное место, где собираются многострочные русские тексты CLI и окна подтверждения. Экраны показывают эти строки как есть.

```python
def format_bytes(num: int) -> str: ...
def confirmation_footer() -> str: ...
def install_scope_label(scope: InstallScope) -> str: ...
def install_preview_text(preview: InstallPreview, *, include_footer: bool) -> str: ...
def install_report_text(report: InstallReport) -> str: ...
def cleanup_target_label(target: CleanupTargetId) -> str: ...
def cleanup_preview_text(preview: CleanupPreview, *, include_footer: bool) -> str: ...
def cleanup_result_text(result: CleanupResult) -> str: ...
def report_summary_text(snapshot: SystemSnapshot) -> str: ...
def startup_source_label(source: StartupSource) -> str: ...
def startup_list_text(entries: Sequence[StartupEntry]) -> str: ...
def startup_action_text(entry: StartupEntry, action: str) -> str: ...
def backup_preview_text(preview: BackupPreview, *, include_footer: bool) -> str: ...
def backup_result_text(result: BackupResult) -> str: ...
def schedule_preview_text(argv: Sequence[str]) -> str: ...
def profile_summary_text(profile: Profile) -> str: ...
def output_tail(stdout: str, stderr: str, lines: int = 20) -> str: ...
```

`format_bytes`, точные примеры, которые тест сравнивает целиком:

| Вход | Выход |
| --- | --- |
| 0 | `0 Б` |
| 1023 | `1023 Б` |
| 1024 | `1,0 КБ` |
| 1536 | `1,5 КБ` |
| 1048576 | `1,0 МБ` |
| 1073741824 | `1,0 ГБ` |

Отрицательное значение — `ValueError`. Единицы: `Б`, `КБ`, `МБ`, `ГБ`, `ТБ`. Порог 1024. Для `Б` целое число без дроби. Дальше одна цифра после запятой, разделитель — запятая. Округление обычное половинное вверх через `f"{value:.1f}"` (банковское округление Python здесь не важно: тесты не используют середину `.5` на границе, кроме значений, которые делятся нацело).

`confirmation_footer()` возвращает ровно:

```text
Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено.
```

`install_scope_label`: `USER` → `для текущего пользователя`, `AUTO` → `как решит winget`.

`install_preview_text` при `winget_found=True` и двух пакетах `7-Zip` / `7zip.7zip`, `VLC` / `VideoLAN.VLC`, scope user, `include_footer=True` возвращает ровно (перевод строки `\n`, в конце один `\n`):

```text
Будет установлено: 2
Область: для текущего пользователя
1. 7-Zip (7zip.7zip)
2. VLC (VideoLAN.VLC)
Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено.
```

При `winget_found=False` перед этим блоком строка `winget не найден. Установка не начнётся.` и пустая строка. При `include_footer=False` последней строки-футера нет. Нумерация с 1. Имена и id берутся из preview в том же порядке.

`install_report_text` для отчёта без отмены:

```text
[1/2] 7-Zip — уже установлен, пропуск
[2/2] VLC — установлено
Готово: установлено 1, пропущено 1, ошибок 0
```

Соответствие статуса и хвоста строки:

| Статус | Хвост |
| --- | --- |
| SUCCESS | `установлено` |
| SKIPPED_INSTALLED | `уже установлен, пропуск` |
| ADMIN_REQUIRED | `нужны права администратора` |
| FAILED | `ошибка: {message}` |

Если `report.cancelled`, последняя строка `Остановлено.` вместо строки `Готово: ...`. Если `report.dry_run`, после списка строка `Режим просмотра: команды winget не запускались.` и строки `Готово` нет.

`cleanup_target_label`:

| Id | Подпись |
| --- | --- |
| user_temp | Временные файлы пользователя |
| windows_temp | Временные файлы Windows |
| recycle_bin | Корзина |
| chrome_cache | Кэш Google Chrome |
| edge_cache | Кэш Microsoft Edge |
| firefox_cache | Кэш Firefox |

`cleanup_preview_text` для одной цели `user_temp` с 3 файлами и 1536 байтами, без предупреждений, `include_footer=True`:

```text
К очистке: 1,5 КБ в 3 файлах
Временные файлы пользователя: 3 файлов, 1,5 КБ
Чтобы выполнить, добавьте --yes. Сейчас ничего не изменено.
```

Если `absent`, вместо чисел строка `{подпись}: папка не найдена, пропуск`. Если `warnings` не пуст, каждая предупреждающая строка идёт следом с префиксом `Предупреждение: `.

`cleanup_result_text` при успехе без сухого прогона:

```text
Удалено файлов: {deleted_files}
Освобождено: {format_bytes(freed_bytes)}
Пропущено занятых файлов: {skipped_locked}
```

Каждая строка `errors` добавляется как `Ошибка: {text}`. При `dry_run` вместо этого возвращается preview-текст с футером плюс строка `Режим просмотра: файлы не удалялись.`

`report_summary_text` — не HTML. Ровно такие строки (числа через `format_bytes`):

```text
Компьютер: {hostname}
Система: {os_name} {os_version} сборка {os_build}
Процессор: {cpu_model} ({cpu_physical} физ. / {cpu_logical} лог.)
Память: {format_bytes(ram_available)} свободно из {format_bytes(ram_total)}
Диски:
{mountpoint} {format_bytes(free)} свободно из {format_bytes(total)}
Программ в списке: {n}
```

Если `available` у диска ложно, строка диска `{mountpoint} нет данных`. Если `cpu_freq_mhz` не None, к строке процессора через пробел добавляется `{freq:.0f} МГц`.

`startup_source_label`:

| Source | Подпись |
| --- | --- |
| hkcu_run | Реестр пользователя |
| hklm_run | Общий реестр |
| user_startup | Папка пользователя |
| common_startup | Общая папка |

`startup_list_text`: по строке на запись

```text
{id}	{Вкл|Выкл}	{подпись источника}	{name}	{command}
```

Колонки разделены одним символом табуляции. Пустой список — строка `Автозагрузка пуста.`

`startup_action_text`: `action` равен `disable` или `enable`.

```text
Выключить автозагрузку: {name}
Источник: {подпись}
Команда: {command}
Запись не удаляется. Её можно включить обратно.
```

Для `enable` первая строка `Включить автозагрузку: {name}`, последняя строка `Запись вернётся туда, откуда была убрана.`

`backup_preview_text`:

```text
Архив: {archive_name}
Куда: {destination}
Папок: {n_sources}
Файлов: {file_count}
Размер до сжатия: {format_bytes(byte_count)}
Будут удалены старые архивы: {имена через ", " или "нет"}
```

Плюс футер, если `include_footer`. Каждое предупреждение — строка `Предупреждение: ...`.

`backup_result_text` при записи:

```text
Создан архив: {archive_path}
Файлов в архиве: {written_files}
```

При `dry_run` — preview с футером и строка `Режим просмотра: архив не создавался.`

`schedule_preview_text`:

```text
Будет выполнена команда:
{argv, элементы через пробел, без дополнительной кавычечной логики сверх join}
Задача: \DeskKit\Backup
Пароль не сохраняется. Копия пойдёт, когда вы вошли в Windows.
```

Элементы argv соединяются одним пробелом как есть. Это текст показа, не командная строка для оболочки: реальный запуск всё равно списком аргументов.

`profile_summary_text` — это `json.dumps` словаря профиля с `ensure_ascii=False`, `indent=2`, в конце перевод строки. Ключи и вложенность совпадают с JSON из раздела 5.12. Enum сериализуется своим `.value`.

`output_tail` склеивает stderr и stdout через `\n`, берёт последние `lines` непустых строк, соединяет `\n`.

### 5.8. `deskkit/logging_setup.py`

```python
def setup_logging(log_path: Path, *, verbose: bool) -> logging.Logger: ...
def read_log_tail(path: Path, max_chars: int = 50_000) -> str: ...
```

`setup_logging` создаёт каталог журнала, очищает хендлеры логгера `deskkit`, ставит `propagate = False`, вешает `RotatingFileHandler` (1_000_000, backupCount=5, encoding utf-8, level DEBUG) и `StreamHandler` на stderr (INFO либо DEBUG). Формат: `%(asctime)s %(levelname)s %(name)s %(message)s`. Возвращает `logging.getLogger("deskkit")`.

`read_log_tail`: если файла нет — `Журнал пока пуст.` Если есть — последние `max_chars` символов UTF-8 с `errors="replace"`.

### 5.9. `deskkit/catalog.py`

```python
CATALOG: tuple[Package, ...] = (...)

class Catalog:
    def __init__(self, packages: tuple[Package, ...] = CATALOG) -> None: ...
    def packages(self) -> tuple[Package, ...]: ...
    def get(self, package_id: str) -> Package: ...
    def ids_for_preset(self, preset: str) -> tuple[str, ...]: ...
    def require_ids(self, package_ids: Sequence[str]) -> tuple[Package, ...]: ...
```

`get` и `require_ids` бросают `ValidationError(f"Неизвестная программа: {package_id}")`, если id нет в каталоге. `ids_for_preset` для неизвестного имени бросает `ValidationError(f"Неизвестный набор: {preset}")`. Порядок `ids_for_preset` — порядок `CATALOG`, не алфавит.

Каталог ровно из этих 15 записей, в этом порядке. Поле `presets` — единственный источник наборов. Другого списка наборов в коде нет.

| id | name | summary | presets |
| --- | --- | --- | --- |
| 7zip.7zip | 7-Zip | Архиватор | home, office, dev |
| VideoLAN.VLC | VLC | Проигрыватель видео | home |
| Google.Chrome | Google Chrome | Браузер | home, office |
| Telegram.TelegramDesktop | Telegram | Мессенджер | home, office |
| SumatraPDF.SumatraPDF | SumatraPDF | Просмотр PDF | home |
| LibreOffice.LibreOffice | LibreOffice | Офисный пакет | office |
| Adobe.Acrobat.Reader.64-bit | Adobe Acrobat Reader | Просмотр PDF | office |
| Zoom.Zoom | Zoom | Видеозвонки | office |
| Git.Git | Git | Система контроля версий | dev |
| Microsoft.VisualStudioCode | Visual Studio Code | Редактор кода | dev |
| Python.Python.3.12 | Python 3.12 | Интерпретатор Python | dev |
| Notepad++.Notepad++ | Notepad++ | Текстовый редактор | dev |
| Mozilla.Firefox | Mozilla Firefox | Браузер | — |
| Microsoft.PowerToys | PowerToys | Утилиты Microsoft | — |
| Yandex.Browser | Яндекс Браузер | Браузер | — |

Если на ручной проверке Windows команда `winget show --id Yandex.Browser --exact --source winget` завершается ненулевым кодом, эту одну строку удаляют из каталога и поправляют тест числа пакетов. Другие id так не трогать и заменой не подбирать: остановиться и оставить запись в журнале прогона. Для реализации на Linux эту проверку не выполнять и строку не удалять.

Наборы, которые получаются из таблицы:

- `home`: `7zip.7zip`, `VideoLAN.VLC`, `Google.Chrome`, `Telegram.TelegramDesktop`, `SumatraPDF.SumatraPDF`
- `office`: `7zip.7zip`, `Google.Chrome`, `LibreOffice.LibreOffice`, `Adobe.Acrobat.Reader.64-bit`, `Zoom.Zoom`, `Telegram.TelegramDesktop`
- `dev`: `7zip.7zip`, `Git.Git`, `Microsoft.VisualStudioCode`, `Python.Python.3.12`, `Notepad++.Notepad++`

### 5.10. `deskkit/platform/protocols.py`

Протоколы (`typing.Protocol`), методы:

```python
class CommandRunner(Protocol):
    def run(self, args: Sequence[str], timeout_s: float) -> CommandResult: ...
    def terminate(self) -> None: ...

class RegistryGateway(Protocol):
    def list_values(self, hive: Hive, key: str) -> tuple[RegValue, ...]: ...
    def set_string(self, hive: Hive, key: str, name: str, data: str) -> None: ...
    def delete_value(self, hive: Hive, key: str, name: str) -> None: ...

class RecycleBinGateway(Protocol):
    def query(self) -> tuple[int, int]: ...          # (байты, число объектов)
    def empty(self) -> None: ...

class SoftwareGateway(Protocol):
    def list_installed(self) -> tuple[SoftwareEntry, ...]: ...

class SystemGateway(Protocol):
    def snapshot_base(self) -> SystemSnapshot: ...   # software может быть пустым, сервис допишет

class Clock(Protocol):
    def now(self) -> datetime: ...                   # aware, локальная зона

class AdminGateway(Protocol):
    def is_admin(self) -> bool: ...
    def relaunch_elevated(self, argv: Sequence[str]) -> ElevationResult: ...

class FileOps(Protocol):
    def walk_files(self, root: Path) -> tuple[FileEntry, ...]: ...
    def delete_file(self, path: Path) -> None: ...
    def remove_dir_if_empty(self, path: Path) -> bool: ...
    def create_zip(self, archive: Path, members: Sequence[ZipMember], manifest: Mapping[str, object]) -> None: ...
    def disk_free(self, path: Path) -> int: ...
    def replace(self, src: Path, dst: Path) -> None: ...
    def remove_file(self, path: Path) -> None: ...
```

Сервисы принимают узкие протоколы в конструкторе, не класс `WindowsPlatform`.

### 5.11. `deskkit/platform/commands.py`

Чистые функции, без `subprocess`.

```python
WINGET_TIMEOUT_S: float = 1800.0
TASK_NAME_PRIMARY = r"\DeskKit\Backup"
TASK_NAME_FALLBACK = "DeskKit Backup"
SCHTASKS_TR_LIMIT = 260

def winget_install_args(winget_exe: str, package_id: str, scope: InstallScope) -> list[str]: ...
def schtasks_create_args(task_name: str, tr: str, schedule: ScheduleSettings) -> list[str]: ...
def schtasks_query_args(task_name: str) -> list[str]: ...
def schtasks_delete_args(task_name: str) -> list[str]: ...
def quote_task_tr(cli_prefix: Sequence[str]) -> str: ...
def subprocess_kwargs() -> dict[str, int]: ...
```

`winget_install_args` возвращает список:

```text
{winget_exe} install --id {id} --exact --silent --accept-package-agreements --accept-source-agreements --disable-interactivity --no-upgrade --source winget
```

При `InstallScope.USER` в конец добавляется `--scope`, `user`. При `AUTO` этих двух аргументов нет. Других флагов нет. `--override` и `--custom` запрещены.

`quote_task_tr` — это `subprocess.list2cmdline(list(cli_prefix) + ["backup", "run", "--yes"])`. Если результат длиннее `SCHTASKS_TR_LIMIT`, бросает `ScheduleError("Команда задачи длиннее 260 символов.")`.

`schtasks_create_args` не добавляет `/RU`, `/RP`, `/RL HIGHEST`, `SYSTEM`. Состав:

- еженедельно: `schtasks /Create /TN {task_name} /TR {tr} /SC WEEKLY /D {weekday} /ST {time} /RL LIMITED /IT /F`
- ежедневно: `schtasks /Create /TN {task_name} /TR {tr} /SC DAILY /ST {time} /RL LIMITED /IT /F`

`weekday` и `time` берутся из `ScheduleSettings` как есть, после валидации профиля. Функция не проверяет расписание повторно.

`schtasks_query_args`: `schtasks /Query /TN {task_name} /XML`

`schtasks_delete_args`: `schtasks /Delete /TN {task_name} /F`

`subprocess_kwargs`: на Windows `{ "creationflags": 0x08000000 }` (`CREATE_NO_WINDOW`), иначе пустой словарь.

### 5.12. `deskkit/profile.py`

```python
class ProfileStore:
    def __init__(self, path: Path) -> None: ...
    def load(self) -> Profile: ...
    def save(self, profile: Profile) -> None: ...

def default_profile() -> Profile: ...
def profile_from_mapping(data: Mapping[str, object]) -> Profile: ...
def profile_to_mapping(profile: Profile) -> dict[str, object]: ...
```

`default_profile()`:

- `schema_version=1`
- `install.package_ids=()`, `scope=USER`
- `cleanup.targets` = user_temp, recycle_bin, chrome_cache, edge_cache, firefox_cache (без windows_temp)
- `backup.sources=()`, `destination=None`, `keep_last=5`
- `schedule`: enabled False, frequency `weekly`, weekday `MON`, time `09:00`
- `report.format="html"`, `last_directory=None`

`load`: если файла нет, вернуть `default_profile()` и не создавать файл. Если JSON битый — `ValidationError("Файл профиля повреждён.")`. Если это не объект — `ValidationError("Файл профиля повреждён.")`. Дальше `profile_from_mapping`.

`profile_from_mapping`:

- неизвестные ключи на любом уровне игнорировать;
- `schema_version` обязателен и равен 1, иначе `ProfileVersionError("Версия профиля не поддерживается.")`;
- отсутствующие ветки заменяются значениями из `default_profile()`;
- `package_ids` — список строк, каждый id проходит `Catalog().get`;
- `scope` — `user` или `auto`, иначе `ValidationError("Неизвестная область установки.")`;
- `targets` — список известных значений `CleanupTargetId`, иначе `ValidationError("Неизвестная цель очистки.")`;
- `sources` — список строк; на этапе загрузки существование папок не проверяется (профиль переносят на другой ПК);
- `destination` — строка или `null`;
- `keep_last` — целое 1..30, иначе `ValidationError("Хранить можно от 1 до 30 архивов.")`;
- `frequency` — `daily` или `weekly`, иначе `ValidationError("Неизвестная периодичность.")`;
- `weekday` — `MON TUE WED THU FRI SAT SUN`, иначе `ValidationError("Неизвестный день недели.")`;
- `time` совпадает с `^([01]\d|2[0-3]):[0-5]\d$`, иначе `ValidationError("Время задаётся как ЧЧ:ММ.")`;
- `format` — `html` или `xlsx`, иначе `ValidationError("Неизвестный формат отчёта.")`.

`save` пишет во временный файл в том же каталоге (`profile.json.tmp`), `flush`, `os.fsync`, затем `os.replace` на целевой путь. Каталог создаётся. При ошибке временный файл удаляется. Кодировка UTF-8, `ensure_ascii=False`, `indent=2`, перевод строки в конце.

Нормативный JSON (именно так выглядит `profile_summary_text` от профиля по умолчанию после подстановки одного источника и назначения; тест круглого пути сравнивает load(save(p)) == p, а не байты):

```json
{
  "schema_version": 1,
  "install": {
    "package_ids": ["7zip.7zip"],
    "scope": "user"
  },
  "cleanup": {
    "targets": ["user_temp", "recycle_bin", "chrome_cache", "edge_cache", "firefox_cache"]
  },
  "backup": {
    "sources": ["C:\\Users\\Stefan\\Documents"],
    "destination": "D:\\DeskKitBackups",
    "keep_last": 5,
    "schedule": {
      "enabled": false,
      "frequency": "weekly",
      "weekday": "MON",
      "time": "09:00"
    }
  },
  "report": {
    "format": "html",
    "last_directory": null
  }
}
```

Пути в JSON хранятся как их передал пользователь, без подстановки другого разделителя.

### 5.13. `deskkit/platform/process.py`

```python
class SubprocessRunner:
    def __init__(self) -> None: ...
    def run(self, args: Sequence[str], timeout_s: float) -> CommandResult: ...
    def terminate(self) -> None: ...
```

`run` вызывает `subprocess.Popen` со списком `args`, `stdout=PIPE`, `stderr=PIPE`, `text=True`, `encoding="utf-8"`, `errors="replace"`, и `**subprocess_kwargs()`. `shell` не передаётся. `communicate(timeout=timeout_s)`. При `TimeoutExpired` процесс убивается, вывод дочитывается, результат с `timed_out=True`, `exit_code=None`, `cancelled=False`. `terminate` убивает текущий процесс, если он ещё идёт; `run` тогда возвращает результат с `cancelled=True` и фактическим кодом. Блокировка `threading.Lock` защищает ссылку на `Popen`. После завершения ссылка обнуляется.

Этот класс тестируется на Linux настоящим спящим процессом `sys.executable`. Он не ходит в сеть.

### 5.14. `deskkit/platform/files.py`

`LocalFileOps` реализует `FileOps` через `pathlib`, `os`, `zipfile`, `shutil`.

`walk_files(root)`:

- если `root` не существует — пустой кортеж;
- `os.walk(root, followlinks=False)`;
- каталог-симлинк или reparse не обходится (`dirnames` фильтруются) и в результат не кладётся;
- файл-симлинк или reparse попадает в результат с `is_symlink`/`is_reparse` истинно, `size=0`, без чтения цели;
- обычный файл: размер и `modified_at` из `stat`. Время aware через `datetime.fromtimestamp(mtime, tz=datetime.now().astimezone().tzinfo)`;
- `OSError` и `PermissionError` на файле: запись с `unreadable=True`, `size=0`, `error=str(exc)`.

`delete_file` — `Path.unlink()`. Не ловит исключения.

`remove_dir_if_empty` — `Path.rmdir()`. True, если удалилось. False, если `OSError`.

`disk_free` — `shutil.disk_usage(path).free`. Если `path` не существует, вызывающий передаёт существующего родителя. Метод сам родителя не ищет.

`create_zip`:

- каждый `arcname` проходит `safe_arcname`;
- пишет в `archive.with_suffix(archive.suffix + ".partial")`, то есть `name.zip.partial`;
- `zipfile.ZipFile(..., mode="w", compression=ZIP_DEFLATED, compresslevel=6)`;
- файлы кладутся через `write(source, arcname)`;
- манифест — `writestr("deskkit-manifest.json", json.dumps(..., ensure_ascii=False, indent=2))`;
- закрытие архива, затем `os.replace` partial → `archive`;
- при любом исключении partial удаляется и исключение пробрасывается.

`replace` — `os.replace`. `remove_file` — `unlink(missing_ok=True)`.

### 5.15. `deskkit/platform/system_probe.py`

`PsutilSystemProbe.snapshot_base()` заполняет `SystemSnapshot` без программ (`software=()`).

- `hostname` — `platform.node()`
- `os_name`, `os_version`, `os_build` — на Windows из `platform.win32_ver()`: имя `Windows {release}` если release непустой, иначе `platform.system()`; версия — второй элемент `win32_ver`; сборка — третий. Вне Windows: `platform.system()`, `platform.release()`, `platform.version()`.
- `machine` — `platform.machine()`
- `cpu_model` — `platform.processor()` или, если строка пустая, `CPU`
- `cpu_physical` — `psutil.cpu_count(logical=False) or 0`
- `cpu_logical` — `psutil.cpu_count(logical=True) or 0`
- `cpu_freq_mhz` — `psutil.cpu_freq().current`, если вызов вернул объект, иначе None. Исключение `RuntimeError` → None.
- RAM — `psutil.virtual_memory().total` и `.available`
- диски — `psutil.disk_partitions(all=False)`. Для каждого `psutil.disk_usage(mountpoint)`. `PermissionError` и `OSError` → `DiskInfo` с нулями и `available=False`.
- `collected_at` — `datetime.now().astimezone()`

Модуль импортирует `psutil` на уровне модуля. Сервисы его не импортируют: им его передают как `SystemGateway`. Покрытие этот файл не включает.

### 5.16. `deskkit/platform/windows.py`

Класс `WindowsPlatform` собирает методы, которые `build_context` раскладывает по аргументам сервисов. Импорт модуля разрешён только при `sys.platform == "win32"`: наверху файла сразу после future-импорта

```python
import sys
if sys.platform != "win32":
    raise ImportError("deskkit.platform.windows is Windows-only")
```

Дальше обычные импорты `ctypes`, `winreg`, `os`, `shutil`.

Методы:

```python
class WindowsPlatform:
    def __init__(self, runner: CommandRunner) -> None: ...
    def is_admin(self) -> bool: ...
    def relaunch_elevated(self, argv: Sequence[str]) -> ElevationResult: ...
    def resolve_winget(self) -> str | None: ...
    def query_recycle_bin(self) -> tuple[int, int]: ...
    def empty_recycle_bin(self) -> None: ...
    def list_installed(self) -> tuple[SoftwareEntry, ...]: ...
    def list_values(self, hive: Hive, key: str) -> tuple[RegValue, ...]: ...
    def set_string(self, hive: Hive, key: str, name: str, data: str) -> None: ...
    def delete_value(self, hive: Hive, key: str, name: str) -> None: ...
    def open_folder(self, path: Path) -> None: ...
```

`is_admin`: `bool(ctypes.windll.shell32.IsUserAnAdmin())`.

`resolve_winget`: `shutil.which("winget")`. Если None и есть `LOCALAPPDATA`, проверить `Path(LOCALAPPDATA) / "Microsoft" / "WindowsApps" / "winget.exe"`. Вернуть строку пути или None.

`relaunch_elevated`: `ShellExecuteW(None, "runas", sys.executable, subprocess.list2cmdline(list(argv)), None, 1)`. Возврат ctypes больше 32 — `ElevationResult(True, "")`. Иначе `ElevationResult(False, "Повышение прав отменено.")`. После истинного результата вызывающий GUI уничтожает текущее окно. Новый процесс стартует с переданным argv. Состояние экранов не переносится.

Реестр. Доступ `KEY_READ` либо `KEY_SET_VALUE`, всегда вместе с `KEY_WOW64_64KEY` (`0x0100`). Ульи: `HKEY_CURRENT_USER`, `HKEY_LOCAL_MACHINE`. `list_values`: отсутствует ключ → пустой кортеж (это не ошибка). Тип `REG_SZ` → `RegKind.SZ`, `REG_EXPAND_SZ` → `EXPAND_SZ`, иное → `OTHER` и `data=""`. `set_string` создаёт ключ (`CreateKeyEx`) и пишет `REG_SZ`. `delete_value` использует `DeleteValue`. Исключения `OSError` пробрасываются.

Ключи, которые читает сервис автозагрузки (константы в `startup.py`, не здесь):

- Run пользователя: `Software\Microsoft\Windows\CurrentVersion\Run`
- Run общий: `Software\Microsoft\Windows\CurrentVersion\Run`
- запас выключенных HKCU: `Software\Stephanchik\DeskKit\DisabledStartup\HKCU`
- запас выключенных HKLM: `Software\Stephanchik\DeskKit\DisabledStartup\HKLM`

Ветку `WOW6432Node` для Run не читать и не писать.

Корзина:

```python
SHERB_NOCONFIRMATION = 0x00000001
SHERB_NOPROGRESSUI = 0x00000002
SHERB_NOSOUND = 0x00000004
```

`SHQUERYRBINFO` — структура с полями `cbSize` (`c_ulong`), `i64Size` (`c_longlong`), `i64NumItems` (`c_longlong`). `query` вызывает `shell32.SHQueryRecycleBinW(None, byref)`. Если код не 0 — бросает `DeskKitError("Не удалось прочитать корзину.")`. Иначе `(int(i64Size), int(i64NumItems))`.

`empty` вызывает `SHEmptyRecycleBinW(None, None, SHERB_NOCONFIRMATION | SHERB_NOPROGRESSUI | SHERB_NOSOUND)`. Ненулевой код, кроме `0x8000FFFF` при уже пустой корзине, — `DeskKitError("Не удалось очистить корзину.")`. Код `0x8000FFFF` (`E_UNEXPECTED` на пустой корзине у части сборок) считать успехом. Другие коды не глушить.

Установленные программы. Читать три ключа:

- `HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall`
- `HKLM\SOFTWARE\WOW6432Node\Microsoft\Windows\CurrentVersion\Uninstall`
- `HKCU\SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall`

Перечислить подключи. Из каждого взять `DisplayName`, `DisplayVersion`, `Publisher`, `InstallDate`. Без `DisplayName` пропустить. Если `SystemComponent` равен 1 — пропустить. Строки декодирует сам `winreg`. Собрать `SoftwareEntry`, где пустые поля становятся `""`. Дубликаты по паре `(name.casefold(), version)` выкинуть, оставить первую. Сортировать по `name.casefold()`.

`open_folder`: `os.startfile(str(path))` и проброс `OSError`.

### 5.17. `deskkit/services/install.py`

```python
ALREADY_INSTALLED_CODES: frozenset[int] = frozenset({-1978335135, -1978334963, -1978335189})
NO_APPLICABLE_INSTALLER: int = -1978335216
COMMAND_REQUIRES_ADMIN: int = -1978335207

class InstallService:
    def __init__(self, catalog: Catalog, runner: CommandRunner, winget_exe: str | None) -> None: ...
    def winget_path(self) -> str | None: ...
    def preview(self, package_ids: Sequence[str], scope: InstallScope) -> InstallPreview: ...
    def apply(
        self,
        package_ids: Sequence[str],
        scope: InstallScope,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> InstallReport: ...
```

`winget_path` возвращает строку, переданную в конструктор, или `None`. `preview` вызывает `catalog.require_ids`. Не запускает winget. `winget_found` ложно, если `winget_path()` вернул `None`.

`apply`:

1. `require_ids`. Пустой список — `ValidationError("Не выбрано ни одной программы.")`.
2. Если winget не найден — `WingetNotFoundError("Не найден winget. Установите «Установщик приложений» из Microsoft Store.")`.
3. Если `dry_run` — отчёт, у каждого элемента статус `SUCCESS`, сообщение `просмотр`, `exit_code=None`, `dry_run=True`. Команду не запускать.
4. Если не `confirmed` — `ConfirmationRequired("Нужно подтверждение.")`.
5. Иначе по порядку каталожного списка (порядок `package_ids`, как передал вызывающий, после проверки):
   - `cancel.raise_if_cancelled()`;
   - аргументы `winget_install_args`;
   - `runner.run(args, WINGET_TIMEOUT_S)`;
   - снова `raise_if_cancelled()` (убитый по отмене процесс не помечается как ошибка пакета);
   - если `timed_out` — статус FAILED, сообщение `превышено время ожидания (30 минут)`;
   - код 0 — SUCCESS, сообщение `установлено`;
   - код из `ALREADY_INSTALLED_CODES` — SKIPPED_INSTALLED, сообщение `уже установлен, пропуск`;
   - код `COMMAND_REQUIRES_ADMIN` — ADMIN_REQUIRED, сообщение `нужны права администратора`;
   - код `NO_APPLICABLE_INSTALLER` и scope был `USER` — один повтор той же функцией с `InstallScope.AUTO`. Повтор не повторяется. Если повтор тоже `NO_APPLICABLE_INSTALLER` — FAILED, сообщение `нет подходящего установщика`;
   - прочий ненулевой код — FAILED, сообщение `output_tail`;
   - журнал `deskkit.install`: INFO `установка {id}`, INFO `результат {id} {status.value}`. stdout целиком только на DEBUG.

Частичный успех не откатывается. `cancelled=True`, если вылетела `CancelledError` после нуля или больше завершённых элементов: пойманная отмена превращается в отчёт, а не летит наружу из `apply`. CLI смотрит `report.cancelled` и возвращает 4. Если при этом есть FAILED — всё равно 4 (отмена важнее), а уже записанные элементы остаются в отчёте.

Логгер получает модуль через `logging.getLogger("deskkit.install")`.

### 5.18. `deskkit/services/cleanup.py`

```python
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
    ) -> None: ...
    def preview(self, targets: Sequence[CleanupTargetId]) -> CleanupPreview: ...
    def apply(
        self,
        targets: Sequence[CleanupTargetId],
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> CleanupResult: ...
```

Пустой `targets` — `ValidationError("Не выбрана ни одна цель очистки.")`.

Как считаются корни цели:

- `user_temp` и `windows_temp`: один корень. Если каталога нет — `absent=True`.
- Chrome и Edge: если `User Data` нет — `absent=True`. Иначе каждый непосредственный подкаталог, чьё имя не в `SKIP_CHROME_EDGE_DIRS` и в котором есть хотя бы один из `BROWSER_CACHE_DIRS`, даёт эти существующие подкаталоги как корни. Файлы `Cookies`, `Login Data`, `History`, `Bookmarks`, `Preferences` лежат уровнем выше и в обход не попадают. Не добавлять другие имена папок.
- Firefox: если `Profiles` нет — `absent`. Иначе каждый непосредственный подкаталог, внутри которого есть каталог `cache2`, даёт этот `cache2` как корень. `cookies.sqlite` лежит рядом и не входит.

Обход корня через `files.walk_files`. В байты и число файлов входят только записи, где ложны `is_symlink`, `is_reparse`, `unreadable`. Для `user_temp` и `windows_temp` файл с `modified_at > clock.now() - TEMP_MIN_AGE` не входит в байты, а увеличивает `skipped_recent`. Для кэша возраст не смотрится. Ссылки увеличивают `skipped_links` и дают предупреждение `пропущена ссылка: {path}`. Нечитаемые увеличивают `unreadable` и предупреждение `нет доступа: {path}`.

Корзина: `recycle.query()`. При `DeskKitError` цель не absent, `warnings` содержит текст исключения, числа нулевые. При успехе `file_count=число объектов`, `byte_count=байты`, `roots=()`.

`apply` при `dry_run` возвращает результат с нулями удаления и `dry_run=True`, не вызывая `delete_file` и `empty`. При отсутствии подтверждения — `ConfirmationRequired`. Иначе для файловых целей удаляет только те файлы, которые preview включил бы в `byte_count` (та же фильтрация, повторный обход). `delete_file` при `PermissionError` или `OSError`: `skipped_locked += 1`, строка в `errors`, продолжать. После файлов пройти созданные пустые каталоги снизу вверх и вызвать `remove_dir_if_empty`. Сам корень цели не удалять никогда. Между файлами — `raise_if_cancelled`. Отмена превращается в результат с `cancelled=True`, уже удалённое не восстанавливается.

Корзина очищается вызовом `recycle.empty()` только если цель выбрана и просмотр не был сухим. Ошибка корзины попадает в `errors`, остальные цели всё равно обрабатываются.

Порядок целей — порядок аргумента `targets`.

`freed_bytes` — сумма размеров успешно удалившихся файлов. Размер корзины прибавляется к `freed_bytes`, если `empty()` не бросил исключение.

### 5.19. `deskkit/services/report.py`

```python
class ReportService:
    def __init__(self, system: SystemGateway, software: SoftwareGateway, clock: Clock) -> None: ...
    def collect(self) -> SystemSnapshot: ...
    def render_html(self, snapshot: SystemSnapshot) -> str: ...
    def write_html(self, snapshot: SystemSnapshot, path: Path) -> None: ...
    def write_xlsx(self, snapshot: SystemSnapshot, path: Path) -> None: ...
```

`collect` берёт `system.snapshot_base()`, подставляет `software.list_installed()` и, если `collected_at` нужно оставить от зонда, не перезаписывает его. Ошибка шлюза программ пробрасывается.

`render_html` возвращает один документ UTF-8 (строка Python), без внешних ссылок, без JavaScript. Каркас:

```html
<!DOCTYPE html>
<html lang="ru">
<head>
<meta charset="utf-8">
<title>Отчёт DeskKit</title>
<style>
body { font-family: Segoe UI, sans-serif; margin: 24px; color: #1a1a1a; }
h1 { font-size: 22px; }
h2 { font-size: 18px; margin-top: 28px; }
table { border-collapse: collapse; width: 100%; }
th, td { border: 1px solid #cccccc; padding: 6px 8px; text-align: left; vertical-align: top; }
th { background: #1f6aa5; color: #ffffff; }
</style>
</head>
<body>
<h1>Отчёт DeskKit</h1>
<p>Собран локально {collected_at:%Y-%m-%d %H:%M}. Никуда не отправляется.</p>
<h2>Система</h2>
...таблица ключ/значение...
<h2>Диски</h2>
...таблица...
<h2>Установленные программы</h2>
...таблица Имя, Версия, Издатель, Дата...
<p>DeskKit {version}. Отчёт описывает только этот компьютер.</p>
</body>
</html>
```

Каждое текстовое поле проходит `html.escape`. Заголовки разделов ровно `Система`, `Диски`, `Установленные программы`. В системе строки: Компьютер, Система, Сборка, Разрядность, Процессор, Память. Память и размеры дисков — через `format_bytes`. Пустой список программ — одна строка таблицы `Программы не найдены` на четыре колонки (`colspan` не обязателен: четыре ячейки, текст в первой, остальные пустые).

`write_html` создаёт родительский каталог и пишет UTF-8.

`write_xlsx` через openpyxl. Книга с тремя листами в таком порядке: `Система`, `Диски`, `Программы`.

- `Система`: колонки `Параметр`, `Значение`. Строки те же, что в HTML-таблице системы. Первая строка жирная, закреплена (`freeze_panes = "A2"`).
- `Диски`: `Диск`, `Том`, `Файловая система`, `Всего байт`, `Занято байт`, `Свободно байт`, `Всего`, `Свободно`. Последние две колонки — `format_bytes`. Недоступный диск — нули и слово `нет данных` в колонке `Всего`.
- `Программы`: `Имя`, `Версия`, `Издатель`, `Дата`.

Ширина колонок: 28 для первой, 36 для остальных. Заголовки жирные на каждом листе.

### 5.20. `deskkit/services/startup.py`

Константы ключей — строки из раздела 5.16.

```python
class StartupService:
    def __init__(
        self,
        registry: RegistryGateway,
        admin: AdminGateway,
        user_startup: Path,
        common_startup: Path,
    ) -> None: ...
    def list_entries(self) -> tuple[StartupEntry, ...]: ...
    def disable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry: ...
    def enable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry: ...
```

`list_entries` склеивает четыре источника в порядке: HKCU Run, HKLM Run, папка пользователя, общая папка.

Реестр: `list_values`. `RegKind.OTHER` пропускается молча (в журнал DEBUG `пропуск типа {name}`). Имя с `|` пропускается, DEBUG `пропуск имени`. `enabled` истинно, если имя есть в Run. Дополнительно читается запасной ключ: имена только оттуда попадают как `enabled=False` и `command=data`. Если одно имя есть и в Run, и в запасе, показывать одну запись `enabled=True` (боевой ключ важнее) и не дублировать. `needs_admin` истинно только для `HKLM_RUN`. `command` — данные значения. Для выключенной записи command — данные из запаса.

Папки: если каталога нет, источник пуст. Берутся только непосредственные файлы (не обход вглубь), имена которых оканчиваются на `.lnk` (включено) или `.lnk.deskkit-disabled` (выключено). Сравнение суффикса без учёта регистра. `desktop.ini` и прочие расширения игнорируются. `name` — имя файла. `command` — полный путь строкой. `needs_admin` истинно для общей папки. Имя с `|` пропускается.

`disable`:

1. Найти запись. Нет такой — `ValidationError("Запись автозагрузки не найдена.")`.
2. Уже выключена — `ValidationError("Запись уже выключена.")`.
3. `needs_admin` и не `admin.is_admin()` — `AdminRequiredError("Нужны права администратора.")`. Это происходит и в сухом прогоне: сухой прогон не маскирует отсутствие прав.
4. `dry_run` — вернуть ту же запись с `enabled=False`, ничего не писать.
5. Не `confirmed` — `ConfirmationRequired`.
6. Реестр: сначала `set_string` в запасной ключ того же улья, затем `delete_value` в Run. Если удаление бросило `OSError`, вызвать `delete_value` запасной копии и пробросить `DeskKitError("Не удалось выключить запись.")`. Порядок «сначала копия, потом удаление» обязателен. Удалять исходное значение до копии нельзя.
7. Ярлык: `Path.rename` на имя `исходное_имя + ".deskkit-disabled"` в той же папке. Если целевое имя занято — `DeskKitError("Не удалось выключить запись.")` и исходный файл не трогать повторно.

`enable` зеркален: копия должна отсутствовать в Run и присутствовать в запасе (или файл оканчивается на `.lnk.deskkit-disabled`). Сначала вернуть значение в Run (`set_string`), потом удалить запас. Если запись в Run не удалась, запас не удалять. Для ярлыка переименовать обратно, срезав суффикс `.deskkit-disabled`. Чужой файл без этого суффикса не переименовывать.

Методы не запускают командные строки из значений реестра и не открывают ярлыки.

### 5.21. `deskkit/services/backup.py`

```python
ARCHIVE_RE = re.compile(r"^DeskKit-backup-\d{8}-\d{6}\.zip$")

class BackupService:
    def __init__(self, files: FileOps, clock: Clock) -> None: ...
    def preview(self, sources: Sequence[Path], destination: Path, keep_last: int) -> BackupPreview: ...
    def apply(
        self,
        sources: Sequence[Path],
        destination: Path,
        keep_last: int,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> BackupResult: ...
```

Общие проверки `preview` и `apply` (обе бросают `ValidationError` или `PathNotAllowedError` с указанными текстами):

- пустые sources — `Не выбраны папки для копии.`;
- больше 20 источников — `Можно выбрать не больше 20 папок.`;
- `keep_last` вне 1..30 — `Хранить можно от 1 до 30 архивов.`;
- источник не абсолютный — `Нужен полный путь.`;
- источника нет на диске — `Папка не найдена: {path}`;
- `is_denied_source` — `Эту папку копировать нельзя: {path}`;
- `destination_conflicts` — `Папка назначения пересекается с копируемой.`;
- свободное место: если назначение существует, `disk_free(destination)`, иначе `disk_free` существующего предка. Если ни один предок не существует — `ValidationError("Не удалось проверить свободное место.")`. Если свободных байт меньше `byte_count` — `ValidationError("Недостаточно места для копии.")`. При `byte_count == 0` проверку места пропустить.

Имя архива: `DeskKit-backup-` + `clock.now().strftime("%Y%m%d-%H%M%S")` + `.zip`. Часы локальные, как их отдал `Clock`.

Обход такой же, как очистка, но возраст не фильтруется. Симлинки и reparse не входят в архив и попадают в `skipped` строкой `пропущена ссылка: {path}`. Нечитаемые — `нет доступа: {path}`. Обычные файлы входят.

`arcname`: `source-{index}/{relative posix}`, index с 1 в порядке аргумента `sources`. Относительный путь считается от корня источника через `relative_to`. Разделитель `/`. Каждый arcname проходит `safe_arcname`.

`rotate_names` в preview: в назначении (если оно есть) имена файлов, совпадающие с `ARCHIVE_RE`, сортировка по имени по убыванию, всё, что окажется за пределом `keep_last - 1` (место оставляется будущему архиву). Если назначения нет — пусто. Чужие файлы не входят. Каталоги не входят.

`apply` + `dry_run`: preview в результате, `archive_path=None`, файлов не создавать, каталог назначения не создавать.

`apply` без `confirmed`: `ConfirmationRequired` после проверок, до создания каталога.

`apply` боевой:

1. `destination.mkdir(parents=True, exist_ok=True)`;
2. между добавлением файлов в список членов проверять отмену (на этапе обхода);
3. манифест-словарь:

```python
{
  "app": "DeskKit",
  "version": __version__,
  "created_at": clock.now().isoformat(timespec="seconds"),
  "sources": [str(p) for p in sources],
  "files": [{"path": arcname, "bytes": size, "source_index": n}],
  "skipped": [{"path": str, "reason": str}],
}
```

4. `files.create_zip`;
5. ротация: удалить через `remove_file` только файлы из `rotate_names`, пересчитанные уже после появления нового архива (держать `keep_last` новейших по имени, включая новый). Шаблон тот же. Ошибка удаления старого архива добавляется в `skipped` как `не удалось удалить старый архив: {name}` и не откатывает новый.

Отмена до `create_zip` — `BackupResult` с `cancelled=True` и `archive_path=None`. Отмена во время `create_zip` не поддерживается: zip пишется одним вызовом после обхода. Обход обязан проверять токен.

### 5.22. `deskkit/services/schedule.py`

```python
class ScheduleService:
    def __init__(self, runner: CommandRunner, cli_prefix: Sequence[str]) -> None: ...
    def status(self) -> ScheduleStatus: ...
    def create_argv(self, schedule: ScheduleSettings) -> list[str]: ...
    def apply(self, schedule: ScheduleSettings, *, confirmed: bool) -> ScheduleStatus: ...
    def remove(self, *, confirmed: bool) -> None: ...
```

`create_argv` считает `tr = quote_task_tr(self._cli_prefix)` и возвращает `schtasks_create_args(TASK_NAME_PRIMARY, tr, schedule)`. Если `schedule.enabled` ложно, всё равно строит argv: вызывающий решает, создавать ли задачу. Метод не запускает процесс.

`status`: запросить XML первичного имени. Если `exit_code != 0`, запросить запасное имя. Если оба не 0 — `ScheduleStatus(exists=False, enabled=False, frequency=None, weekday=None, time=None, task_name=None, warning=None)`. Если stdout пуст — то же с `warning="Пустой ответ планировщика."`.

Разбор XML через `xml.etree.ElementTree`. Пространство имён `http://schemas.microsoft.com/windows/2004/02/mit/task`. Искать:

- `Settings/Enabled` — текст `true` (без учёта регистра) означает enabled;
- первый `Triggers/CalendarTrigger/StartBoundary` — время из `THH:MM`, то есть символы после `T`, первые пять `HH:MM`;
- наличие `ScheduleByDay` → frequency `daily`, weekday None;
- наличие `ScheduleByWeek` → frequency `weekly`. День из дочерних элементов `DaysOfWeek`: `Monday→MON`, `Tuesday→TUE`, `Wednesday→WED`, `Thursday→THU`, `Friday→FRI`, `Saturday→SAT`, `Sunday→SUN`. Несколько дней: берётся первый в порядке этого списка, `warning="В задаче несколько дней, профиль хранит один."`.

Ошибка разбора — `ScheduleError("Не удалось прочитать задачу планировщика.")`.

Нормативный XML еженедельной задачи, на котором тест проверяет разбор (объявить константой в тесте, не в продукте):

```xml
<?xml version="1.0" encoding="UTF-16"?>
<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">
  <Settings>
    <Enabled>true</Enabled>
  </Settings>
  <Triggers>
    <CalendarTrigger>
      <StartBoundary>2026-01-19T09:00:00</StartBoundary>
      <ScheduleByWeek>
        <DaysOfWeek>
          <Monday />
        </DaysOfWeek>
        <WeeksInterval>1</WeeksInterval>
      </ScheduleByWeek>
    </CalendarTrigger>
  </Triggers>
  <Actions>
    <Exec>
      <Command>C:\Program Files\DeskKit\DeskKit-cli\DeskKit-cli.exe</Command>
      <Arguments>backup run --yes</Arguments>
    </Exec>
  </Actions>
</Task>
```

Для ежедневного теста заменить узел `ScheduleByWeek` на `<ScheduleByDay><DaysInterval>1</DaysInterval></ScheduleByDay>`. Ожидание: frequency `daily`, weekday None, time `09:00`, enabled True.

`apply`: если не `confirmed` — `ConfirmationRequired` до запуска. Если `schedule.enabled` ложно — `ValidationError("В профиле расписание выключено.")` и процесс не запускать. Иначе выполнить argv первичного имени с таймаутом 60 секунд. Если код не 0, повторить с запасным именем в `/TN`. Если и оно не 0 — `ScheduleError("Не удалось создать задачу планировщика.")` плюс хвост вывода в сообщении. Успех → вернуть свежий `status()`.

`remove`: без подтверждения `ConfirmationRequired`. С подтверждением выполнить delete для обоих имён, таймаут 60 секунд. Ненулевые коды игнорировать: задачи могло не быть. Не бросать, если обеих нет.

Никакой argv, построенный этими функциями, не содержит подстрок `/RU` и `SYSTEM`.

### 5.23. `deskkit/app_context.py`

```python
@dataclass(frozen=True)
class Context:
    paths: AppPaths
    catalog: Catalog
    profile_store: ProfileStore
    installer: InstallService
    cleanup: CleanupService
    report: ReportService
    startup: StartupService
    backup: BackupService
    schedule: ScheduleService
    clock: Clock
    admin: AdminGateway
    runner: CommandRunner
    open_folder: Callable[[Path], None]
    version: str

def resolve_cli_argv() -> list[str]: ...
def build_context() -> Context: ...
```

`resolve_cli_argv`:

- если `getattr(sys, "frozen", False)` и рядом существует `Path(sys.executable).resolve().parent.parent / "DeskKit-cli" / "DeskKit-cli.exe"`, вернуть список из одного этого пути (окно установлено в `{app}\DeskKit\DeskKit.exe`, консоль в `{app}\DeskKit-cli\DeskKit-cli.exe`);
- если frozen и имя текущего exe `DeskKit-cli.exe` без учёта регистра — список из `sys.executable`;
- если frozen и оба варианта не сработали — `ScheduleError("Не найден DeskKit-cli.exe рядом с установкой.")`;
- если не frozen — `[sys.executable, "-m", "deskkit"]`.

`build_context`:

- если `sys.platform != "win32"`: бросить `UnsupportedOSError("DeskKit работает только в Windows.")`;
- собрать пути, `setup_logging` с `verbose=False` (CLI потом перенастроит);
- один `SubprocessRunner` кладётся и в `WindowsPlatform`, и в поле `Context.runner`, и в `InstallService`, и в `ScheduleService` (это один и тот же объект, чтобы кнопка «Остановить» убивала текущий winget);
- `PsutilSystemProbe()`, `LocalFileOps()`, `ProfileStore`, сервисы;
- `Clock` — вложенный класс с `now = datetime.now().astimezone`;
- `open_folder` — метод платформы.

Тесты `build_context` не вызывают.

### 5.24. `deskkit/__main__.py`, точки входа

```python
def dispatch(argv: list[str]) -> int: ...
def main() -> None: ...
```

`main` делает `raise SystemExit(dispatch(sys.argv[1:]))`.

`dispatch`:

- `argv == []` — импортировать `run_gui` и вызвать, вернуть 0;
- `argv == ["gui"]` — то же;
- `argv[0] == "gui"` и длина больше 1 — напечатать в stderr `команда gui не принимает аргументы`, вернуть 4, `run_gui` не импортировать;
- `argv[0] in {"-V", "--version"}` — напечатать `DeskKit 0.1.0`, вернуть 0;
- иначе `deskkit.cli.main.run(argv)`.

`entry_gui.main` только вызывает `run_gui`. `entry_cli.main` делает `raise SystemExit(run(sys.argv[1:]))`.

Импорт `deskkit.ui.app` стоит внутри ветки GUI, не на уровне модуля `__main__.py`.

### 5.25. `deskkit/cli/main.py`

```python
def build_parser() -> argparse.ArgumentParser: ...
def run(argv: list[str]) -> int: ...
```

Разбор:

```text
deskkit [--verbose] [--profile PATH] <команда> ...
```

`--verbose` / `-v` — store_true. `--profile` — необязательный путь, иначе путь из `profile_path_from_env(os.environ, Path.home())`.

Команды и аргументы:

| Команда | Аргументы |
| --- | --- |
| `install list` | нет |
| `install preview` | `--preset {home,office,dev}` либо повторяемый `--id`, необязательный `--scope {user,auto}` по умолчанию `user`, необязательный `--dry-run` |
| `install run` | те же, что у preview, плюс `--yes` |
| `clean preview` | повторяемый `--target` со значениями enum, необязательный `--dry-run` |
| `clean run` | те же, плюс `--yes` |
| `report show` | нет |
| `report save` | позиционный `path` |
| `startup list` | нет |
| `startup disable` | `--id` обязателен, `--yes`, `--dry-run` |
| `startup enable` | то же |
| `backup preview` | повторяемый `--source`, `--dest`, `--keep`, необязательный `--dry-run` |
| `backup run` | те же, плюс `--yes` |
| `backup schedule` | `--yes`, `--dry-run` |
| `backup unschedule` | `--yes`, `--dry-run` |
| `profile path` | нет |
| `profile show` | нет |
| `profile init` | нет |
| `profile export` | позиционный `path` |
| `profile import` | позиционный `path`, `--yes`, `--dry-run` |
| `profile apply-install` | `--yes`, `--dry-run` |

`--preset` и `--id` вместе: argparse не умеет это сам, поэтому `run` проверяет и пишет в stderr `Укажите набор или --id, не оба сразу.`, возвращает 2.

Если для install не переданы ни preset, ни id — `ValidationError`, код 1, текст `Не выбрано ни одной программы.`

`clean` без `--target` берёт цели из профиля.

`backup` без `--source` берёт источники, назначение и `keep_last` из профиля. Если `--source` передан, `--dest` обязателен, профиль не изменяется, `--keep` по умолчанию 5. `--source` без `--dest` — код 2, stderr `Вместе с --source нужен --dest.`

`report save`: суффикс `.html` или `.xlsx` без учёта регистра выбирает писатель. Иной суффикс — код 2, stderr `Нужен файл .html или .xlsx.`

`backup schedule` читает только профиль. `--dry-run` печатает `schedule_preview_text(create_argv(...))` и возвращает 0, процесс не запускается. Без `--yes` печатает тот же текст и футер, возвращает 3. С `--yes` вызывает `apply`. Если в профиле `enabled` ложно — код 1 и текст исключения `В профиле расписание выключено.`

`backup unschedule` в сухом прогоне печатает `Задача будет удалена, если она есть.` и возвращает 0. Без `--yes` — этот текст, футер, код 3.

`profile init`: если файл есть — код 1, stderr `Профиль уже есть.` Если нет — `save(default_profile())`, stdout путь, код 0.

`profile path` печатает путь. `profile show` печатает `profile_summary_text`.

`profile export`: если цель существует — код 1, stderr `Файл уже есть.` Иначе записать JSON. Каталог назначения создавать.

`profile import`: прочитать и разобрать через `profile_from_mapping`. Сухой прогон печатает summary и `Режим просмотра: профиль не заменён.`, код 0. Без `--yes` печатает summary и футер, код 3. С `--yes` — `save`.

`profile apply-install` берёт `install.package_ids` и `scope` и зовёт `InstallService.apply`.

Порядок мутирующей команды (`install run`, `clean run`, `startup disable`, `startup enable`, `backup run`, `backup schedule`, `backup unschedule`, `profile import`, `profile apply-install`):

1. Собрать аргументы и провалидировать их до записи.
2. Если передан `--dry-run`, вызвать сервис с `dry_run=True` (подтверждение не важно) и вернуть 0. Флаг `--yes` при этом ни на что не влияет.
3. Если `--yes` нет и это не сухой прогон, напечатать preview-текст с `include_footer=True` и вернуть 3. Сервисный `apply` не вызывать. Для `backup unschedule` печатать ровно `Задача будет удалена, если она есть.` и следом футер.
4. Если есть `--yes` и нет `--dry-run`, вызвать сервис с `dry_run=False, confirmed=True`.

Команды `install preview`, `clean preview`, `backup preview` сервисный `apply` не вызывают никогда. Они печатают preview-текст. С `--dry-run` футер не печатается (`include_footer=False`) и код 0. Без `--dry-run` футер печатается и код 3. У этих трёх команд аргумента `--yes` нет.

Общий перехват в `run`, если шаг 4 всё же бросил исключение:

- `ConfirmationRequired` → stderr `Нужно подтверждение.`, код 3 (в нормальном пути CLI сюда не попадает, потому что без `--yes` до `apply` не доходит);
- `CancelledError` → stderr `Остановлено.`, вернуть 4;
- `DeskKitError` → stderr `str(exc)`, вернуть 1;
- отчёт установки с любым `FAILED` или `ADMIN_REQUIRED` → код 1;
- отчёт с `cancelled` → код 4.

Перед командой вызвать `setup_logging(log_path, verbose=args.verbose)`.

Команда `install list` печатает по строке `{id}\t{name}\t{summary}\t{presets через запятую или "-"}`.

Вывод preview идёт в stdout. Ошибки в stderr.

На Linux `run` не вызывает `build_context`. Для тестов `run` принимает необязательный уже собранный `Context` через параметр `context: Context | None = None`. Если он передан, сервисы берутся из него, и проверка платформы пропускается. Боевой `__main__` вызывает `run(argv)` без context; тогда `run` зовёт `build_context()` и на Linux получает `UnsupportedOSError` с кодом 1. Так тесты не зависят от Windows, а случайный запуск на Linux объясняет причину.

Сигнатура, к которой должны прийти тесты:

```python
def run(argv: list[str], context: Context | None = None) -> int: ...
```

### 5.26. `deskkit/ui/strings.py`

Только константы. Экраны берут подписи отсюда.

```python
APP_TITLE = "DeskKit"
NAV: dict[str, str] = {
    "home": "Обзор",
    "install": "Установка",
    "cleanup": "Очистка",
    "report": "Отчёт",
    "startup": "Автозагрузка",
    "backup": "Копии",
    "profile": "Профиль",
    "logs": "Журнал",
}
BTN_PREVIEW = "Просмотреть"
BTN_EXECUTE = "Выполнить"
BTN_BACKUP_NOW = "Копировать сейчас"
BTN_CANCEL_ACTION = "Остановить"
BTN_CONFIRM = "Выполнить"
BTN_ABORT = "Отмена"
BTN_BROWSE = "Обзор…"
BTN_ADD_FOLDER = "Добавить папку"
BTN_REMOVE = "Убрать"
BTN_SAVE_SCHEDULE = "Сохранить расписание"
BTN_DELETE_SCHEDULE = "Удалить расписание"
BTN_COLLECT = "Собрать сведения"
BTN_SAVE_HTML = "Сохранить HTML"
BTN_SAVE_XLSX = "Сохранить Excel"
BTN_REFRESH = "Обновить"
BTN_OPEN_LOG_DIR = "Открыть папку журнала"
BTN_ELEVATE = "Запросить права администратора"
BTN_APPLY_INSTALL = "Применить установку из профиля"
BTN_PROFILE_INIT = "Создать по умолчанию"
BTN_PROFILE_IMPORT = "Загрузить из файла"
BTN_PROFILE_EXPORT = "Сохранить копию"
VIEW_ONLY = "Режим просмотра"
ADMIN_ON = "Администратор"
ADMIN_OFF = "Обычные права"
PRESETS: tuple[tuple[str, str], ...] = (
    ("home", "Дом"),
    ("office", "Офис"),
    ("dev", "Разработка"),
    ("custom", "Свой выбор"),
)
SCOPE_LABELS: tuple[tuple[str, str], ...] = (
    ("user", "Для текущего пользователя"),
    ("auto", "Как решит winget"),
)
FREQ_LABELS: tuple[tuple[str, str], ...] = (
    ("daily", "Ежедневно"),
    ("weekly", "Еженедельно"),
)
WEEKDAYS: tuple[tuple[str, str], ...] = (
    ("MON", "Понедельник"),
    ("TUE", "Вторник"),
    ("WED", "Среда"),
    ("THU", "Четверг"),
    ("FRI", "Пятница"),
    ("SAT", "Суббота"),
    ("SUN", "Воскресенье"),
)
CONFIRM_TITLE = "Подтверждение"
CONFIRM_LEAD = "Проверьте список. После подтверждения действие будет выполнено."
CLOSE_WHILE_BUSY = "Сейчас выполняется операция. Остановить и закрыть?"
BTN_CLOSE_ANYWAY = "Закрыть"
BTN_STAY = "Остаться"
SAFETY_LINES: tuple[str, ...] = (
    "Удаление, установка и автозагрузка начинаются только после подтверждения.",
    "Пароли, закладки и история браузера не входят в очистку.",
    "Файл настроек и журнал остаются на этом компьютере.",
)
PROFILE_HINT = "Применение профиля ставит только отмеченные программы. Очистка и копия сами не запускаются."
WINDOWS_TEMP_HINT = "Может потребовать права администратора. Файлы без доступа будут пропущены."
TEMP_AGE_HINT = "Файлы во временных папках моложе 24 часов не удаляются."
BACKUP_PLAIN_HINT = "Архив без пароля. Храните его на своём диске. Распаковка — вручную, мастера восстановления нет."
SCHEDULE_LOGIN_HINT = "Задача выполняется, когда вы вошли в систему. Пароль нигде не записывается."
ELEVATE_HINT = "Общий реестр и общая папка автозагрузки меняются только с правами администратора."
EMPTY_SELECTION = "Не выбрано ни одной программы."
```

### 5.27. `deskkit/ui/presenters.py`

Тонкий слой, который экраны вызывают. Он не импортирует CustomTkinter.

```python
def can_execute(view_only: bool) -> bool: ...

@dataclass(frozen=True)
class HomeStatus:
    winget_found: bool
    winget_path: str
    profile_exists: bool
    schedule_exists: bool
    schedule_enabled: bool
    is_admin: bool
    version: str
    last_log_line: str

class HomePresenter:
    def __init__(self, context: Context) -> None: ...
    def status(self) -> HomeStatus: ...

class InstallPresenter:
    def __init__(self, context: Context) -> None: ...
    def packages(self) -> tuple[Package, ...]: ...
    def preview(self, package_ids: Sequence[str], scope: InstallScope) -> InstallPreview: ...
    def execute(self, package_ids: Sequence[str], scope: InstallScope, *, dry_run: bool, confirmed: bool, cancel: CancellationToken) -> InstallReport: ...
    def confirmation(self, preview: InstallPreview) -> str: ...

class CleanupPresenter:
    def __init__(self, context: Context) -> None: ...
    def preview(self, targets: Sequence[CleanupTargetId]) -> CleanupPreview: ...
    def execute(self, targets: Sequence[CleanupTargetId], *, dry_run: bool, confirmed: bool, cancel: CancellationToken) -> CleanupResult: ...
    def confirmation(self, preview: CleanupPreview) -> str: ...

class ReportPresenter:
    def __init__(self, context: Context) -> None: ...
    def collect(self) -> SystemSnapshot: ...
    def summary(self, snapshot: SystemSnapshot) -> str: ...
    def save_html(self, snapshot: SystemSnapshot, path: Path) -> None: ...
    def save_xlsx(self, snapshot: SystemSnapshot, path: Path) -> None: ...

class StartupPresenter:
    def __init__(self, context: Context) -> None: ...
    def entries(self) -> tuple[StartupEntry, ...]: ...
    def confirmation(self, entry: StartupEntry, action: str) -> str: ...
    def disable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry: ...
    def enable(self, entry_id: str, *, dry_run: bool, confirmed: bool) -> StartupEntry: ...
    def elevate(self) -> ElevationResult: ...

class BackupPresenter:
    def __init__(self, context: Context) -> None: ...
    def preview(self, sources: Sequence[Path], destination: Path, keep_last: int) -> BackupPreview: ...
    def execute(self, sources: Sequence[Path], destination: Path, keep_last: int, *, dry_run: bool, confirmed: bool, cancel: CancellationToken) -> BackupResult: ...
    def confirmation(self, preview: BackupPreview) -> str: ...
    def schedule_status(self) -> ScheduleStatus: ...
    def schedule_text(self, settings: ScheduleSettings) -> str: ...
    def save_schedule(self, settings: ScheduleSettings, *, confirmed: bool) -> ScheduleStatus: ...
    def remove_schedule(self, *, confirmed: bool) -> None: ...

class ProfilePresenter:
    def __init__(self, context: Context) -> None: ...
    def path(self) -> Path: ...
    def load(self) -> Profile: ...
    def text(self) -> str: ...
    def init_default(self) -> Profile: ...
    def export_to(self, path: Path) -> None: ...
    def parse_file(self, path: Path) -> Profile: ...
    def import_from(self, path: Path, *, confirmed: bool) -> Profile: ...
    def apply_install(self, *, dry_run: bool, confirmed: bool, cancel: CancellationToken) -> InstallReport: ...

class LogsPresenter:
    def __init__(self, context: Context) -> None: ...
    def text(self) -> str: ...
    def directory(self) -> Path: ...
```

`can_execute` возвращает `not view_only`.

`HomePresenter.status` берёт путь winget из `context.installer.winget_path()`. Пустая строка и `None` означают `winget_found=False`, а `winget_path` в `HomeStatus` тогда равен `""`. `profile_exists` — `paths.profile_path.is_file()`. Расписание — `schedule.status()`. `last_log_line` — последняя непустая строка `read_log_tail`, либо `Журнал пока пуст.`

`confirmation` у установки — `CONFIRM_LEAD + "\n\n" + install_preview_text(..., include_footer=False)`. У очистки и копии так же со своими preview-текстами. У автозагрузки — `CONFIRM_LEAD + "\n\n" + startup_action_text(...)`.

`BackupPresenter.schedule_text` — `schedule_preview_text(context.schedule.create_argv(settings))`.

`save_schedule` при `settings.enabled` ложно вызывает `remove(confirmed=confirmed)` и возвращает `status()`. При истинно — `apply`. Экран перед этим сохраняет профиль (раздел 6), чтобы задача и JSON не разъехались.

`ProfilePresenter.init_default` повторяет правило CLI: если файл есть, `ValidationError("Профиль уже есть.")`.

`parse_file` читает JSON и возвращает `profile_from_mapping`, ничего не записывая. `import_from` при `confirmed=False` бросает `ConfirmationRequired` и не пишет файл. При `confirmed=True` сохраняет разобранный профиль поверх текущего и возвращает его. Сухой прогон в GUI для импорта не нужен: диалог и есть подтверждение. Экран сначала вызывает `parse_file`, показывает текст и только после согласия вызывает `import_from(..., confirmed=True)`.

`elevate` вызывает `context.admin.relaunch_elevated([])`, то есть новый процесс без аргументов CLI, он откроет GUI.

### 5.28. Остальные UI-файлы

Поведение экранов — раздел 6. Здесь только границы модулей.

- `ui/theme.py`: функция `apply_theme() -> None` вызывает `set_appearance_mode("system")` и `set_default_color_theme("blue")`. Больше ничего.
- `ui/widgets.py`: `confirm(parent, title: str, body: str) -> bool`, `TaskRunner`, `set_readonly(textbox) -> None`.
- `ui/app.py`: `run_gui(context: Context | None = None) -> None`.
- `ui/screens/*.py`: класс экрана с конструктором `(parent, presenter, host)`, метод `refresh() -> None`. Имена классов: `HomeScreen`, `InstallScreen`, `CleanupScreen`, `ReportScreen`, `StartupScreen`, `BackupScreen`, `ProfileScreen`, `LogsScreen`.

`host` — небольшой протокол в `ui/app.py`:

```python
class ScreenHost(Protocol):
    def show(self, screen_id: str) -> None: ...
    def view_only(self) -> bool: ...
    def run_task(self, fn: Callable[[], object], on_ok: Callable[[object], None], on_err: Callable[[BaseException], None]) -> None: ...
    def set_busy(self, busy: bool) -> None: ...
    def notify(self, text: str) -> None: ...
    def ask(self, title: str, body: str) -> bool: ...
    def pick_directory(self) -> str | None: ...
    def pick_save(self, suffix: str, initial: str) -> str | None: ...
    def pick_open(self) -> str | None: ...
    def open_folder(self, path: Path) -> None: ...
    def request_elevation(self) -> None: ...
```

Экраны не импортируют `filedialog` и не вызывают сервисы мимо презентера.

---

## 6. Экраны GUI

Одно окно `customtkinter.CTk`. Заголовок `DeskKit`. Иконка — `deskkit/assets/icon.ico`, через `iconbitmap`, ошибку отсутствующей иконки не прятать на Windows; в тестах этот код не выполняется.

Сетка корня: колонка 0 шириной 220 (`weight=0`), колонка 1 `weight=1`. Строка 0 `weight=1` — содержимое. Строка 1 высотой 40 — статус.

Боковая панель, `CTkFrame`:

- подпись `DeskKit`, шрифт `("Segoe UI", 20)`;
- подпись версии `0.1.0`, шрифт 12;
- восемь `CTkButton` в порядке словаря `NAV`: Обзор, Установка, Очистка, Отчёт, Автозагрузка, Копии, Профиль, Журнал. `anchor="w"`, высота 36, отступы 12 по горизонтали и 4 по вертикали. Выбранная кнопка красится `fg_color="#1f6aa5"`. Остальные остаются в цвете темы.

Статусная строка:

- слева `Администратор` или `Обычные права` по `admin.is_admin()` на момент старта (после повышения прав процесс уже новый);
- по центру `CTkSwitch` с текстом `Режим просмотра`, по умолчанию выключен;
- справа короткая подсказка последнего действия, её пишет `host.notify`, начальный текст пустой.

Экраны создаются один раз и укладываются в одну клетку `grid`. Переключение — `tkraise()`. Состояние галочек при переходе по разделам сохраняется.

`TaskRunner` (в `widgets.py`): одна очередь, один рабочий поток `daemon=True`. Пока задача идёт, второй `run_task` вызывает `host.notify("Дождитесь окончания операции.")` и не стартует поток. Опрос `after(100, ...)`. Успех и исключение возвращаются в главный поток колбэками. `set_busy(True)` на старте и `False` в колбэке.

Кнопка «Остановить» вызывает `token.cancel()` и `context` не обязан убивать процесс сам: `InstallPresenter.execute` получает токен, а `app.py` дополнительно вызывает `terminate` у раннера. Для этого `Context` дополняется полем `runner: CommandRunner`. Очистка и архив проверяют только токен. Текущий файл zip не обрывается посередине `create_zip`.

Закрытие окна (`WM_DELETE_WINDOW`): если занято, `confirm` с текстом `CLOSE_WHILE_BUSY`, кнопки `Закрыть` и `Остаться`. «Закрыть» отменяет токен, вызывает `runner.terminate()` и уничтожает окно. «Остаться» ничего не делает. Если не занято — сразу `destroy`.

Диалог `confirm`:

- `CTkToplevel`, заголовок из аргумента, `transient` и `grab_set` относительно родителя;
- тело — `CTkTextbox` в состоянии только для чтения: чтобы вставить текст, переключить `state="normal"`, вставить, вернуть `state="disabled"`;
- кнопки справа снизу: `Отмена` (фокус по умолчанию) и `Выполнить`;
- `Return` и `Escape` связаны с отменой, не с выполнением;
- крестик топового окна — отказ;
- функция возвращает `True` только от кнопки `Выполнить`.

Кнопки «Выполнить» на экранах при `view_only()` не вызывают диалог: они `state="disabled"`, а `host.notify` получает `Включён режим просмотра.` Кнопка «Просмотреть» при этом работает.

Общий вид экрана действия: заголовок раздела шрифтом 20, пояснение шрифтом 13 серым цветом `("gray30", "gray70")`, рабочая область, `CTkTextbox` высотой 160 для результата, `CTkProgressBar` в режиме `indeterminate` (методы `start` и `stop`), ряд кнопок. Прогресс крутится только пока `busy`.

Тексты результатов на экранах — функции `text.py`, чтобы окно и CLI говорили одно и то же.

### 6.1. Обзор (`HomeScreen`)

Заголовок `Обзор`. Подзаголовок `Настройка и обслуживание этого компьютера`.

Четыре карточки `CTkFrame` сеткой 2×2:

1. `Программы`. Текст `winget: найден` и путём на следующей строке, либо `winget: не найден`. Кнопка `К установке` вызывает `host.show("install")`.
2. `Профиль`. `Файл настроек найден` либо `Файл настроек ещё не создан`. Кнопка `К профилю`.
3. `Копии`. `Расписание включено` либо `Расписание выключено` по `schedule_exists and schedule_enabled`. Кнопка `К копиям`.
4. `Права`. Строка статуса администратора и фраза `Для обычной работы права администратора не нужны.`

Под карточками три строки `SAFETY_LINES`. Внизу подпись `Стефан Митрохин · GitHub Stephanchik · MIT · версия 0.1.0`.

`refresh` перечитывает `HomePresenter.status`.

### 6.2. Установка (`InstallScreen`)

`CTkSegmentedButton` со значениями `Дом`, `Офис`, `Разработка`, `Свой выбор`. Выбрано `Свой выбор`. Нажатие набора выставляет галочки ровно по `Catalog.ids_for_preset`. `Свой выбор` галочки не меняет. Ручное переключение галочки не двигает сегмент обратно: в установку идут галочки, не имя набора.

`CTkOptionMenu` области: `Для текущего пользователя` (значение `user`, оно выбрано) и `Как решит winget` (`auto`).

`CTkScrollableFrame` с 15 `CTkCheckBox`. Текст `{name} — {summary}`. По умолчанию все сняты.

Пояснение под списком: `Сначала установка идёт для текущего пользователя. Если такой сборки нет, DeskKit повторит её без указания области, и Windows может запросить права.`

Кнопки `Просмотреть`, `Выполнить`, `Остановить`. Просмотр пишет `install_preview_text` в текстовое поле и не открывает диалог. Выполнить (если есть галочки и режим просмотра выключен) считает preview, открывает `confirm` с `presenter.confirmation`. Да — `execute(..., dry_run=False, confirmed=True)`. Нет — `host.notify("Действие отменено.")`. Пустые галочки — `notify(EMPTY_SELECTION)` без диалога.

По ходу задачи текстовое поле заменяется итогом `install_report_text`. Если в отчёте есть `ADMIN_REQUIRED`, под итогом показывается кнопка `Запросить права администратора`. Она вызывает `host.request_elevation()`.

### 6.3. Очистка (`CleanupScreen`)

Шесть `CTkCheckBox` с подписями `cleanup_target_label`. Начальное состояние — цели из загруженного профиля. Рядом с временными целями серым текст `TEMP_AGE_HINT`. Рядом с Windows Temp — `WINDOWS_TEMP_HINT`.

Просмотр и выполнение как у установки, тексты очистки. Выполнение не сохраняет галочки в профиль само: профиль меняется только на экране профиля и при сохранении расписания. Галочки очистки, выставленные здесь, действуют на этот запуск. Чтобы они попали в JSON, пользователь правит профиль. Это записано в пояснении: `Этот запуск не переписывает файл настроек.`

Кнопка повышения прав на этом экране есть всегда, не только при ошибке: `Запросить права администратора`, пояснение `WINDOWS_TEMP_HINT`. Отказ UAC оставляет окно открытым и пишет `Повышение прав отменено.`

### 6.4. Отчёт (`ReportScreen`)

Кнопка `Собрать сведения` запускает `collect` в задаче и кладёт в текстовое поле `report_summary_text`. Кнопки сохранения неактивны, пока сбора не было.

`Сохранить HTML` открывает диалог сохранения с начальным именем `DeskKit-report-{yyyyMMdd-HHmmss}.html`. `Сохранить Excel` — то же с `.xlsx`. После записи `notify(f"Сохранено: {path}")`. Отмена диалога ничего не пишет. Каталог запоминать в профиле не нужно в v1: `ReportSettings.last_directory` остаётся в JSON для будущего, экран его не заполняет.

### 6.5. Автозагрузка (`StartupScreen`)

Сверху, если не администратор, строка `ELEVATE_HINT` и кнопка `Запросить права администратора`.

Дальше `CTkScrollableFrame` строк. Строка: имя, бейдж `Вкл` или `Выкл`, подпись источника, команда, обрезанная до 80 символов с `…` если длиннее, кнопка `Выключить` или `Включить`.

Кнопка строки с `needs_admin` и без прав администратора имеет `state="disabled"`. Подсказка в `notify` при попытке не нужна: кнопки просто нет активной.

Нажатие активной кнопки открывает подтверждение с `startup_action_text`. После согласия вызывает `disable` или `enable` с `confirmed=True`, `dry_run=False`, затем `refresh`. В режиме просмотра кнопки строк выключены.

Пустой список — подпись `Автозагрузка пуста.`

Ошибки `AdminRequiredError` и `DeskKitError` показываются через `notify`, список не ломается.

### 6.6. Копии (`BackupScreen`)

Список выбранных папок (метки в `CTkScrollableFrame`), кнопки `Добавить папку` и `Убрать`. Добавление — `pick_directory`. Повтор той же папки не добавляется, `notify("Папка уже в списке.")`. Пустой выбор диалога игнорируется.

Поле назначения: `CTkEntry` и `Обзор…`.

Поле `Хранить последних архивов (1–30)` — `CTkEntry` шириной 80, начальное значение из профиля.

Блок расписания: `CTkSwitch` `По расписанию`; меню `Ежедневно` / `Еженедельно`; меню дня недели, которое `grid_remove`, когда выбрано ежедневно, и возвращается для еженедельного; поле времени с начальным `09:00`. Серым `SCHEDULE_LOGIN_HINT` и `BACKUP_PLAIN_HINT`.

Кнопки: `Просмотреть`, `Копировать сейчас` (`BTN_BACKUP_NOW`), `Сохранить расписание`, `Удалить расписание`.

`Сохранить расписание` сначала проверяет поля так же, как preview (презентация вызывает `preview`, ошибка уходит в notify), затем пишет профиль: в текущий профиль подставляются источники, назначение, keep, блок schedule, `ProfileStore.save`, и только потом `save_schedule`. Подтверждение одно — диалог с `schedule_preview_text`, если расписание включается. Если выключатель расписания снят, диалог спрашивает текстом `Задача будет удалена, если она есть.` и вызывается `remove`. Профиль всё равно сохраняется.

`Удалить расписание` не меняет список папок. Оно подтверждает удаление задачи и вызывает `remove`, затем в профиле ставит `schedule.enabled=False` и сохраняет профиль.

Статус задачи на экране: если `status.warning` не пусто, показать его жёлтым не получится штатно — показать обычным `notify` и строкой под кнопками.

Начальные значения полей заполняет `refresh` из профиля.

### 6.7. Профиль (`ProfileScreen`)

`CTkEntry` только для чтения с путём профиля. Текстовое поле с `profile_summary_text`. Кнопки `Создать по умолчанию`, `Загрузить из файла`, `Сохранить копию`, `Применить установку из профиля`.

Пояснение — `PROFILE_HINT`.

`Создать по умолчанию` зовёт `init_default`. Если профиль уже есть, notify получает текст ошибки, файл не перезаписывается.

`Загрузить из файла` — `pick_open`. Затем прочитать текст для диалога через разбор (презентация: сначала `profile_from_mapping` без записи — вынести это в метод `parse_file(path) -> Profile`, а `import_from(path, confirmed=True)` пишет). Диалог показывает `profile_summary_text` разобранного профиля. Согласие сохраняет поверх текущего файла.

`Сохранить копию` — `pick_save` с суффиксом `.json` и именем `deskkit-profile.json`. Если пользователь выбрал существующий файл, диалог сохранения ОС сам спрашивает о замене; если путь вернулся, `export_to` перезаписывает. Если `export_to` получил существующий путь, он перезаписывает: это осознанное отличие от CLI, потому что диалог ОС уже спросил. Записать это в докстринге `export_to`.

`Применить установку` идёт тем же подтверждением, что экран установки, и вызывает `apply_install`. Очистку и копию не запускает.

### 6.8. Журнал (`LogsScreen`)

Текстовое поле на всю ширину с `LogsPresenter.text`. Кнопки `Обновить` и `Открыть папку журнала`. Вторая вызывает `host.open_folder(presenter.directory())`. Ошибка открытия попадает в notify.

`refresh` при каждом показе экрана перечитывает файл.

---

## 7. Командная строка

Запуск из исходников: `python -m deskkit ...`. После установки пользователь вызывает консольный exe. Ярлык меню Пуск запускает оконный exe без аргументов.

Примеры ниже используют консольный exe. Код выхода подписан в конце комментарием.

```text
"C:\Program Files\DeskKit\DeskKit-cli.exe" --version
DeskKit 0.1.0
:: 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" install list
7zip.7zip	7-Zip	Архиватор	home,office,dev
:: 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" install preview --preset home
:: stdout — install_preview_text с футером, код 3

"C:\Program Files\DeskKit\DeskKit-cli.exe" install preview --preset home --dry-run
:: тот же текст плюс поведение dry-run у preview: preview не запускает winget в любом случае.
:: Для preview флаг --dry-run не обязателен. Код preview без --yes равен 3, с --dry-run равен 0.
:: С --yes команда preview не существует: у preview нет --yes.

"C:\Program Files\DeskKit\DeskKit-cli.exe" install run --id 7zip.7zip --id VideoLAN.VLC --scope user --yes
:: код 0, если оба успеха или пропуск; код 1, если хоть один FAILED или ADMIN_REQUIRED

"C:\Program Files\DeskKit\DeskKit-cli.exe" install run --preset office --dry-run
:: код 0, winget install не вызывается

"C:\Program Files\DeskKit\DeskKit-cli.exe" install run --preset home --id 7zip.7zip
:: stderr: Укажите набор или --id, не оба сразу.
:: код 2

"C:\Program Files\DeskKit\DeskKit-cli.exe" clean preview
:: цели из профиля, текст cleanup_preview_text, код 3

"C:\Program Files\DeskKit\DeskKit-cli.exe" clean run --target user_temp --target chrome_cache --yes
:: код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" clean run --target user_temp --dry-run --yes
:: побеждает dry-run, код 0, файлы на месте

"C:\Program Files\DeskKit\DeskKit-cli.exe" report show
:: report_summary_text, код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" report save C:\Users\Stefan\Desktop\otchet.html
:: создаёт файл, stdout: Сохранено: C:\Users\Stefan\Desktop\otchet.html
:: код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" report save C:\Users\Stefan\Desktop\otchet.xlsx
:: код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" report save C:\Users\Stefan\Desktop\otchet.txt
:: stderr: Нужен файл .html или .xlsx.
:: код 2

"C:\Program Files\DeskKit\DeskKit-cli.exe" startup list
:: startup_list_text, код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" startup disable --id hkcu_run|OneDrive
:: stdout: startup_action_text и футер, код 3, реестр не менялся

"C:\Program Files\DeskKit\DeskKit-cli.exe" startup disable --id hkcu_run|OneDrive --yes
:: код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" startup enable --id user_startup|Slack.lnk.deskkit-disabled --yes
:: код 0; идентификатор выключенного ярлыка содержит суффикс, потому что name — имя файла

"C:\Program Files\DeskKit\DeskKit-cli.exe" backup preview --source C:\Users\Stefan\Documents --dest D:\DeskKitBackups
:: код 3

"C:\Program Files\DeskKit\DeskKit-cli.exe" backup run --source C:\Users\Stefan\Documents --dest D:\DeskKitBackups --keep 5 --yes
:: код 0, профиль не изменён

"C:\Program Files\DeskKit\DeskKit-cli.exe" backup run --yes
:: берёт папки из профиля; если их нет — код 1, stderr: Не выбраны папки для копии.

"C:\Program Files\DeskKit\DeskKit-cli.exe" backup schedule --dry-run
:: печатает команду schtasks, код 0, задачи нет

"C:\Program Files\DeskKit\DeskKit-cli.exe" backup schedule --yes
:: создаёт задачу по блоку schedule профиля, код 0 только если enabled истинно

"C:\Program Files\DeskKit\DeskKit-cli.exe" backup unschedule --yes
:: удаляет оба возможных имени, код 0

"C:\Program Files\DeskKit\DeskKit-cli.exe" profile path
"C:\Program Files\DeskKit\DeskKit-cli.exe" profile init
"C:\Program Files\DeskKit\DeskKit-cli.exe" profile show
"C:\Program Files\DeskKit\DeskKit-cli.exe" profile export C:\Users\Stefan\Desktop\deskkit-profile.json
"C:\Program Files\DeskKit\DeskKit-cli.exe" profile import C:\Users\Stefan\Desktop\deskkit-profile.json --yes
"C:\Program Files\DeskKit\DeskKit-cli.exe" profile apply-install --yes

"C:\Program Files\DeskKit\DeskKit-cli.exe" gui
:: открывает окно; в автоматических тестах не вызывать

"C:\Program Files\DeskKit\DeskKit-cli.exe" gui --verbose
:: stderr: команда gui не принимает аргументы
:: код 4
```

Двойной щелчок по `DeskKit.exe` равен `dispatch([])`.

---

## 8. Установщик, сборка и релиз

### 8.1. Иконка

`installer/make_icon.py` рисует знак и пишет два файла. Запускать один раз из корня репозитория:

```text
python installer/make_icon.py
```

Скрипт:

- ищет шрифт по порядку: `C:\Windows\Fonts\arialbd.ttf`, `C:\Windows\Fonts\segoeuib.ttf`, `/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf`, `/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf`;
- если ни одного нет — `SystemExit(1)` и в stderr список путей;
- рисует RGBA 256×256, прозрачный фон, скруглённый прямоугольник отступа `size // 8`, радиус `size // 6`, заливка `#1F6AA5`;
- по центру белые буквы `DK`, кегль `int(size * 0.38)`;
- сохраняет `deskkit/assets/icon.png` 256×256;
- сохраняет `deskkit/assets/icon.ico` с размерами 16, 32, 48, 64, 256.

Оба файла коммитятся. Релиз их не перерисовывает, чтобы сборка не зависела от шрифта на раннере.

### 8.2. Version resource

`installer/version_info.txt` — текст для PyInstaller, общий для обоих exe. `OriginalFilename` оставлен `DeskKit.exe` и у консольной сборки, чтобы не завести второй файл версии.

```text
VSVersionInfo(
  ffi=FixedFileInfo(
    filevers=(0, 1, 0, 0),
    prodvers=(0, 1, 0, 0),
    mask=0x3F,
    flags=0x0,
    OS=0x40004,
    fileType=0x1,
    subtype=0x0,
    date=(0, 0)
  ),
  kids=[
    StringFileInfo([
      StringTable(
        "040904B0",
        [
          StringStruct("CompanyName", "Stefan Mitrokhin"),
          StringStruct("FileDescription", "DeskKit"),
          StringStruct("FileVersion", "0.1.0"),
          StringStruct("InternalName", "DeskKit"),
          StringStruct("LegalCopyright", "Copyright (c) 2026 Stephanchik"),
          StringStruct("OriginalFilename", "DeskKit.exe"),
          StringStruct("ProductName", "DeskKit"),
          StringStruct("ProductVersion", "0.1.0"),
        ],
      )
    ]),
    VarFileInfo([VarStruct("Translation", [1033, 1200])])
  ]
)
```

В интерфейсе автор пишется как `Стефан Митрохин`. В ресурсе файла — латинская транслитерация, чтобы старые средства просмотра версии не портили строку.

### 8.3. Спеки PyInstaller

Оба спека лежат в `installer/`. `SPECPATH` указывает на этот каталог, корень репозитория — `Path(SPECPATH).resolve().parent`.

Общее:

- `upx=False`;
- `uac_admin=False` и `uac_uiaccess=False` (программа не требует повышения прав при старте; установщик — требует, это другое);
- `collect_data_files("customtkinter")` плюс оба файла из `deskkit/assets` в каталог сборки `deskkit/assets`;
- `hiddenimports = collect_submodules("customtkinter") + ["openpyxl", "psutil"]`;
- `excludes=["pytest", "ruff", "PIL"]`;
- `pathex` включает корень репозитория;
- onedir (`exclude_binaries=True` у `EXE` и отдельный `COLLECT`), не onefile.

`installer/deskkit-gui.spec`: скрипт `deskkit/entry_gui.py`, `name="DeskKit"`, `console=False`, иконка `deskkit/assets/icon.ico`, `version` указывает на `installer/version_info.txt`. `COLLECT` с `name="DeskKit"`.

`installer/deskkit-cli.spec`: скрипт `deskkit/entry_cli.py`, `name="DeskKit-cli"`, `console=True`, та же иконка и version. `COLLECT` с `name="DeskKit-cli"`.

Команды сборки из корня, именно в этом порядке, без `--clean` (второй прогон не должен стирать первый каталог):

```text
pyinstaller installer/deskkit-gui.spec --noconfirm --distpath dist --workpath build/gui
pyinstaller installer/deskkit-cli.spec --noconfirm --distpath dist --workpath build/cli
```

Ожидаемые файлы:

```text
dist/DeskKit/DeskKit.exe
dist/DeskKit-cli/DeskKit-cli.exe
```

### 8.4. Inno Setup

Файл `installer/installer.iss` целиком:

```iss
#define MyAppName "DeskKit"
#define MyAppVersion "0.1.0"
#define MyAppPublisher "Стефан Митрохин"
#define MyAppURL "https://github.com/Stephanchik/windows-automation-utility"
#define MyAppExeName "DeskKit.exe"
#define MyAppId "{{8F3C1A2E-6B47-4D91-9C5E-2A7F0B4D8E16}"

[Setup]
AppId={#MyAppId}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\DeskKit
DefaultGroupName=DeskKit
DisableProgramGroupPage=yes
LicenseFile=..\LICENSE
OutputDir=..\dist
OutputBaseFilename=DeskKit-Setup-{#MyAppVersion}
SetupIconFile=..\deskkit\assets\icon.ico
UninstallDisplayIcon={app}\DeskKit\{#MyAppExeName}
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=admin
MinVersion=10.0
VersionInfoVersion=0.1.0.0
VersionInfoCompany=Stefan Mitrokhin
VersionInfoDescription=DeskKit setup
VersionInfoProductName=DeskKit
CloseApplications=yes
UsedUserAreasWarning=no

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "Ярлык на рабочем столе"; GroupDescription: "Ярлыки:"; Flags: checkedonce

[Files]
Source: "..\dist\DeskKit\*"; DestDir: "{app}\DeskKit"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\dist\DeskKit-cli\*"; DestDir: "{app}\DeskKit-cli"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\DeskKit"; Filename: "{app}\DeskKit\{#MyAppExeName}"
Name: "{group}\Удалить DeskKit"; Filename: "{uninstallexe}"
Name: "{autodesktop}\DeskKit"; Filename: "{app}\DeskKit\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\DeskKit\{#MyAppExeName}"; Description: "Запустить DeskKit"; Flags: nowait postinstall skipifsilent

[UninstallRun]
Filename: "{cmd}"; Parameters: "/C schtasks /Delete /TN ""\DeskKit\Backup"" /F & exit /B 0"; Flags: runhidden
Filename: "{cmd}"; Parameters: "/C schtasks /Delete /TN ""DeskKit Backup"" /F & exit /B 0"; Flags: runhidden
```

`#define MyAppId` начинается с удвоенной скобки, потому что Inno съедает одну `{` как начало константы. В готовом скрипте после препроцессора AppId равен `{8F3C1A2E-6B47-4D91-9C5E-2A7F0B4D8E16}`.

Установщик просит права администратора, чтобы писать в `Program Files` и общее меню Пуск. Манифест самих exe права администратора не просит.

Удаление стирает `{app}` средствами Inno и снимает задачу планировщика. Оно не удаляет `%APPDATA%\DeskKit`, `%LOCALAPPDATA%\DeskKit` и zip-копии. Это сказано в README.

Русский язык мастера берётся из `Russian.isl`, который входит в Inno Setup 7.1.1. Если компилятор пишет, что файла нет, реализация останавливается и не подменяет язык пустым файлом.

Выход компилятора: `dist/DeskKit-Setup-0.1.0.exe`.

### 8.5. Пайплайн релиза

Workflow из раздела 11. Ручная команда, которой он соответствует, на всякий случай:

1. Поставить Python 3.12 и `pip install -e ".[dev]"`.
2. Прогнать `ruff` и `pytest`.
3. Две команды PyInstaller из раздела 8.3.
4. Скачать `https://github.com/jrsoftware/issrc/releases/download/is-7_1_1/innosetup-7.1.1-x64.exe`.
5. Установить тихо: `innosetup-7.1.1-x64.exe /VERYSILENT /SUPPRESSMSGBOXES /NORESTART /SP-`.
6. Компилятор: `C:\Program Files\Inno Setup 7\ISCC.exe installer\installer.iss`.
7. Посчитать SHA-256 и приложить exe к релизу тега.

Если `ISCC.exe` не лежит по этому пути, шаг падает. Искать компилятор по диску и ставить Inno Setup 6 запрещено. Версия компилятора зафиксирована: Inno Setup 7.1.1, 64-bit сборка от 2026-10-28.

Тег релиза имеет вид `v0.1.0` и совпадает с `deskkit.__version__`, с `project.version`, с `#define MyAppVersion` и с `filevers`. Первая публичная сборка — тег `v0.1.0`. Реализация тег не создаёт сама: это делает автор, когда Windows-приёмка из раздела 13 пройдена.

---

## 9. Безопасность и права

Жёсткие правила, которые нельзя ослабить «для удобства»:

1. `subprocess` вызывается только из `SubprocessRunner`, только списком аргументов, без `shell`. `creationflags` на Windows включает `CREATE_NO_WINDOW`.
2. Установка запускает только `winget` с аргументами из `winget_install_args`. Id проходит `Catalog.get` до построения команды. Произвольная строка из профиля, которая не входит в каталог, до процесса не доходит.
3. Очистка удаляет файлы только внутри корней, собранных `CleanupService` для выбранных целей. Корень цели не удаляется. Симлинки и точки повторной обработки не удаляются и не обходятся. Перед удалением путь ещё раз проверяется: `path.resolve().is_relative_to(root.resolve())`. Если проверка бросает `OSError`, файл пропускается как нечитаемый.
4. Временные файлы моложе 24 часов остаются. Кэш браузера ограничен каталогами `Cache`, `Code Cache`, `GPUCache` и `cache2`. Рядом лежащие `Cookies`, `Login Data`, `History`, `Web Data`, `Bookmarks`, `Extensions` не являются корнями и не обходятся.
5. Корзина очищается только если цель выбрана и подтверждена. Флаги `SHEmptyRecycleBinW` отключают второе системное подтверждение, потому что своё уже было. Звук и лишний прогресс тоже отключены константами из раздела 5.16.
6. Автозагрузка не удаляет запись без копии. Сбой удаления исходного значения откатывает копию. Команды из Run не исполняются. Общий реестр и общая папка без `is_admin()` дают `AdminRequiredError` до любой записи.
7. Копия не берёт корень диска, `Windows`, `Program Files`, `Program Files (x86)`. Назначение не может лежать внутри источника и не может быть его родителем. В архив не кладутся ссылки. Имена внутри zip относительные (`source-1/...`), манифест отдельно хранит абсолютные пути для хозяина копии. Архив не шифруется; об этом говорит интерфейс.
8. Ротация удаляет только файлы по регулярному выражению `^DeskKit-backup-\d{8}-\d{6}\.zip$` в папке назначения.
9. Профиль — JSON через `json.loads` / `json.dumps`. Запись атомарная. Неизвестная версия схемы отвергается.
10. Планировщик не получает `/RU`, пароль и `SYSTEM`. Уровень `/RL LIMITED`, флаг `/IT`: задача идёт в сеансе пользователя, когда он вошёл. Имя задачи только одно из двух фиксированных.
11. Повышение прав — только по кнопке `Запросить права администратора` через `ShellExecuteW(..., "runas", ...)`. Старт ярлыка, очистка пользовательской временной папки, отчёт, профиль и копия его не требуют. Отказ UAC не закрывает программу, кроме случая, когда пользователь сам подтвердил закрытие.
12. Журнал не пишет содержимое копируемых файлов и не пишет stdout winget на уровне INFO.
13. HTML-отчёт экранирует все подставленные строки.
14. Сеть. У процесса DeskKit нет HTTP-клиента. Пакеты качает `winget` с официальных источников пакета, когда пользователь подтвердил установку. Сборщик релиза качает один зафиксированный URL Inno Setup.
15. Установщик не кладёт программу в автозагрузку и не создаёт задачу копии. Задачу создаёт только пользователь.

Что видит пользователь без прав администратора: установку в область пользователя, очистку своего `%TEMP%`, кэша своих браузеров и корзины, отчёт, свой Run и свою папку Startup, копию своих папок, расписание от своего имени. `C:\Windows\Temp`, HKLM Run и общая папка Startup либо пропускают недоступные файлы, либо отказывают с понятным текстом и кнопкой повышения прав.

---

## 10. План тестов

Общее:

- `tests/conftest.py` задаёт автоиспользуемую фикстуру `isolated_env`. Она создаёт под `tmp_path` каталоги `Roaming`, `Local`, `Temp`, `Windows`, `ProgramData`, выставляет `APPDATA`, `LOCALAPPDATA`, `TEMP`, `TMP`, `SYSTEMROOT`, `PROGRAMDATA` и удаляет `DESKKIT_PROFILE`, если переменная есть. Фикстура не трогает реальный домашний каталог.
- Там же фикстура `context`, которая вызывает `make_context(tmp_path)` и отдаёт один `Context` на тест. `make_context` живёт в `tests/fakes.py`.
- `make_context(tmp_path: Path) -> Context` собирает боевые `LocalFileOps`, `ProfileStore` (путь `tmp_path / "Roaming" / "DeskKit" / "profile.json"`), `Catalog()`, сервисы на `FakeRunner`, `FakeRegistry`, `FakeRecycle`, `FakeAdmin` (`is_admin` ложно), `FakeClock`, `FakeSoftware`, `FakeSystem`. Корни очистки указывают внутрь `tmp_path / "Temp"` и `tmp_path / "browsers" / ...`. Папки автозагрузки — `tmp_path / "startup-user"` и `tmp_path / "startup-common"`, каталоги фикстура создаёт. `open_folder` — функция, которая пишет путь в список `opened` на объекте `FakeAdmin` (добавить туда список `opened: list[Path]`). `runner` в контексте — тот же `FakeRunner`, что у установки и планировщика. `resolve_cli_argv` не вызывается: префикс планировщика в тестах равен `["deskkit-cli"]`. `version` равен `__version__`.
- `tests/fakes.py` содержит `FakeRunner`, `FakeRegistry`, `FakeRecycle`, `FakeAdmin`, `FakeClock`, `FakeSoftware`, `FakeSystem` и `make_context`. Подделки записывают вызовы в списки. `FakeClock.now` возвращает `datetime(2026, 1, 15, 9, 0, tzinfo=timezone(timedelta(hours=3)))`, пока тест не подменит. Имя архива от этих часов: `DeskKit-backup-20260115-090000.zip`. `FakeSystem.snapshot_base` возвращает снимок с hostname `OFFICE-PC`, пустым списком программ и одним диском `C:\` на 1024 байта, `available=True`. `FakeSoftware.list_installed` по умолчанию пуст; тест отчёта подменяет его. `FakeRecycle.query` возвращает `(0, 0)`, `empty` пишет событие в список `emptied`. `FakeAdmin.relaunch_elevated` возвращает `ElevationResult(False, "Повышение прав отменено.")` и не поднимает процесс.
- `FakeRunner` повторяет контракт `CommandRunner`: очередь `CommandResult`, списки `calls` и `timeouts`, колбэк `on_call`, метод `terminate`, который ставит флаг. Пустая очередь на `run` роняет тест `AssertionError`.
- `FakeRegistry` хранит `dict[tuple[Hive, str], dict[str, RegValue]]`. `fail_delete: set[tuple[Hive, str, str]]` заставляет `delete_value` бросить `OSError` после того, как тест увидел порядок. Список `events` получает строки `set` и `delete` с ключом и именем.
- Сервисы в тестах конструируются напрямую. `build_context()` не вызывается.
- Окно не создаётся. Модули `deskkit.ui.screens`, `deskkit.ui.app`, `deskkit.ui.widgets` тесты не импортируют.

Каждый тест ниже обязателен, имя функции совпадает.

### `tests/test_version.py`

| Тест | Проверка |
| --- | --- |
| `test_version_string` | `__version__ == "0.1.0"` |
| `test_version_matches_pyproject` | `tomllib` видит `project.version == "0.1.0"` |
| `test_version_matches_inno` | в `installer/installer.iss` есть строка `#define MyAppVersion "0.1.0"` |
| `test_version_matches_file_info` | в `version_info.txt` есть `filevers=(0, 1, 0, 0)` и `FileVersion", "0.1.0"` |

### `tests/test_paths.py`

| Тест | Проверка |
| --- | --- |
| `test_profile_path_windows_env` | `APPDATA=C:\Users\A\AppData\Roaming` даёт `...\Roaming\DeskKit\profile.json` |
| `test_profile_path_fallback_without_appdata` | без ключа путь `home / ".deskkit" / "profile.json"` |
| `test_log_path_uses_localappdata` | `...\DeskKit\logs\deskkit.log` |
| `test_cleanup_roots_from_env` | `TEMP` и `SYSTEMROOT` попадают в соответствующие корни, Chrome оканчивается на `Google\Chrome\User Data` |
| `test_startup_folders` | оба пути оканчиваются на `Start Menu\Programs\Startup` |

### `tests/test_safety.py`

| Тест | Проверка |
| --- | --- |
| `test_reject_relative` | `ensure_absolute(Path("docs"))` бросает `PathNotAllowedError` |
| `test_drive_root` | `C:\` и `/` истинны для `is_drive_root`, `C:\Users` ложно |
| `test_denied_windows_and_program_files` | запрещены три префикса в разном регистре, `C:\Users\A\Documents` разрешён |
| `test_destination_inside_source` | назначение-потомок и источник-потомок оба конфликт |
| `test_safe_arcname_rejects` | `../a`, `/a`, `a/../../b`, `a\\b` отвергаются |
| `test_safe_arcname_accepts` | `source-1/docs/a.txt` возвращается как есть |
| `test_no_shell_true_in_sources` | обход `deskkit/**/*.py` не находит `shell=True`, `os.system`, `pickle.loads`, `eval(` |

### `tests/test_text.py`

| Тест | Проверка |
| --- | --- |
| `test_format_bytes_table` | все шесть пар из таблицы раздела 5.7 |
| `test_format_bytes_negative` | `ValueError` |
| `test_install_preview_text_exact` | строка из раздела 5.7 байт в байт |
| `test_install_preview_missing_winget` | первая строка `winget не найден. Установка не начнётся.` |
| `test_confirmation_footer_exact` | ровно фраза про `--yes` |
| `test_cleanup_preview_text_exact` | пример 3 файлов и `1,5 КБ` |
| `test_install_report_text_exact` | пример «уже установлен» / «установлено» |
| `test_scope_labels` | две русские подписи |

### `tests/test_catalog.py`

| Тест | Проверка |
| --- | --- |
| `test_count_and_unique_ids` | длина 15, id уникальны |
| `test_presets_match_table` | три набора равны спискам раздела 5.9 |
| `test_unknown_id` | `ValidationError` и текст начинается с `Неизвестная программа:` |
| `test_unknown_preset` | текст начинается с `Неизвестный набор:` |

### `tests/test_profile.py`

| Тест | Проверка |
| --- | --- |
| `test_default_values` | цели без `windows_temp`, keep 5, расписание выключено, понедельник 09:00 |
| `test_roundtrip` | `load(save(p))` равен `p` на профиле с одним id и путём |
| `test_missing_file_does_not_create` | `load` вернул умолчание, файла нет |
| `test_unknown_keys_ignored` | лишний ключ `telemetry` не мешает разбору |
| `test_bad_schema_version` | `ProfileVersionError` |
| `test_unknown_package` | `ValidationError` про программу |
| `test_unknown_target` | текст `Неизвестная цель очистки.` |
| `test_bad_time` | `24:00` и `9:00` отвергаются, `09:00` принимается |
| `test_bad_weekday` | `Monday` отвергается, `MON` принимается |
| `test_keep_last_bounds` | 0 и 31 отвергаются, 1 и 30 принимаются |
| `test_invalid_json` | текст `Файл профиля повреждён.` |
| `test_sources_need_not_exist_at_load` | несуществующий путь в JSON загружается |
| `test_bad_scope` | текст `Неизвестная область установки.` |
| `test_atomic_save_replaces` | после `save` нет файла `profile.json.tmp`, есть валидный JSON |

### `tests/test_commands.py`

| Тест | Проверка |
| --- | --- |
| `test_winget_args_user` | список содержит `--scope`, `user`, `--no-upgrade`, `--source`, `winget`, `--exact`, `--disable-interactivity` и не содержит `--override` |
| `test_winget_args_auto` | `--scope` отсутствует |
| `test_schtasks_weekly` | argv содержит `/SC`, `WEEKLY`, `/D`, `MON`, `/ST`, `09:00`, `/RL`, `LIMITED`, `/IT`, `/F` и не содержит `/RU` и `SYSTEM` |
| `test_schtasks_daily` | есть `/SC`, `DAILY`, нет `/D` |
| `test_tr_too_long` | префикс длиннее лимита бросает `ScheduleError` |
| `test_subprocess_kwargs_platform` | на Windows значение `0x08000000`, иначе пустой словарь |

### `tests/test_process.py`

| Тест | Проверка |
| --- | --- |
| `test_terminate_sleeping_process` | `SubprocessRunner` запускает `sys.executable -c "import time; time.sleep(30)"`, другой поток вызывает `terminate`, `run` возвращается раньше 10 секунд с `cancelled=True` |

### `tests/test_files.py`

| Тест | Проверка |
| --- | --- |
| `test_walk_sums_and_skips_missing_root` | отсутствующий корень даёт пусто; обычный файл виден с размером |
| `test_walk_does_not_follow_symlink` | если `os.symlink` бросает `OSError`, тест `pytest.skip`; иначе файл вне корня, на который указывает ссылка внутри, не увеличивается в размере цели, а ссылка помечена `is_symlink` |
| `test_zip_contains_manifest_and_member` | после `create_zip` в архиве есть `deskkit-manifest.json` и член, partial-файла нет |
| `test_zip_cleans_partial_on_bad_arcname` | arcname `../x` не оставляет `.partial` |
| `test_delete_and_empty_dir` | файл удаляется, пустой каталог снимается, непустой `remove_dir_if_empty` даёт False |

### `tests/test_cleanup.py`

| Тест | Проверка |
| --- | --- |
| `test_preview_sums_files` | три файла во временной папке, возраст 48 часов, байты и число сходятся |
| `test_skips_recent_temp_only` | файл моложе часа не входит в `byte_count` и увеличивает `skipped_recent`; такой же молодой файл в `Cache` Chrome входит |
| `test_does_not_include_cookies` | `User Data/Default/Cookies` не входит, `User Data/Default/Cache/a.bin` входит |
| `test_absent_browser` | нет каталога Chrome — `absent` и нули, исключения нет |
| `test_symlink_not_counted` | ссылка увеличивает `skipped_links`, не байты; skip, если symlink нельзя создать |
| `test_apply_deletes_and_keeps_root` | файлы исчезли, корневая папка цели осталась |
| `test_dry_run_deletes_nothing` | файл на месте, `dry_run` истинно |
| `test_confirmation_required` | `ConfirmationRequired`, файл на месте |
| `test_locked_file_skipped` | подкласс `FileOps`, чей `delete_file` бросает `PermissionError`; `skipped_locked == 1`, другие файлы удалены |
| `test_cancel_before_second_file` | токен отменяется из колбэка после первого удаления; `cancelled` истинно, второй файл цел |
| `test_recycle_only_when_selected` | без цели корзины `empty` не вызван; с целью и подтверждением вызван один раз |
| `test_recycle_error_is_warning` | `query` бросает `DeskKitError`, preview не падает, предупреждение непустое |
| `test_empty_targets` | `ValidationError` |

### `tests/test_report.py`

| Тест | Проверка |
| --- | --- |
| `test_html_escapes_and_has_sections` | имя программы `<script>` превращается в экранированный текст, в документе есть `Система`, `Диски`, `Установленные программы`, нет живого `<script>` |
| `test_html_utf8_note` | есть фраза `Никуда не отправляется.` |
| `test_empty_software_row` | фраза `Программы не найдены` |
| `test_xlsx_sheets_and_headers` | имена листов `Система`, `Диски`, `Программы`; на листе программ заголовки `Имя`, `Версия`, `Издатель`, `Дата` |
| `test_xlsx_disk_bytes` | в колонке байтов лежит исходное целое, рядом текст `format_bytes` |
| `test_summary_contains_hostname` | поддельный hostname виден в `report_summary_text` |

Поддельный снимок в этих тестах собирается вручную, без psutil: hostname `OFFICE-PC`, один диск `C:\` на 1024 байта, одна программа `1С <script>` (или просто `<script>`, как в тесте экранирования).

### `tests/test_startup.py`

| Тест | Проверка |
| --- | --- |
| `test_list_combines_sources` | по одной записи каждого источника, порядок источников как в разделе 5.20 |
| `test_id_format` | `hkcu_run\|OneDrive` |
| `test_skip_non_string` | `RegKind.OTHER` не попадает в список |
| `test_skip_pipe_in_name` | имя `a\|b` не попадает |
| `test_disable_hkcu_order` | события fake: сначала `set` в ключе `DisabledStartup\HKCU`, потом `delete` в Run |
| `test_disable_rolls_back` | `fail_delete` на Run; после исключения запасного значения тоже нет |
| `test_enable_restores` | значение снова в Run и отсутствует в запасе |
| `test_hklm_requires_admin` | `FakeAdmin.is_admin False` → `AdminRequiredError`, событий записи нет, в том числе при `dry_run=True` |
| `test_disable_shortcut` | `Slack.lnk` становится `Slack.lnk.deskkit-disabled` |
| `test_enable_shortcut` | обратное переименование |
| `test_dry_run_registry` | событий `set`/`delete` нет, у возвращённой записи `enabled` ложно |
| `test_confirmation_required` | событий нет |
| `test_missing_entry` | текст `Запись автозагрузки не найдена.` |

Ярлыки создаются `Path.write_bytes(b"")` в `tmp_path`, шлюз папок — просто эти каталоги, переданные в конструктор. Отдельный gateway каталогов не нужен: сервис сам делает `iterdir`.

### `tests/test_backup.py`

| Тест | Проверка |
| --- | --- |
| `test_preview_counts` | два файла, байты суммируются, имя архива `DeskKit-backup-20260115-090000.zip` |
| `test_rejects_drive_root` | `PathNotAllowedError` |
| `test_rejects_windows_directory` | текст начинается с `Эту папку копировать нельзя:` |
| `test_rejects_overlap` | текст `Папка назначения пересекается с копируемой.` |
| `test_insufficient_space` | `disk_free` возвращает 10 при файле в 100 байт, текст `Недостаточно места для копии.` |
| `test_apply_zip_and_manifest` | архив существует, в манифесте `app == DeskKit`, arcname начинается с `source-1/` |
| `test_two_sources_indexed` | второй источник лежит под `source-2/` |
| `test_unreadable_recorded` | `walk_files` подделки отдаёт `unreadable`, в манифесте `skipped` непуст, архив всё равно создан |
| `test_symlink_skipped` | ссылка не член архива; skip, если symlink нельзя создать |
| `test_rotation_only_matching` | в папке лежат `notes.zip`, `DeskKit-backup-20260101-000000.zip` и новый; при `keep_last=1` удалён только старый по шаблону, `notes.zip` цел |
| `test_dry_run_creates_nothing` | каталог назначения не создаётся, если его не было |
| `test_confirmation_required` | каталог не создан |
| `test_missing_source` | текст начинается с `Папка не найдена:` |
| `test_too_many_sources` | 21 путь, текст `Можно выбрать не больше 20 папок.` |
| `test_cancel_during_walk` | `cancelled`, архива нет |

Для тестов, которым нужен управляемый обход, допускается подкласс `LocalFileOps` с переопределённым `walk_files`. Боевой класс при этом остаётся на тестах zip и symlink.

### `tests/test_schedule.py`

| Тест | Проверка |
| --- | --- |
| `test_parse_weekly_xml` | фикстура раздела 5.22: weekly, MON, 09:00, enabled, имя первичное |
| `test_parse_daily_xml` | daily, weekday None |
| `test_missing_task` | оба вызова вернули код 1, `exists` ложно |
| `test_fallback_name` | первый вызов код 1, второй код 0 с XML, `task_name == "DeskKit Backup"` |
| `test_create_uses_primary_name` | `apply` с confirmed шлёт `/TN` равный `\DeskKit\Backup` |
| `test_create_requires_confirmation` | `calls` пуст |
| `test_disabled_schedule_rejected` | текст `В профиле расписание выключено.` |
| `test_remove_deletes_both` | два вызова `/Delete`, коды 1 не превращаются в исключение |
| `test_argv_has_no_ru_or_system` | в любом элементе `create_argv` нет `/RU` и нет `SYSTEM` |

### `tests/test_install.py`

| Тест | Проверка |
| --- | --- |
| `test_preview_does_not_call_runner` | `calls` пуст, имена на месте |
| `test_unknown_id` | `ValidationError` |
| `test_empty_ids` | текст `Не выбрано ни одной программы.` |
| `test_dry_run` | `calls` пуст, `dry_run` истинно |
| `test_confirmation_required` | `calls` пуст |
| `test_success` | код 0 → SUCCESS, в argv есть id и `--no-upgrade` |
| `test_already_installed_codes` | каждый код из `ALREADY_INSTALLED_CODES` даёт `SKIPPED_INSTALLED` |
| `test_retry_once_without_scope` | первый результат `-1978335216` при scope user, второй код 0; второй argv без `--scope`; ровно два вызова |
| `test_no_retry_when_auto` | scope auto и код `NO_APPLICABLE` дают один вызов и FAILED |
| `test_admin_code` | `-1978335207` → `ADMIN_REQUIRED` |
| `test_timeout_message` | `timed_out=True` → сообщение `превышено время ожидания (30 минут)` |
| `test_cancel_between_packages` | `on_call` отменяет токен на первом пакете; второй id не вызывается; `cancelled` истинно |
| `test_winget_missing` | `WingetNotFoundError`, текст начинается с `Не найден winget.` |
| `test_order_preserved` | три id вызываются в переданном порядке |
| `test_partial_failure_keeps_success` | первый SUCCESS, второй код 1; в отчёте оба, у второго FAILED |

### `tests/test_cli.py`

Контекст поддельный, передаётся в `run(argv, context=...)`.

| Тест | Проверка |
| --- | --- |
| `test_version_dispatch` | `dispatch(["--version"]) == 0`, stdout `DeskKit 0.1.0\n` |
| `test_help` | `run(["--help"])` завершается `SystemExit` 0 |
| `test_install_list` | stdout содержит `7zip.7zip` и `7-Zip`; до и после вызова ключей `customtkinter` и `tkinter` нет в `sys.modules` |
| `test_install_preview_exit_3` | код 3, в stdout есть `7-Zip` и футер, runner пуст |
| `test_install_dry_run_exit_0` | код 0, runner пуст |
| `test_install_yes` | код 0, один вызов winget |
| `test_preset_and_id_conflict` | код 2, stderr содержит `не оба сразу` |
| `test_clean_preview_exit_3` | код 3 |
| `test_clean_yes` | код 0 при одной цели и пустой папке (создать корень, чтобы не было ошибки) |
| `test_report_show` | код 0, hostname в stdout |
| `test_report_save_html` | файл содержит `<html` |
| `test_report_save_bad_suffix` | код 2 |
| `test_startup_list` | код 0 |
| `test_startup_disable_without_yes` | код 3, реестр без событий |
| `test_backup_run_from_profile` | профиль с одной папкой и назначением, `--yes`, код 0, архив есть |
| `test_backup_source_without_dest` | код 2 |
| `test_profile_init_and_show` | init код 0, show печатает `"schema_version": 1` |
| `test_profile_init_twice` | второй код 1, stderr `Профиль уже есть.` |
| `test_profile_import_requires_yes` | код 3, старый файл не заменён |
| `test_verbose_does_not_crash` | `run(["-v", "install", "list"], context=...)` код 0 |
| `test_dispatch_gui_rejects_extra` | `dispatch(["gui", "x"]) == 4` |
| `test_unknown_command` | `SystemExit` 2 |
| `test_schedule_disabled_profile` | `backup schedule --yes` код 1, stderr про выключенное расписание |
| `test_dry_run_wins_over_yes` | `clean run --target user_temp --dry-run --yes` код 0, файл, созданный во временном корне, на месте |

### `tests/test_presenters.py`

| Тест | Проверка |
| --- | --- |
| `test_can_execute` | `can_execute(False)` истинно, `can_execute(True)` ложно |
| `test_home_status_winget_missing` | пустой путь winget → `winget_found` ложно |
| `test_install_confirmation_has_lead_and_name` | есть `CONFIRM_LEAD` и `7-Zip` |
| `test_profile_init_refuses_second` | второй `init_default` бросает `ValidationError` |
| `test_strings_nav_complete` | у `NAV` ровно ключи home, install, cleanup, report, startup, backup, profile, logs, значения не пустые |

### `tests/test_logging.py`

| Тест | Проверка |
| --- | --- |
| `test_creates_file` | после `setup_logging` и `logger.info("проверка")` строка есть в файле |
| `test_rotation_settings` | хендлер `RotatingFileHandler`, `maxBytes == 1_000_000`, `backupCount == 5` |
| `test_missing_tail` | `read_log_tail` отсутствующего файла равен `Журнал пока пуст.` |

### `tests/test_windows_readonly.py`

Все три теста помечены `pytest.mark.skipif(sys.platform != "win32", reason="Windows-only")`.

| Тест | Проверка |
| --- | --- |
| `test_is_admin_returns_bool` | `isinstance(WindowsPlatform(...).is_admin(), bool)` |
| `test_resolve_winget_type` | результат `str` или `None` |
| `test_query_recycle_bin_readonly` | `query` возвращает пару неотрицательных int либо `DeskKitError`; `empty` не вызывать |

На Linux эти тесты пропускаются и не роняют прогон. На Windows они только читают.

---

## 11. CI

Файл `.github/workflows/ci.yml`:

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:

permissions:
  contents: read

jobs:
  linux:
    name: Linux ${{ matrix.python-version }}
    runs-on: ubuntu-latest
    strategy:
      fail-fast: false
      matrix:
        python-version: ["3.11", "3.12"]
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: ${{ matrix.python-version }}
          cache: pip
          cache-dependency-path: pyproject.toml
      - name: Install
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      - name: Ruff
        run: |
          ruff check .
          ruff format --check .
      - name: Pytest
        run: pytest
      - name: Version and help
        run: |
          python -m deskkit --version
          python -m deskkit --help

  windows:
    name: Windows
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: pyproject.toml
      - name: Install
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      - name: Ruff
        run: |
          ruff check .
          ruff format --check .
      - name: Pytest
        run: pytest
      - name: Version and help
        run: |
          python -m deskkit --version
          python -m deskkit --help
```

Windows-джоб не вызывает `winget install`, не вызывает `schtasks /Create`, не собирает установщик и не открывает окно. `python -m deskkit --help` обязан завершаться нулём и не создавать `CTk`.

Файл `.github/workflows/release.yml`:

```yaml
name: Release

on:
  push:
    tags: ["v[0-9]+.[0-9]+.[0-9]+"]

permissions:
  contents: write

jobs:
  installer:
    name: Build installer
    runs-on: windows-latest
    steps:
      - uses: actions/checkout@v7
      - uses: actions/setup-python@v7
        with:
          python-version: "3.12"
          cache: pip
          cache-dependency-path: pyproject.toml
      - name: Install
        run: |
          python -m pip install --upgrade pip
          python -m pip install -e ".[dev]"
      - name: Test
        run: pytest
      - name: Version matches tag
        shell: pwsh
        run: |
          $version = python -c "import deskkit; print(deskkit.__version__)"
          if ("v$version" -ne "${{ github.ref_name }}") {
            Write-Error "Tag ${{ github.ref_name }} does not match $version"
            exit 1
          }
      - name: PyInstaller
        run: |
          pyinstaller installer/deskkit-gui.spec --noconfirm --distpath dist --workpath build/gui
          pyinstaller installer/deskkit-cli.spec --noconfirm --distpath dist --workpath build/cli
      - name: Install Inno Setup 7.1.1
        shell: pwsh
        run: |
          $url = "https://github.com/jrsoftware/issrc/releases/download/is-7_1_1/innosetup-7.1.1-x64.exe"
          Invoke-WebRequest -Uri $url -OutFile "$env:RUNNER_TEMP\innosetup.exe"
          Start-Process -FilePath "$env:RUNNER_TEMP\innosetup.exe" -ArgumentList "/VERYSILENT","/SUPPRESSMSGBOXES","/NORESTART","/SP-" -Wait
          if (-not (Test-Path "C:\Program Files\Inno Setup 7\ISCC.exe")) {
            Write-Error "ISCC.exe not found"
            exit 1
          }
      - name: Compile installer
        run: '& "C:\Program Files\Inno Setup 7\ISCC.exe" installer\installer.iss'
      - name: Hash
        shell: pwsh
        run: |
          $file = Get-ChildItem dist\DeskKit-Setup-*.exe | Select-Object -First 1
          $hash = (Get-FileHash $file.FullName -Algorithm SHA256).Hash
          @"
          Установщик DeskKit ${{ github.ref_name }}

          Файл: $($file.Name)
          SHA256: $hash

          Сверьте сумму перед запуском. Установщик не подписан цифровой подписью, поэтому Windows SmartScreen может показать предупреждение.
          "@ | Set-Content -Encoding utf8 dist\release-body.md
      - name: Upload artifact
        uses: actions/upload-artifact@v7
        with:
          name: DeskKit-Setup
          path: dist/DeskKit-Setup-*.exe
          if-no-files-found: error
      - name: GitHub Release
        uses: softprops/action-gh-release@v3
        with:
          files: dist/DeskKit-Setup-*.exe
          body_path: dist/release-body.md
          generate_release_notes: true
          prerelease: ${{ contains(github.ref_name, '-') }}
```

Секретов, кроме встроенного `GITHUB_TOKEN`, нет. Подписывать артефакт нечем — шаг подписи отсутствует нарочно.

`python -m deskkit --help` на Windows в CI может попытаться импортировать argparse и завершиться. Он не должен импортировать CustomTkinter. Это уже обеспечено `dispatch`.

---

## 12. README, описание репозитория и темы

Заменить содержимое `README.md` ровно на текст ниже. Картинок в нём нет специально: битых ссылок на GitHub быть не должно, пока снимки не сняты на Windows.

```markdown
# DeskKit

DeskKit — программа для Windows 10 и Windows 11, которая помогает настроить новый компьютер и поддерживать его в порядке. Её делает Стефан Митрохин (GitHub: [Stephanchik](https://github.com/Stephanchik)) для дома и небольших офисов: поставить привычный набор программ, убрать временные файлы, посмотреть отчёт о компьютере, проверить автозагрузку и настроить копию документов.

Программа ставится обычным установщиком. Отдельно ставить Python не нужно.

## Что умеет

- Ставит программы из готового списка через winget: браузеры, архиватор, офис, мессенджер и другие. Можно выбрать набор «Дом», «Офис» или «Разработка» и поправить галочки.
- Показывает, сколько места занимают временные файлы, кэш браузеров и корзина, и удаляет их только после подтверждения.
- Собирает отчёт о процессоре, памяти, дисках, версии Windows и установленных программах. Отчёт сохраняется в HTML или Excel.
- Показывает программы в автозагрузке и даёт выключить или включить их обратно. Записи не удаляются безвозвратно.
- Делает zip-копию выбранных папок на другой диск и может запускать её по расписанию Windows.
- Хранит настройки в файле JSON, чтобы повторить тот же набор программ на другом компьютере.

## Чего программа не делает

DeskKit не чистит реестр, не обновляет драйверы и Windows, не лечит вирусы и не отправляет сведения о компьютере в интернет. Установка программ идёт только из списка внутри программы. Архив копии не шифруется. Вернуть файлы из архива можно обычной распаковкой zip, отдельного мастера восстановления нет.

## Скриншоты

Снимки появятся после проверки на Windows и будут лежать в каталоге `docs/screenshots/`. Пока их нет, эта страница на картинки не ссылается.

1. `docs/screenshots/01-home.png` — главный экран: winget, профиль, расписание, права.
2. `docs/screenshots/02-install.png` — набор «Офис» и список программ.
3. `docs/screenshots/03-install-confirm.png` — окно подтверждения перед установкой.
4. `docs/screenshots/04-cleanup.png` — подсчёт места до удаления.
5. `docs/screenshots/05-report.png` — краткий отчёт на экране.
6. `docs/screenshots/06-startup.png` — автозагрузка, выключенная запись помечена.
7. `docs/screenshots/07-backup.png` — папки, назначение и расписание.
8. `docs/screenshots/08-profile.png` — файл настроек JSON.

## Как установить

1. Откройте [релизы](https://github.com/Stephanchik/windows-automation-utility/releases) и скачайте файл `DeskKit-Setup-0.1.0.exe`. Если вышла более новая версия, берите её и сверяйте имя файла с описанием релиза.
2. Сверьте контрольную сумму SHA-256 с суммой в описании релиза. В PowerShell:

```powershell
Get-FileHash .\DeskKit-Setup-0.1.0.exe -Algorithm SHA256
```

3. Запустите установщик. Windows может показать предупреждение SmartScreen: установщик не подписан цифровой подписью. Это ожидаемо для этой сборки. Продолжать имеет смысл только если сумма совпала.
4. Установщик один раз попросит права администратора, чтобы положить программу в `C:\Program Files\DeskKit` и создать ярлыки. Сама программа после этого работает с обычными правами.
5. Ярлык «DeskKit» появится в меню «Пуск». Ярлык на рабочем столе создаётся, если соответствующая галочка была включена.

Нужна 64-разрядная Windows 10 или Windows 11. Для установки программ нужен winget («Установщик приложений»). В Windows 11 он уже есть. Остальные разделы DeskKit работают и без него.

## Как пользоваться

Откройте DeskKit ярлыком. Слева — разделы: обзор, установка, очистка, отчёт, автозагрузка, копии, профиль и журнал.

Перед удалением файлов, установкой, сменой автозагрузки и копированием программа показывает состав операции. Кнопка подтверждения нажимается мышью. Клавиша Enter диалог не подтверждает.

Переключатель «Режим просмотра» внизу окна отключает выполнение и оставляет просмотр.

Командная строка после установки:

```text
"C:\Program Files\DeskKit\DeskKit-cli.exe" --help
"C:\Program Files\DeskKit\DeskKit-cli.exe" install list
"C:\Program Files\DeskKit\DeskKit-cli.exe" report show
```

Без `--yes` команды, которые меняют компьютер, только показывают план и ничего не записывают.

## Безопасность

- Удаляются только известные места: временная папка пользователя, по желанию `C:\Windows\Temp`, корзина и кэш Chrome, Edge и Firefox. Пароли, закладки, история и расширения браузера в очистку не входят.
- Файлы во временных папках моложе 24 часов не удаляются: их может держать текущая установка.
- Корзина очищается только если этот пункт включён и подтверждён.
- Автозагрузка выключается переносом записи в служебный раздел реестра DeskKit или переименованием ярлыка. Включение возвращает её обратно.
- Копия складывается в zip без пароля. Держите архив на диске, к которому есть доступ только у вас.
- Журнал: `%LOCALAPPDATA%\DeskKit\logs\deskkit.log`.
- Настройки: `%APPDATA%\DeskKit\profile.json`.

Права администратора нужны не всегда. Программа предложит их отдельно, если вы меняете общую автозагрузку или хотите повторить действие с повышенными правами. Отказ не закрывает программу.

Расписание копии создаётся в Планировщике заданий под именем `\DeskKit\Backup`. Если создать имя с папкой не удалось, используется `DeskKit Backup`. Задача выполняется от вашего пользователя и только когда вы вошли в систему. Пароль для этого не сохраняется. В назначенное время компьютер должен быть включён, а сеанс — открыт.

## Как удалить

Откройте «Параметры Windows → Приложения → DeskKit → Удалить» или ярлык «Удалить DeskKit» в меню Пуск.

Удаление снимает программу, ярлыки и задачу планировщика. Файл настроек, журнал и уже сделанные zip-копии остаются. Их можно удалить вручную:

- `%APPDATA%\DeskKit`
- `%LOCALAPPDATA%\DeskKit`
- папка, которую вы указали для копий

## Лицензия

MIT. Copyright (c) 2026 Stephanchik.

Программа поставляется как есть, без гарантии. Перед очисткой и копированием проверьте предварительный список.
```

Описание репозитория на GitHub (поле Description, одна строка):

```text
Утилита настройки и обслуживания Windows для дома и небольшого офиса: установка программ, очистка, отчёт, автозагрузка и резервные копии.
```

Темы репозитория, все сразу:

```text
python
windows
winget
pyinstaller
inno-setup
desktop-app
automation
customtkinter
```

Команда, которую реализация выполняет один раз из клона, если `gh` уже авторизован на этот репозиторий:

```text
gh repo edit Stephanchik/windows-automation-utility --description "Утилита настройки и обслуживания Windows для дома и небольшого офиса: установка программ, очистка, отчёт, автозагрузка и резервные копии." --add-topic python --add-topic windows --add-topic winget --add-topic pyinstaller --add-topic inno-setup --add-topic desktop-app --add-topic automation --add-topic customtkinter
```

Если `gh` отвечает отказом прав, описание и темы записать в конец PR и не повторять попытку. Сайт, вики и другие поля About не заполнять.

---

## 13. Порядок реализации и приёмка

Идти сверху вниз. Шаг не начинается, пока предыдущий не зелёный. Коммит на шаг, сообщение на английском, в повелительной форме, до 72 символов в заголовке. В коммит не попадают `dist/`, `build/`, `__pycache__`, журналы.

### Шаг 1. Каркас

Файлы: `pyproject.toml`, `deskkit/__init__.py`, пустые пакеты `__init__.py` по дереву, правка `.gitignore`, `tests/test_version.py` только с `test_version_string` и `test_version_matches_pyproject`.

Приёмка: `pip install -e ".[dev]"` ставится, `ruff check .` и `pytest` зелёные, `python -c "import deskkit; print(deskkit.__version__)"` печатает `0.1.0`.

### Шаг 2. Модели, ошибки, пути, безопасность, тексты

Файлы: `errors.py`, `models.py`, `cancel.py`, `paths.py`, `safety.py`, `text.py`, тесты `test_paths`, `test_safety`, `test_text`.

Приёмка: тесты этих модулей зелёные, отрицательный `format_bytes` бросает `ValueError`, относительный путь отвергается.

### Шаг 3. Каталог и профиль

Файлы: `catalog.py`, `profile.py`, `test_catalog.py`, `test_profile.py`.

Приёмка: ровно 15 id, круг save/load, битый JSON даёт `Файл профиля повреждён.`, отсутствующий файл не создаётся.

### Шаг 4. Платформенный край без Win32-записи

Файлы: `platform/protocols.py`, `commands.py`, `process.py`, `files.py`, `tests/fakes.py`, `tests/conftest.py`, `test_commands.py`, `test_process.py`, `test_files.py`.

Приёмка: argv winget совпадает со списком раздела 5.11, argv schtasks не содержит `/RU`, спящий процесс обрывается, zip содержит манифест.

### Шаг 5. Очистка

Файлы: `services/cleanup.py`, `test_cleanup.py`.

Приёмка: сухой прогон не удаляет файл; без подтверждения файл цел; cookies вне `Cache` не считаются; файл моложе 24 часов во временной папке остаётся.

### Шаг 6. Отчёт

Файлы: `services/report.py`, `platform/system_probe.py`, `test_report.py`.

Приёмка: HTML экранирует `<script>`, книга Excel содержит три листа с заданными именами. `system_probe.py` может остаться без прямого теста: он в `omit`.

### Шаг 7. Автозагрузка

Файлы: `services/startup.py`, `test_startup.py`.

Приёмка: порядок операций реестра «копия, потом удаление», откат при сбое, HKLM без прав не пишет даже в сухом прогоне, ярлык переименовывается, а не удаляется.

### Шаг 8. Копия

Файлы: `services/backup.py`, `test_backup.py`.

Приёмка: корень диска и `C:\Windows` отвергаются, архив создаётся с `source-1/`, чужой `notes.zip` не удаляется ротацией, сухой прогон не создаёт каталог.

### Шаг 9. Планировщик

Файлы: `services/schedule.py`, `test_schedule.py`.

Приёмка: XML из плана разбирается, выключенный профиль не вызывает `schtasks`, удаление пытается стереть оба имени.

### Шаг 10. Установка winget

Файлы: `services/install.py`, `test_install.py`.

Приёмка: неизвестный id не доходит до runner; код «уже установлено» — пропуск; нет подходящего установщика в области пользователя даёт ровно один повтор без `--scope`; отмена не запускает второй пакет.

### Шаг 11. CLI

Файлы: `cli/main.py`, `__main__.py`, `entry_cli.py`, `logging_setup.py`, `test_cli.py`, `test_logging.py`.

Приёмка: таблица кодов выхода из раздела 4 соблюдена тестами; `dispatch(["gui", "x"])` равен 4; `python -m deskkit --version` печатает версию; импорт `deskkit.cli.main` не импортирует `customtkinter` (проверить отсутствием ключа в `sys.modules` внутри `test_install_list` до и после — добавить эту проверку в `test_install_list`).

### Шаг 12. GUI

Файлы: `ui/strings.py`, `theme.py`, `widgets.py`, `presenters.py`, `app.py`, все `screens/*.py`, `entry_gui.py`, `app_context.py`, `platform/windows.py`, `test_presenters.py`, `test_windows_readonly.py`.

Приёмка: `pytest` зелёный на Linux без дисплея; тесты не создают `CTk`; у `NAV` восемь пунктов; `can_execute(True)` ложно. Окно вручную на Linux не открывать. Импорт `deskkit.platform.windows` на Linux бросает `ImportError`.

Сборка экранов сверяется с разделом 6 по списку: восемь разделов, диалог с фокусом на `Отмена`, Enter не подтверждает, режим просмотра гасит «Выполнить», задача копии сохраняет профиль до вызова планировщика.

### Шаг 13. Иконка и установщик

Файлы: `installer/make_icon.py`, оба asset, оба spec, `version_info.txt`, `installer.iss`, оставшиеся тесты версии.

Приёмка: `python installer/make_icon.py` создаёт png и ico; `test_version_matches_inno` и `test_version_matches_file_info` зелёные. На Linux PyInstaller и ISCC не запускать. Спеки остаются в git благодаря исключению в `.gitignore`.

### Шаг 14. Workflow

Файлы: `.github/workflows/ci.yml`, `.github/workflows/release.yml`.

Приёмка: YAML — валидный, имена action совпадают с разделом 11 (`checkout@v7`, `setup-python@v7`, `upload-artifact@v7`, `softprops/action-gh-release@v3`), релизный workflow срабатывает только на тег, CI не ставит Inno Setup. Локально достаточно `python -c "import yaml,pathlib; yaml.safe_load(pathlib.Path('.github/workflows/ci.yml').read_text())"` если PyYAML есть. Если PyYAML нет, не ставить его: просмотреть отступы глазами и положиться на GitHub. В зависимости PyYAML не добавлять.

### Шаг 15. README и описание репозитория

Файлы: `README.md`. Команда `gh repo edit` из раздела 12.

Приёмка: README совпадает с разделом 12, в нём нет `![`, нет ссылок на png. Описание и темы выставлены либо перечислены в ответе, если `gh` отказал.

### Шаг 16. Сквозная автоматическая приёмка

Команды из корня:

```text
ruff check .
ruff format --check .
pytest
python -m deskkit --version
python -m deskkit --help
```

Ожидание: покрытие не ниже 90% по конфигурации из `pyproject.toml`, код выхода всех команд 0. `pytest` на Linux пропускает три Windows-теста и не пропускает остальные.

Ручная приёмка на Windows — до тега, не до коммита реализации, если у исполнителя нет интерактивного рабочего стола Windows. Её выполняет автор на Windows 10 или 11:

1. Собрать оба exe и установщик командами раздела 8.
2. Поставить на чистую учётную запись, проверить ярлыки Пуск и рабочего стола, свойства exe (версия 0.1.0, компания Stefan Mitrokhin).
3. Открыть окно без UAC. Статус «Обычные права».
4. Просмотр набора «Дом» не ставит программы. Подтверждённая установка `7zip.7zip` в область пользователя ставит 7-Zip или сообщает, что он уже есть. Сеть при этом нужна.
5. Очистка: просмотр показывает число файлов; отказ в диалоге ничего не удаляет; подтверждение удаляет только выбранное. Файл, созданный во временной папке только что, остаётся.
6. Отчёт HTML открывается в браузере локально, Excel открывается, имя программы с символом `<` видно как текст.
7. Выключение ярлыка в своей папке автозагрузки переименовывает его, включение возвращает имя. Запись HKLM без повышения прав не меняется.
8. Копия одной небольшой папки на другой диск создаёт zip, внутри есть `deskkit-manifest.json`. Посторонний файл в папке назначения остаётся.
9. Сохранение расписания создаёт задачу `\DeskKit\Backup` или `DeskKit Backup`. В свойствах задачи нет сохранённого пароля, уровень прав обычный. `backup unschedule --yes` задачу удаляет.
10. Экспорт профиля, удаление программы через «Приложения», проверка, что JSON и zip остались, а задача планировщика исчезла.
11. Сверить SHA-256 установщика с тем, что релизный workflow напишет в описание релиза, когда автор поставит тег `v0.1.0`.

Реализация не ставит тег и не публикует релиз сама.

---

## 14. Риски и вопросы

Вопросы, которые могли остановить работу, закрыты решениями раздела 1.3. Ниже то, что может сломать уже согласованный план, и что делать, не расширяя продукт.

| Риск | Что делать |
| --- | --- |
| SmartScreen пугает заказчика, подписи нет | Не покупать сертификат в рамках v1 и не подделывать подпись. README и текст релиза говорят об этом прямо. Тег ставится только после сверки SHA-256. |
| Антивирус ругается на PyInstaller | UPX не включать. Если сработает эвристика, не обфусцировать код. Зафиксировать ложное срабатывание в заметке к релизу и оставить сборку как есть. |
| `Yandex.Browser` отсутствует в winget | Удалить только эту строку каталога и поправить число 15 в тесте. Остальной каталог не перебирать. |
| У пакета нет сборки `--scope user` | Уже покрыто одним повтором без `--scope`. Третий повтор и переход на `--scope machine` не добавлять. |
| winget нет на Windows 10 LTSC | Сообщение `WingetNotFoundError`. Не скачивать App Installer из программы. |
| Коды выхода winget когда-нибудь сдвинутся | Константы раздела 5.17 не «улучшать» наугад. Если на ручной приёмке уже установленный 7-Zip даёт другой код, добавить этот один код в `ALREADY_INSTALLED_CODES` и в тест, сохранив старые. |
| Кэш Chrome сменит имя папки | Не добавлять новые имена сверх трёх. Просмотр просто покажет меньше байт. |
| Файл кэша занят браузером | Он учитывается как пропущенный, операция продолжается. Браузер не закрывать из программы. |
| `schtasks /Create` с именем `\DeskKit\Backup` не создаёт папку задачи | Повтор с именем `DeskKit Backup` уже в `ScheduleService.apply`. Третье имя не придумывать. |
| Длина `/TR` | `quote_task_tr` бросает `ScheduleError`. Не укорачивать путь записью в `System32`. |
| Задача не срабатывает, пока пользователь не вошёл | Это выбранное поведение. Пароль в задачу не записывать, `/RL HIGHEST` не ставить. |
| Inno Setup 7.1.1 не кладёт `ISCC.exe` в `C:\Program Files\Inno Setup 7` | Шаг релиза падает. Не ставить Inno Setup 6 и не искать exe по всему диску в workflow. |
| `x64compatible` не принят компилятором | Заменить на `x64` в обеих директивах `Architectures*` и только в них. |
| Два рантайма раздувают установщик | Принято. Не склеивать exe и не переходить на onefile в v1. |
| Отмена не обрывает уже начатый `zipfile.write` одного большого файла | Принято. Токен проверяется между файлами. |
| Отмена winget убивает процесс, но установщик пакета мог остаться дочерним | `terminate` убивает только процесс winget. Дочерние msiexec не выслеживать. В журнале останется запись об остановке. |
| Tcl/Tk на Linux CI | Тесты не создают окно и не импортируют CustomTkinter. Ставить `python3-tk` в CI не нужно. |
| `import winreg` на Linux | Модуль `windows.py` падает сразу. Сервисы его не импортируют. |
| Профиль с другого ПК содержит чужие пути | Загрузка это разрешает. Запуск копии сообщит `Папка не найдена`. Установка программ от путей не зависит. |
| Пользователь выбирает папку с секретами | Копия именно для его документов. Шифрование вне рамок. Текст на экране копий про архив без пароля обязателен. |
| Частичная установка | Уже поставленные пакеты не снимаются. Код выхода 1, список по каждому пакету виден. |
| Покрытие окон | Намеренно выключено `omit`. Дыру не закрывать фиктивными тестами, которые создают `CTk` на сервере без дисплея. |
| Лицензия CustomTkinter в метаданных PyPI одновременно упоминает CC0 и MIT | Пакет остаётся зависимостью. Отдельный файл лицензий не собирать в v1. В установщике показывается лицензия самого DeskKit (MIT). |

Открытых вопросов, без ответа на которые нельзя писать код, нет. Не возвращаться к выбору PySide6, имени продукта, одного exe вместо двух и публикации в PyPI, пока v1 не собран по этому плану.
