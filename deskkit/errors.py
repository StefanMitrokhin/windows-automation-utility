from __future__ import annotations


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
