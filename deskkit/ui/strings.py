from __future__ import annotations

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
PROFILE_HINT = (
    "Применение профиля ставит только отмеченные программы. Очистка и копия сами не запускаются."
)
WINDOWS_TEMP_HINT = "Может потребовать права администратора. Файлы без доступа будут пропущены."
TEMP_AGE_HINT = "Файлы во временных папках моложе 24 часов не удаляются."
BACKUP_PLAIN_HINT = "Архив без пароля. Храните его на своём диске. Распаковка — вручную, мастера восстановления нет."
SCHEDULE_LOGIN_HINT = "Задача выполняется, когда вы вошли в систему. Пароль нигде не записывается."
ELEVATE_HINT = "Общий реестр и общая папка автозагрузки меняются только с правами администратора."
EMPTY_SELECTION = "Не выбрано ни одной программы."
