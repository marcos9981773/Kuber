"""
kuber/core/exceptions.py
Custom exception hierarchy for Kuber.

All exceptions raised by core modules MUST be subclasses of KuberError.
ViewModels catch these and emit user-friendly messages via signals.
"""
from __future__ import annotations


class KuberError(Exception):
    """Base exception for all Kuber domain errors."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message)
        self.message = message
        self.details = details

    def __str__(self) -> str:
        if self.details:
            return f"{self.message} — {self.details}"
        return self.message


# ──────────────────────────────────────────────
# Kubernetes errors
# ──────────────────────────────────────────────

class KuberApiError(KuberError):
    """Raised when the Kubernetes API returns an unexpected error."""

    def __init__(self, message: str, status_code: int = 0, details: str = "") -> None:
        super().__init__(message, details)
        self.status_code = status_code


class KuberPermissionError(KuberApiError):
    """Raised when the user lacks permission to perform an operation (HTTP 403)."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message, status_code=403, details=details)


class KuberNotFoundError(KuberApiError):
    """Raised when a requested Kubernetes resource does not exist (HTTP 404)."""

    def __init__(self, message: str, details: str = "") -> None:
        super().__init__(message, status_code=404, details=details)


class KuberConnectionError(KuberError):
    """Raised when the Kubernetes API server is unreachable."""


class KuberConfigError(KuberError):
    """Raised when the kubeconfig file is missing, malformed, or invalid."""


# ──────────────────────────────────────────────
# Docker errors
# ──────────────────────────────────────────────

class KuberDockerError(KuberError):
    """Base class for Docker-related errors."""


class KuberDockerNotRunningError(KuberDockerError):
    """Raised when the Docker daemon is not running."""


class KuberDockerVersionError(KuberDockerError):
    """Raised when the installed Docker version is below the minimum required."""


# ──────────────────────────────────────────────
# Git errors
# ──────────────────────────────────────────────

class KuberGitError(KuberError):
    """Base class for Git-related errors."""


class KuberGitConfigError(KuberGitError):
    """Raised when Git is not configured or the config is invalid."""


class KuberGitAccessError(KuberGitError):
    """Raised when the user cannot access the required repository."""


# ──────────────────────────────────────────────
# Helm errors
# ──────────────────────────────────────────────

class KuberHelmError(KuberError):
    """Base class for Helm-related errors."""


# ──────────────────────────────────────────────
# Validation errors
# ──────────────────────────────────────────────

class KuberValidationError(KuberError):
    """Raised when input validation fails (e.g., invalid manifest YAML)."""


# ──────────────────────────────────────────────
# Backup / Restore errors
# ──────────────────────────────────────────────

class KuberBackupError(KuberError):
    """Raised when a backup or restore operation fails."""

