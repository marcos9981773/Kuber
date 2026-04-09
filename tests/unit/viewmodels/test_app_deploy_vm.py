"""
tests/unit/viewmodels/test_app_deploy_vm.py
Tests for kuber/viewmodels/app_deploy_vm.py
"""
from __future__ import annotations

import pytest
from kuber.viewmodels.app_deploy_vm import AppDeployViewModel, DeployMode, DeploySpec


class TestAppDeployVMDocker:
    """Tests for Docker image deployment mode."""

    def test_docker_deploy_emits_completed(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.app_deploy_vm.apply_manifest")
        vm = AppDeployViewModel()

        spec = DeploySpec(
            mode=DeployMode.DOCKER_IMAGE,
            namespace="default",
            image="nginx",
            tag="1.25",
            replicas=2,
        )
        with qtbot.waitSignal(vm.deploy_completed, timeout=5000) as blocker:
            vm.execute(spec)

        assert "nginx" in blocker.args[0]

    def test_docker_deploy_dry_run_no_apply(self, qtbot, mocker) -> None:
        mock_apply = mocker.patch("kuber.viewmodels.app_deploy_vm.apply_manifest")
        vm = AppDeployViewModel()

        spec = DeploySpec(
            mode=DeployMode.DOCKER_IMAGE,
            image="redis",
            dry_run=True,
        )
        with qtbot.waitSignal(vm.deploy_completed, timeout=5000) as blocker:
            vm.execute(spec)

        mock_apply.assert_not_called()
        assert "DRY RUN" in blocker.args[0]


class TestAppDeployVMHelm:
    """Tests for Helm chart deployment mode."""

    def test_helm_deploy_emits_completed(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.app_deploy_vm.install_chart", return_value="ok")
        vm = AppDeployViewModel()

        spec = DeploySpec(
            mode=DeployMode.HELM_CHART,
            chart="bitnami/nginx",
            release_name="web",
            namespace="default",
        )
        with qtbot.waitSignal(vm.deploy_completed, timeout=5000) as blocker:
            vm.execute(spec)

        assert "web" in blocker.args[0]


class TestAppDeployVMManifest:
    """Tests for manifest deployment mode."""

    def test_manifest_deploy_emits_completed(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.app_deploy_vm.apply_manifest")
        vm = AppDeployViewModel()

        yaml_text = (
            "apiVersion: apps/v1\n"
            "kind: Deployment\n"
            "metadata:\n"
            "  name: my-app\n"
            "spec:\n"
            "  replicas: 1\n"
        )
        spec = DeploySpec(
            mode=DeployMode.MANIFEST,
            manifest_yaml=yaml_text,
            namespace="default",
        )
        with qtbot.waitSignal(vm.deploy_completed, timeout=5000) as blocker:
            vm.execute(spec)

        assert "my-app" in blocker.args[0]

    def test_manifest_dry_run_no_apply(self, qtbot, mocker) -> None:
        mock_apply = mocker.patch("kuber.viewmodels.app_deploy_vm.apply_manifest")
        vm = AppDeployViewModel()

        yaml_text = "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: x\n"
        spec = DeploySpec(
            mode=DeployMode.MANIFEST,
            manifest_yaml=yaml_text,
            dry_run=True,
        )
        with qtbot.waitSignal(vm.deploy_completed, timeout=5000) as blocker:
            vm.execute(spec)

        mock_apply.assert_not_called()
        assert "DRY RUN" in blocker.args[0]

    def test_deploy_error_emits_failed(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.app_deploy_vm.apply_manifest",
            side_effect=Exception("API error"),
        )
        vm = AppDeployViewModel()

        yaml_text = "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: bad\n"
        spec = DeploySpec(
            mode=DeployMode.MANIFEST,
            manifest_yaml=yaml_text,
        )
        with qtbot.waitSignal(vm.deploy_failed, timeout=5000) as blocker:
            vm.execute(spec)

        assert "API error" in blocker.args[0]

