from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypeVar

from deskkit.app_context import Context, build_context
from deskkit.cancel import CancellationToken
from deskkit.errors import (
    CancelledError,
    ConfirmationRequired,
    DeskKitError,
    ValidationError,
)
from deskkit.logging_setup import setup_logging
from deskkit.models import CleanupTargetId, InstallScope, InstallStatus
from deskkit.profile import ProfileStore, default_profile, profile_from_mapping
from deskkit.text import (
    backup_preview_text,
    backup_result_text,
    cleanup_preview_text,
    cleanup_result_text,
    confirmation_footer,
    install_preview_text,
    install_report_text,
    profile_summary_text,
    report_summary_text,
    schedule_preview_text,
    startup_action_text,
    startup_list_text,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="deskkit")
    parser.add_argument("-v", "--verbose", action="store_true")
    parser.add_argument("--profile", dest="profile_path")
    sub = parser.add_subparsers(dest="command", required=False)

    install = sub.add_parser("install")
    install_sub = install.add_subparsers(dest="install_cmd", required=True)
    install_sub.add_parser("list")
    for name in ("preview", "run"):
        cmd = install_sub.add_parser(name)
        cmd.add_argument("--preset", choices=["home", "office", "dev"])
        cmd.add_argument("--id", action="append", dest="ids", default=[])
        cmd.add_argument("--scope", choices=["user", "auto"], default="user")
        cmd.add_argument("--dry-run", action="store_true")
        if name == "run":
            cmd.add_argument("--yes", action="store_true")

    clean = sub.add_parser("clean")
    clean_sub = clean.add_subparsers(dest="clean_cmd", required=True)
    for name in ("preview", "run"):
        cmd = clean_sub.add_parser(name)
        cmd.add_argument(
            "--target",
            action="append",
            dest="targets",
            choices=[t.value for t in CleanupTargetId],
            default=[],
        )
        cmd.add_argument("--dry-run", action="store_true")
        if name == "run":
            cmd.add_argument("--yes", action="store_true")

    report = sub.add_parser("report")
    report_sub = report.add_subparsers(dest="report_cmd", required=True)
    report_sub.add_parser("show")
    report_save = report_sub.add_parser("save")
    report_save.add_argument("path")

    startup = sub.add_parser("startup")
    startup_sub = startup.add_subparsers(dest="startup_cmd", required=True)
    startup_sub.add_parser("list")
    for name in ("disable", "enable"):
        cmd = startup_sub.add_parser(name)
        cmd.add_argument("--id", required=True)
        cmd.add_argument("--dry-run", action="store_true")
        cmd.add_argument("--yes", action="store_true")

    backup = sub.add_parser("backup")
    backup_sub = backup.add_subparsers(dest="backup_cmd", required=True)
    for name in ("preview", "run"):
        cmd = backup_sub.add_parser(name)
        cmd.add_argument("--source", action="append", dest="sources", default=[])
        cmd.add_argument("--dest")
        cmd.add_argument("--keep", type=int, default=5)
        cmd.add_argument("--dry-run", action="store_true")
        if name == "run":
            cmd.add_argument("--yes", action="store_true")
    backup_schedule = backup_sub.add_parser("schedule")
    backup_schedule.add_argument("--dry-run", action="store_true")
    backup_schedule.add_argument("--yes", action="store_true")
    backup_unschedule = backup_sub.add_parser("unschedule")
    backup_unschedule.add_argument("--dry-run", action="store_true")
    backup_unschedule.add_argument("--yes", action="store_true")

    profile = sub.add_parser("profile")
    profile_sub = profile.add_subparsers(dest="profile_cmd", required=True)
    profile_sub.add_parser("path")
    profile_sub.add_parser("show")
    profile_sub.add_parser("init")
    profile_export = profile_sub.add_parser("export")
    profile_export.add_argument("path")
    profile_import = profile_sub.add_parser("import")
    profile_import.add_argument("path")
    profile_import.add_argument("--dry-run", action="store_true")
    profile_import.add_argument("--yes", action="store_true")
    profile_apply = profile_sub.add_parser("apply-install")
    profile_apply.add_argument("--dry-run", action="store_true")
    profile_apply.add_argument("--yes", action="store_true")

    return parser


