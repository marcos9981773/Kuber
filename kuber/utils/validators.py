"""
kuber/utils/validators.py
Pre-flight validators for the 5 APP Requirements.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path

from kuber.config.kube_config import load_kube_config, validate_cluster_access
from kuber.constants import KUBE_CONFIG_DEFAULT, MIN_DOCKER_VERSION, MIN_GIT_VERSION
from kuber.core.docker.client import check_docker_status
from kuber.core.git.client import check_git_status
from kuber.utils.network import is_internet_available

logger = logging.getLogger(__name__)


class CheckStatus(Enum):
    OK = auto()
    WARNING = auto()
    ERROR = auto()


@dataclass
class CheckResult:
    """Result of a single pre-flight check."""

    name: str
    status: CheckStatus
    message: str
    details: str = ""
    fix_hint: str = ""


@dataclass
class PreflightReport:
    """Aggregated result of all pre-flight checks."""

    results: list[CheckResult] = field(default_factory=list)

    @property
    def all_ok(self) -> bool:
        return all(r.status == CheckStatus.OK for r in self.results)

    @property
    def has_errors(self) -> bool:
        return any(r.status == CheckStatus.ERROR for r in self.results)

    @property
    def errors(self) -> list[CheckResult]:
        return [r for r in self.results if r.status == CheckStatus.ERROR]


def check_kube_config(config_path: Path = KUBE_CONFIG_DEFAULT) -> CheckResult:
    """
    Requirement 1: Load kubernetes config file from user default location.

    Verifies the kubeconfig file exists and is parseable.
    """
    try:
        info = load_kube_config(config_path)
        context_count = len(info.contexts)
        return CheckResult(
            name="Kubernetes Config",
            status=CheckStatus.OK,
            message=f"Kubeconfig loaded — {context_count} context(s) found.",
        )
    except Exception as exc:
        return CheckResult(
            name="Kubernetes Config",
            status=CheckStatus.ERROR,
            message="Kubeconfig file not found or invalid.",
            details=str(exc),
            fix_hint=(
                f"Ensure '{config_path}' exists. "
                "Run 'kubectl config view' to verify your configuration."
            ),
        )


def check_kubernetes_permissions() -> CheckResult:
    """
    Requirement 2: Ensure the user has necessary permissions to access Kubernetes resources.
    """
    try:
        validate_cluster_access()
        return CheckResult(
            name="Kubernetes Permissions",
            status=CheckStatus.OK,
            message="Kubernetes API accessible with required permissions.",
        )
    except Exception as exc:
        return CheckResult(
            name="Kubernetes Permissions",
            status=CheckStatus.ERROR,
            message="Cannot access the Kubernetes API.",
            details=str(exc),
            fix_hint=(
                "Verify your kubeconfig credentials and RBAC permissions. "
                "Contact your cluster administrator if you lack access."
            ),
        )


def check_internet_connectivity() -> CheckResult:
    """
    Requirement 3: Verify that the user has a working internet connection.
    """
    if is_internet_available():
        return CheckResult(
            name="Internet Connectivity",
            status=CheckStatus.OK,
            message="Internet connection available.",
        )
    return CheckResult(
        name="Internet Connectivity",
        status=CheckStatus.WARNING,
        message="No internet connection detected.",
        details="Image pulls and remote registry access will not be available.",
        fix_hint="Check your network connection and proxy settings.",
    )


def check_docker() -> CheckResult:
    """
    Requirement 4: Check that the user has a compatible version of Docker installed and running.
    """

    status = check_docker_status()
    if not status.is_running:
        return CheckResult(
            name="Docker",
            status=CheckStatus.ERROR,
            message="Docker daemon is not running.",
            fix_hint="Start Docker Desktop or run 'dockerd' and try again.",
        )
    if not status.version_ok:
        min_str = ".".join(str(v) for v in MIN_DOCKER_VERSION)
        return CheckResult(
            name="Docker",
            status=CheckStatus.WARNING,
            message=f"Docker version {status.version} is below the recommended {min_str}.",
            fix_hint=f"Upgrade Docker to version {min_str} or later.",
        )
    return CheckResult(
        name="Docker",
        status=CheckStatus.OK,
        message=f"Docker {status.version} is running.",
    )


def check_git() -> CheckResult:
    """
    Requirement 5: Validate that the user has a valid Git configuration.
    """
    status = check_git_status()
    if not status.is_installed:
        return CheckResult(
            name="Git",
            status=CheckStatus.ERROR,
            message="Git is not installed.",
            fix_hint="Install Git 2.39+ from https://git-scm.com/",
        )
    if not status.version_ok:
        min_str = ".".join(str(v) for v in MIN_GIT_VERSION)
        return CheckResult(
            name="Git",
            status=CheckStatus.WARNING,
            message=f"Git version {status.version} is below the recommended {min_str}.",
            fix_hint=f"Upgrade Git to version {min_str} or later.",
        )
    if not status.config_ok:
        return CheckResult(
            name="Git",
            status=CheckStatus.WARNING,
            message="Git user.name or user.email is not configured.",
            fix_hint=(
                "Run: git config --global user.name 'Your Name' && "
                "git config --global user.email 'you@example.com'"
            ),
        )
    return CheckResult(
        name="Git",
        status=CheckStatus.OK,
        message=f"Git {status.version} configured for {status.user_email}.",
    )


def run_preflight_checks(
    config_path: Path = KUBE_CONFIG_DEFAULT,
) -> PreflightReport:
    """
    Run all 5 pre-flight checks and return an aggregated report.

    Args:
        config_path: Path to the kubeconfig file.

    Returns:
        :class:`PreflightReport` with individual check results.
    """
    checks = [
        check_kube_config(config_path),
        check_kubernetes_permissions(),
        check_internet_connectivity(),
        check_docker(),
        check_git(),
    ]
    for result in checks:
        icon = "✅" if result.status == CheckStatus.OK else (
            "⚠️" if result.status == CheckStatus.WARNING else "❌"
        )
        logger.info(f"{icon} [{result.name}] {result.message}")

    return PreflightReport(results=checks)

