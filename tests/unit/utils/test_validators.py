"""
tests/unit/utils/test_validators.py
Tests for kuber/utils/validators.py (the 5 APP Requirements checks).
"""
from __future__ import annotations

import pytest

from kuber.utils.validators import (
    CheckStatus,
    PreflightReport,
    check_docker,
    check_git,
    check_internet_connectivity,
    check_kube_config,
    check_kubernetes_permissions,
    run_preflight_checks,
)


class TestCheckKubeConfig:
    def test_check_kube_config_ok_when_file_exists(self, mocker) -> None:
        """Returns OK when kubeconfig loads successfully."""
        from kuber.config.kube_config import KubeConfigInfo, KubeContext
        mocker.patch(
            "kuber.utils.validators.load_kube_config",
            return_value=KubeConfigInfo(
                contexts=[KubeContext(name="ctx", cluster="c", user="u")],
                active_context_name="ctx",
            ),
        )
        result = check_kube_config()
        assert result.status == CheckStatus.OK

    def test_check_kube_config_error_when_file_missing(self, mocker) -> None:
        """Returns ERROR when kubeconfig cannot be loaded."""
        from kuber.core.exceptions import KuberConfigError
        mocker.patch(
            "kuber.utils.validators.load_kube_config",
            side_effect=KuberConfigError("not found"),
        )
        result = check_kube_config()
        assert result.status == CheckStatus.ERROR


class TestCheckInternetConnectivity:
    def test_check_internet_ok_when_reachable(self, mocker) -> None:
        """Returns OK when internet is reachable."""
        mocker.patch(
            "kuber.utils.validators.is_internet_available", return_value=True
        )
        result = check_internet_connectivity()
        assert result.status == CheckStatus.OK

    def test_check_internet_warning_when_not_reachable(self, mocker) -> None:
        """Returns WARNING when internet is not reachable."""
        mocker.patch(
            "kuber.utils.validators.is_internet_available", return_value=False
        )
        result = check_internet_connectivity()
        assert result.status == CheckStatus.WARNING


class TestCheckDocker:
    def test_check_docker_ok_when_running_and_version_ok(self, mocker) -> None:
        """Returns OK when Docker is running with a supported version."""
        from kuber.core.docker.client import DockerStatus
        mocker.patch(
            "kuber.utils.validators.check_docker_status",
            return_value=DockerStatus(is_running=True, version="24.0.0", version_ok=True),
        )
        result = check_docker()
        assert result.status == CheckStatus.OK

    def test_check_docker_error_when_not_running(self, mocker) -> None:
        """Returns ERROR when the Docker daemon is not running."""
        from kuber.core.docker.client import DockerStatus
        mocker.patch(
            "kuber.utils.validators.check_docker_status",
            return_value=DockerStatus(is_running=False, version="", version_ok=False),
        )
        result = check_docker()
        assert result.status == CheckStatus.ERROR

    def test_check_docker_warning_when_version_outdated(self, mocker) -> None:
        """Returns WARNING when Docker is running but version is below minimum."""
        from kuber.core.docker.client import DockerStatus
        mocker.patch(
            "kuber.utils.validators.check_docker_status",
            return_value=DockerStatus(is_running=True, version="19.0.0", version_ok=False),
        )
        result = check_docker()
        assert result.status == CheckStatus.WARNING


class TestCheckGit:
    def test_check_git_ok_when_configured(self, mocker) -> None:
        """Returns OK when Git is installed, version is ok, and user is configured."""
        from kuber.core.git.client import GitStatus
        mocker.patch(
            "kuber.utils.validators.check_git_status",
            return_value=GitStatus(
                is_installed=True,
                version="2.45.0",
                version_ok=True,
                user_name="Dev",
                user_email="dev@example.com",
                config_ok=True,
            ),
        )
        result = check_git()
        assert result.status == CheckStatus.OK

    def test_check_git_error_when_not_installed(self, mocker) -> None:
        """Returns ERROR when Git is not installed."""
        from kuber.core.git.client import GitStatus
        mocker.patch(
            "kuber.utils.validators.check_git_status",
            return_value=GitStatus(is_installed=False, version="", version_ok=False),
        )
        result = check_git()
        assert result.status == CheckStatus.ERROR


class TestRunPreflightChecks:
    def test_run_preflight_checks_returns_5_results(self, mocker) -> None:
        """Pre-flight always returns exactly 5 check results."""
        from kuber.config.kube_config import KubeConfigInfo, KubeContext
        from kuber.core.docker.client import DockerStatus
        from kuber.core.git.client import GitStatus

        mocker.patch(
            "kuber.utils.validators.load_kube_config",
            return_value=KubeConfigInfo(
                contexts=[KubeContext(name="c", cluster="c", user="u")],
                active_context_name="c",
            ),
        )
        mocker.patch("kuber.utils.validators.validate_cluster_access")
        mocker.patch("kuber.utils.validators.is_internet_available", return_value=True)
        mocker.patch(
            "kuber.utils.validators.check_docker_status",
            return_value=DockerStatus(is_running=True, version="24.0", version_ok=True),
        )
        mocker.patch(
            "kuber.utils.validators.check_git_status",
            return_value=GitStatus(
                is_installed=True, version="2.45", version_ok=True,
                user_name="Dev", user_email="d@e.com", config_ok=True,
            ),
        )

        report = run_preflight_checks()
        assert len(report.results) == 5

    def test_run_preflight_all_ok_sets_all_ok_true(self, mocker) -> None:
        """all_ok property is True when every check passes."""
        from kuber.utils import validators
        from kuber.utils.validators import CheckResult

        for attr in [
            "check_kube_config",
            "check_kubernetes_permissions",
            "check_internet_connectivity",
            "check_docker",
            "check_git",
        ]:
            mocker.patch.object(
                validators, attr,
                return_value=CheckResult(attr, CheckStatus.OK, "ok"),
            )

        report = validators.run_preflight_checks()
        assert report.all_ok is True