def run(argv: list[str], context: Context | None = None) -> int:
    parser = build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as exc:
        code = exc.code
        return 0 if code is None else int(code)

    if context is None:
        try:
            context = build_context()
        except DeskKitError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    if getattr(args, "profile_path", None):
        context = _with_profile_path(context, Path(args.profile_path))
    setup_logging(context.paths.log_path, verbose=args.verbose)

    if args.command is None:
        parser.print_help()
        return 0

    cancel = CancellationToken()
    try:
        return _dispatch(args, context, cancel)
    except ConfirmationRequired as exc:
        print(str(exc), file=sys.stderr)
        return 3
    except CancelledError as exc:
        print(str(exc), file=sys.stderr)
        return 4
    except DeskKitError as exc:
        print(str(exc), file=sys.stderr)
        return 1


def _with_profile_path(context: Context, profile_path: Path) -> Context:
    from dataclasses import replace

    store = ProfileStore(profile_path)
    paths = replace(context.paths, profile_path=profile_path)
    return replace(context, paths=paths, profile_store=store)


def _dispatch(args: argparse.Namespace, context: Context, cancel: CancellationToken) -> int:
    if args.command == "install":
        return _cmd_install(args, context, cancel)
    if args.command == "clean":
        return _cmd_clean(args, context, cancel)
    if args.command == "report":
        return _cmd_report(args, context)
    if args.command == "startup":
        return _cmd_startup(args, context)
    if args.command == "backup":
        return _cmd_backup(args, context, cancel)
    if args.command == "profile":
        return _cmd_profile(args, context, cancel)
    return 1


def _install_ids_and_scope(
    args: argparse.Namespace, context: Context
) -> tuple[tuple[str, ...], InstallScope] | int:
    if args.preset and args.ids:
        print("Укажите набор или --id, не оба сразу.", file=sys.stderr)
        return 2  # type: ignore[return-value]
    if args.preset:
        ids = context.catalog.ids_for_preset(args.preset)
    elif args.ids:
        ids = tuple(args.ids)
    else:
        raise ValidationError("Не выбрано ни одной программы.")
    scope = InstallScope.USER if args.scope == "user" else InstallScope.AUTO
    return ids, scope


def _cmd_install(args: argparse.Namespace, context: Context, cancel: CancellationToken) -> int:
    if args.install_cmd == "list":
        for package in context.catalog.packages():
            presets = ",".join(package.presets) if package.presets else "-"
            print(f"{package.id}\t{package.name}\t{package.summary}\t{presets}")
        return 0
    resolved = _install_ids_and_scope(args, context)
    if isinstance(resolved, int):
        return resolved
    ids, scope = resolved
    if args.install_cmd == "preview":
        preview = context.installer.preview(ids, scope)
        text = install_preview_text(preview, include_footer=not args.dry_run)
        print(text, end="")
        return 0 if args.dry_run else 3
    return _mutating(
        preview_fn=lambda: install_preview_text(
            context.installer.preview(ids, scope), include_footer=True
        ),
        dry_run=args.dry_run,
        yes=args.yes,
        execute=lambda: context.installer.apply(
            ids, scope, dry_run=False, confirmed=True, cancel=cancel
        ),
        dry_execute=lambda: context.installer.apply(
            ids, scope, dry_run=True, confirmed=False, cancel=cancel
        ),
        on_success=lambda report: print(install_report_text(report), end=""),
        exit_from_result=_install_exit,
    )


def _install_exit(report: object) -> int:
    from deskkit.models import InstallReport

    assert isinstance(report, InstallReport)
    if report.cancelled:
        return 4
    if any(
        item.status in (InstallStatus.FAILED, InstallStatus.ADMIN_REQUIRED) for item in report.items
    ):
        return 1
    return 0


