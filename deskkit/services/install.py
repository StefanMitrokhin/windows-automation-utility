from __future__ import annotations

import logging
from collections.abc import Sequence

from deskkit.cancel import CancellationToken
from deskkit.catalog import Catalog
from deskkit.errors import (
    CancelledError,
    ConfirmationRequired,
    ValidationError,
    WingetNotFoundError,
)
from deskkit.models import (
    InstallItemResult,
    InstallPreview,
    InstallReport,
    InstallScope,
    InstallStatus,
)
from deskkit.platform.commands import WINGET_TIMEOUT_S, winget_install_args
from deskkit.platform.protocols import CommandRunner
from deskkit.text import output_tail

ALREADY_INSTALLED_CODES: frozenset[int] = frozenset({-1978335135, -1978334963, -1978335189})
NO_APPLICABLE_INSTALLER: int = -1978335216
COMMAND_REQUIRES_ADMIN: int = -1978335207

_LOG = logging.getLogger("deskkit.install")


class InstallService:
    def __init__(
        self,
        catalog: Catalog,
        runner: CommandRunner,
        winget_exe: str | None,
    ) -> None:
        self._catalog = catalog
        self._runner = runner
        self._winget_exe = winget_exe

    def winget_path(self) -> str | None:
        return self._winget_exe

    def preview(self, package_ids: Sequence[str], scope: InstallScope) -> InstallPreview:
        packages = self._catalog.require_ids(package_ids)
        return InstallPreview(
            package_ids=tuple(p.id for p in packages),
            names=tuple(p.name for p in packages),
            scope=scope,
            winget_found=self._winget_exe is not None,
        )

    def apply(
        self,
        package_ids: Sequence[str],
        scope: InstallScope,
        *,
        dry_run: bool,
        confirmed: bool,
        cancel: CancellationToken,
    ) -> InstallReport:
        packages = self._catalog.require_ids(package_ids)
        if not packages:
            raise ValidationError("Не выбрано ни одной программы.")
        if self._winget_exe is None:
            raise WingetNotFoundError(
                "Не найден winget. Установите «Установщик приложений» из Microsoft Store."
            )
        if dry_run:
            items = tuple(
                InstallItemResult(
                    package_id=p.id,
                    name=p.name,
                    status=InstallStatus.SUCCESS,
                    exit_code=None,
                    message="просмотр",
                )
                for p in packages
            )
            return InstallReport(items=items, dry_run=True, cancelled=False)
        if not confirmed:
            raise ConfirmationRequired("Нужно подтверждение.")

        items: list[InstallItemResult] = []
        cancelled = False
        winget = self._winget_exe
        try:
            for package in packages:
                cancel.raise_if_cancelled()
                status, exit_code, message = self._install_one(
                    winget, package.id, package.name, scope, cancel
                )
                items.append(
                    InstallItemResult(
                        package_id=package.id,
                        name=package.name,
                        status=status,
                        exit_code=exit_code,
                        message=message,
                    )
                )
        except CancelledError:
            cancelled = True

        return InstallReport(items=tuple(items), dry_run=False, cancelled=cancelled)

    def _install_one(
        self,
        winget: str,
        package_id: str,
        name: str,
        scope: InstallScope,
        cancel: CancellationToken,
    ) -> tuple[InstallStatus, int | None, str]:
        _LOG.info("установка %s", package_id)
        args = winget_install_args(winget, package_id, scope)
        result = self._runner.run(args, WINGET_TIMEOUT_S)
        cancel.raise_if_cancelled()
        if result.cancelled:
            raise CancelledError("Остановлено.")
        if result.timed_out:
            status = InstallStatus.FAILED
            message = "превышено время ожидания (30 минут)"
            _LOG.info("результат %s %s", package_id, status.value)
            return status, result.exit_code, message
        code = result.exit_code or 0
        if code == 0:
            status = InstallStatus.SUCCESS
            message = "установлено"
        elif code in ALREADY_INSTALLED_CODES:
            status = InstallStatus.SKIPPED_INSTALLED
            message = "уже установлен, пропуск"
        elif code == COMMAND_REQUIRES_ADMIN:
            status = InstallStatus.ADMIN_REQUIRED
            message = "нужны права администратора"
        elif code == NO_APPLICABLE_INSTALLER and scope == InstallScope.USER:
            retry_args = winget_install_args(winget, package_id, InstallScope.AUTO)
            retry = self._runner.run(retry_args, WINGET_TIMEOUT_S)
            cancel.raise_if_cancelled()
            if retry.cancelled:
                raise CancelledError("Остановлено.")
            if retry.exit_code == 0:
                status = InstallStatus.SUCCESS
                message = "установлено"
                code = 0
            elif retry.exit_code == NO_APPLICABLE_INSTALLER:
                status = InstallStatus.FAILED
                message = "нет подходящего установщика"
                code = retry.exit_code
            else:
                status = InstallStatus.FAILED
                message = output_tail(retry.stdout, retry.stderr)
                code = retry.exit_code
        elif code == NO_APPLICABLE_INSTALLER:
            status = InstallStatus.FAILED
            message = "нет подходящего установщика"
        else:
            status = InstallStatus.FAILED
            message = output_tail(result.stdout, result.stderr)
        _LOG.info("результат %s %s", package_id, status.value)
        _LOG.debug("stdout %s", result.stdout)
        return status, code, message
