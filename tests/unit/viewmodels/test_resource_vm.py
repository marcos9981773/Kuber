"""
tests/unit/viewmodels/test_resource_vm.py
Tests for kuber/viewmodels/resource_vm.py and concrete subclasses.
"""
from __future__ import annotations

import pytest
from dataclasses import dataclass

from kuber.core.kubernetes.pods import PodInfo
from kuber.core.kubernetes.deployments import DeploymentInfo
from kuber.core.kubernetes.services import ServiceInfo
from kuber.core.kubernetes.configmaps import ConfigMapInfo


# ── Fake data ────────────────────────────────────────────────────────────────

_FAKE_PODS = [
    PodInfo(name="pod-1", namespace="default", status="Running",
            ready="1/1", restarts=0, node="node-1", image="nginx:1.25", age="5m"),
    PodInfo(name="pod-2", namespace="default", status="Pending",
            ready="0/1", restarts=2, node="", image="redis:7", age="10m"),
]

_FAKE_DEPLOYS = [
    DeploymentInfo(name="web", namespace="default", replicas=3,
                   ready_replicas=3, image="nginx:1.25", age="1d", strategy="RollingUpdate"),
]

_FAKE_SERVICES = [
    ServiceInfo(name="web-svc", namespace="default", type="ClusterIP",
                cluster_ip="10.0.0.1", external_ip="<none>", ports=[], age="2d"),
]

_FAKE_CONFIGMAPS = [
    ConfigMapInfo(name="app-config", namespace="default",
                  data_keys=["key1", "key2"], age="3d", data={"key1": "v1", "key2": "v2"}),
]


# ── ResourceViewModel (namespace loading) ───────────────────────────────────

class TestResourceViewModelNamespaces:
    """Regression: load_namespaces must not be cancelled by load_items."""

    def test_load_namespaces_emits_namespaces_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.resource_vm.list_namespaces",
            return_value=["default", "kube-system"],
        )
        mocker.patch("kuber.viewmodels.pod_vm.list_pods", return_value=_FAKE_PODS)
        from kuber.viewmodels.pod_vm import PodViewModel
        vm = PodViewModel()

        with qtbot.waitSignal(vm.namespaces_loaded, timeout=3000) as blocker:
            vm.load_namespaces()
            vm.load_items()  # must NOT cancel the namespace worker

        assert blocker.args[0] == ["default", "kube-system"]


# ── PodViewModel tests ──────────────────────────────────────────────────────

class TestPodViewModel:
    def test_load_items_emits_items_loaded(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.pod_vm.list_pods", return_value=_FAKE_PODS)
        mocker.patch(
            "kuber.viewmodels.resource_vm.list_namespaces", return_value=["default"]
        )
        from kuber.viewmodels.pod_vm import PodViewModel
        vm = PodViewModel()

        with qtbot.waitSignal(vm.items_loaded, timeout=3000) as blocker:
            vm.load_items()

        assert len(blocker.args[0]) == 2

    def test_delete_item_emits_item_deleted(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.pod_vm.delete_pod")
        mocker.patch("kuber.viewmodels.pod_vm.list_pods", return_value=[])
        from kuber.viewmodels.pod_vm import PodViewModel
        vm = PodViewModel()

        with qtbot.waitSignal(vm.item_deleted, timeout=3000) as blocker:
            vm.delete_item("pod-1", "default")

        assert blocker.args[0] == "pod-1"


# ── DeploymentViewModel tests ───────────────────────────────────────────────

class TestDeploymentViewModel:
    def test_load_items_emits_items_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.deployment_vm.list_deployments",
            return_value=_FAKE_DEPLOYS,
        )
        from kuber.viewmodels.deployment_vm import DeploymentViewModel
        vm = DeploymentViewModel()

        with qtbot.waitSignal(vm.items_loaded, timeout=3000) as blocker:
            vm.load_items()

        assert len(blocker.args[0]) == 1
        assert blocker.args[0][0].name == "web"

    def test_scale_emits_action_completed(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.deployment_vm.scale_deployment", return_value=None)
        mocker.patch(
            "kuber.viewmodels.deployment_vm.list_deployments", return_value=[]
        )
        from kuber.viewmodels.deployment_vm import DeploymentViewModel
        vm = DeploymentViewModel()

        with qtbot.waitSignal(vm.action_completed, timeout=3000):
            vm.scale("web", "default", 5)


# ── ServiceViewModel tests ──────────────────────────────────────────────────

class TestServiceViewModel:
    def test_load_items_emits_items_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.service_vm.list_services",
            return_value=_FAKE_SERVICES,
        )
        from kuber.viewmodels.service_vm import ServiceViewModel
        vm = ServiceViewModel()

        with qtbot.waitSignal(vm.items_loaded, timeout=3000) as blocker:
            vm.load_items()

        assert blocker.args[0][0].name == "web-svc"


# ── ConfigMapViewModel tests ────────────────────────────────────────────────

class TestConfigMapViewModel:
    def test_load_items_emits_items_loaded(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.configmap_vm.list_configmaps",
            return_value=_FAKE_CONFIGMAPS,
        )
        from kuber.viewmodels.configmap_vm import ConfigMapViewModel
        vm = ConfigMapViewModel()

        with qtbot.waitSignal(vm.items_loaded, timeout=3000) as blocker:
            vm.load_items()

        assert blocker.args[0][0].name == "app-config"

    def test_save_data_emits_action_completed(self, qtbot, mocker) -> None:
        mocker.patch("kuber.viewmodels.configmap_vm.update_configmap")
        mocker.patch(
            "kuber.viewmodels.configmap_vm.list_configmaps", return_value=[]
        )
        from kuber.viewmodels.configmap_vm import ConfigMapViewModel
        vm = ConfigMapViewModel()

        with qtbot.waitSignal(vm.action_completed, timeout=3000):
            vm.save_data("app-config", "default", {"k": "v"})