def _cmd_clean(args: argparse.Namespace, context: Context, cancel: CancellationToken) -> int:
    targets = _cleanup_targets(args, context)
    if args.clean_cmd == "preview":
        preview = context.cleanup.preview(targets)
        print(cleanup_preview_text(preview, include_footer=not args.dry_run), end="")
        return 0 if args.dry_run else 3
    return _mutating(
        preview_fn=lambda: cleanup_preview_text(
            context.cleanup.preview(targets), include_footer=True
        ),
        dry_run=args.dry_run,
        yes=args.yes,
        execute=lambda: context.cleanup.apply(
            targets, dry_run=False, confirmed=True, cancel=cancel
        ),
        dry_execute=lambda: context.cleanup.apply(
            targets, dry_run=True, confirmed=False, cancel=cancel
        ),
        on_success=lambda result: print(cleanup_result_text(result), end=""),
        exit_from_result=lambda result: 4 if result.cancelled else 0,
    )


def _cleanup_targets(args: argparse.Namespace, context: Context) -> tuple[CleanupTargetId, ...]:
    if args.targets:
        return tuple(CleanupTargetId(t) for t in args.targets)
    profile = context.profile_store.load()
    return profile.cleanup.targets


def _cmd_report(args: argparse.Namespace, context: Context) -> int:
    if args.report_cmd == "show":
        snapshot = context.report.collect()
        print(report_summary_text(snapshot), end="")
        return 0
    path = Path(args.path)
    suffix = path.suffix.lower()
    snapshot = context.report.collect()
    if suffix == ".html":
        context.report.write_html(snapshot, path)
    elif suffix == ".xlsx":
        context.report.write_xlsx(snapshot, path)
    else:
        print("Нужен файл .html или .xlsx.", file=sys.stderr)
        return 2
    print(f"Сохранено: {path}")
    return 0


def _cmd_startup(args: argparse.Namespace, context: Context) -> int:
    if args.startup_cmd == "list":
        print(startup_list_text(context.startup.list_entries()), end="")
        return 0
    entry_id = args.id
    action = "disable" if args.startup_cmd == "disable" else "enable"
    entries = {e.id: e for e in context.startup.list_entries()}
    entry = entries.get(entry_id)
    if entry is None:
        raise ValidationError("Запись автозагрузки не найдена.")
    preview_text = startup_action_text(entry, action) + "\n" + confirmation_footer() + "\n"
    if args.dry_run:
        context.startup.disable(
            entry_id, dry_run=True, confirmed=False
        ) if action == "disable" else context.startup.enable(
            entry_id, dry_run=True, confirmed=False
        )
        print(preview_text, end="")
        return 0
    if not args.yes:
        print(preview_text, end="")
        return 3
    if action == "disable":
        context.startup.disable(entry_id, dry_run=False, confirmed=True)
    else:
        context.startup.enable(entry_id, dry_run=False, confirmed=True)
    return 0


def _cmd_backup(args: argparse.Namespace, context: Context, cancel: CancellationToken) -> int:
    if args.backup_cmd == "schedule":
        profile = context.profile_store.load()
        if args.dry_run:
            text = schedule_preview_text(context.schedule.create_argv(profile.backup.schedule))
            print(text, end="")
            return 0
        text = schedule_preview_text(context.schedule.create_argv(profile.backup.schedule))
        if not args.yes:
            print(text + confirmation_footer() + "\n", end="")
            return 3
        try:
            context.schedule.apply(profile.backup.schedule, confirmed=True)
        except ValidationError as exc:
            print(str(exc), file=sys.stderr)
            return 1
        return 0

    if args.backup_cmd == "unschedule":
        if args.dry_run:
            print("Задача будет удалена, если она есть.\n", end="")
            return 0
        if not args.yes:
            print("Задача будет удалена, если она есть.\n" + confirmation_footer() + "\n", end="")
            return 3
        context.schedule.remove(confirmed=True)
        return 0

    resolved = _backup_args(args, context)
    if resolved is None:
        return 2
    sources, destination, keep = resolved
    sources_path = tuple(Path(s) for s in sources)
    dest_path = Path(destination)
    if args.backup_cmd == "preview":
        preview = context.backup.preview(sources_path, dest_path, keep)
        print(backup_preview_text(preview, include_footer=not args.dry_run), end="")
        return 0 if args.dry_run else 3

    return _mutating(
        preview_fn=lambda: backup_preview_text(
            context.backup.preview(sources_path, dest_path, keep), include_footer=True
        ),
        dry_run=args.dry_run,
        yes=args.yes,
        execute=lambda: context.backup.apply(
            sources_path, dest_path, keep, dry_run=False, confirmed=True, cancel=cancel
        ),
        dry_execute=lambda: context.backup.apply(
            sources_path, dest_path, keep, dry_run=True, confirmed=False, cancel=cancel
        ),
        on_success=lambda result: print(backup_result_text(result), end=""),
        exit_from_result=lambda result: 4 if result.cancelled else 0,
    )


def _backup_args(args: argparse.Namespace, context: Context) -> tuple[tuple[str, ...], str, int]:
    profile = context.profile_store.load()
    if args.sources:
        if not args.dest:
            print("Вместе с --source нужен --dest.", file=sys.stderr)
            return None  # type: ignore[return-value]
        return tuple(args.sources), args.dest, args.keep
    if not profile.backup.sources or not profile.backup.destination:
        raise ValidationError("Не выбраны папки для копии.")
    return profile.backup.sources, profile.backup.destination, profile.backup.keep_last


def _cmd_profile(args: argparse.Namespace, context: Context, cancel: CancellationToken) -> int:
    store = context.profile_store
    if args.profile_cmd == "path":
        print(context.paths.profile_path)
        return 0
    if args.profile_cmd == "show":
        print(profile_summary_text(store.load()), end="")
        return 0
    if args.profile_cmd == "init":
        if store.path.is_file():
            print("Профиль уже есть.", file=sys.stderr)
            return 1
        profile = default_profile()
        store.save(profile)
        print(context.paths.profile_path)
        return 0
    if args.profile_cmd == "export":
        target = Path(args.path)
        if target.exists():
            print("Файл уже есть.", file=sys.stderr)
            return 1
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(profile_summary_text(store.load()), encoding="utf-8")
        return 0
    if args.profile_cmd == "import":
        data = json.loads(Path(args.path).read_text(encoding="utf-8"))
        profile = profile_from_mapping(data)
        text = profile_summary_text(profile)
        if args.dry_run:
            print(text + "Режим просмотра: профиль не заменён.\n", end="")
            return 0
        if not args.yes:
            print(text + confirmation_footer() + "\n", end="")
            return 3
        store.save(profile)
        return 0
    profile = store.load()
    ids = profile.install.package_ids
    scope = profile.install.scope
    return _mutating(
        preview_fn=lambda: install_preview_text(
            context.installer.preview(ids, scope), include_footer=True
        ),
        dry_run=args.dry_run,
        yes=args.yes,
        execute=lambda: context.installer.apply(
            ids, scope, dry_run=False, confirmed=True, cancel=cancel
        ),
        dry_execute=lambda: context.installer.apply(
            ids, scope, dry_run=True, confirmed=False, cancel=cancel
        ),
        on_success=lambda report: print(install_report_text(report), end=""),
        exit_from_result=_install_exit,
    )


_T = TypeVar("_T")


def _mutating(
    *,
    preview_fn: Callable[[], str],
    dry_run: bool,
    yes: bool,
    execute: Callable[[], _T],
    dry_execute: Callable[[], _T],
    on_success: Callable[[_T], None],
    exit_from_result: Callable[[_T], int],
) -> int:
    if dry_run:
        result = dry_execute()
        on_success(result)
        return 0
    if not yes:
        print(preview_fn(), end="")
        return 3
    result = execute()
    on_success(result)
    return exit_from_result(result)
