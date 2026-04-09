"""
tests/unit/viewmodels/test_monitoring_vm.py
Tests for kuber/viewmodels/monitoring_vm.py
"""
from __future__ import annotations

import pytest
from kuber.core.kubernetes.metrics import NodeMetrics, PodMetrics
from kuber.core.kubernetes.events import EventInfo
from kuber.core.kubernetes.pods import PodInfo


_FAKE_POD_METRICS = [
    PodMetrics(name="pod-1", namespace="default", cpu_millicores=100, memory_mib=64),
]

_FAKE_NODE_METRICS = [
    NodeMetrics(name="node-1", cpu_millicores=500, memory_mib=1024),
]

_FAKE_EVENTS = [
    EventInfo(
        namespace="default", name="ev-1", type="Warning", reason="BackOff",
        message="Back-off pulling image", source="kubelet",
        involved_object="Pod/pod-1", count=5, age="2m",
    ),
]

_FAKE_PODS = [
    PodInfo(name="nginx-abc", namespace="default", status="Running",
            ready="1/1", restarts=0, node="node-1", image="nginx", age="5m"),
    PodInfo(name="redis-xyz", namespace="default", status="Running",
            ready="1/1", restarts=0, node="node-1", image="redis", age="3m"),
]


class TestMonitoringVMMetrics:
    def test_load_metrics_emits_signal(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.metrics_loaded, timeout=5000) as blocker:
            vm.load_metrics()

        data = blocker.args[0]
        assert len(data["pods"]) == 1
        assert len(data["nodes"]) == 1


class TestMonitoringVMEvents:
    def test_load_events_emits_signal(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_events",
            return_value=_FAKE_EVENTS,
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.events_loaded, timeout=5000) as blocker:
            vm.load_events()

        assert len(blocker.args[0]) == 1
        assert blocker.args[0][0].reason == "BackOff"


class TestMonitoringVMLogs:
    def test_load_logs_emits_signal(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.get_pod_logs",
            return_value="line1\nline2\n",
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.logs_loaded, timeout=5000) as blocker:
            vm.load_logs("pod-1", "default")

        assert "line1" in blocker.args[0]


class TestMonitoringVMNamespaces:
    def test_load_namespaces_emits_signal(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_namespaces",
            return_value=["default", "kube-system"],
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.namespaces_loaded, timeout=3000) as blocker:
            vm.load_namespaces()

        assert blocker.args[0] == ["default", "kube-system"]

    def test_load_namespaces_not_cancelled_by_load_metrics(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_namespaces",
            return_value=["default", "prod"],
        )
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.namespaces_loaded, timeout=3000) as blocker:
            vm.load_namespaces()
            vm.load_metrics()  # must NOT cancel namespace worker

        assert blocker.args[0] == ["default", "prod"]


class TestMonitoringVMPods:
    def test_load_pods_emits_signal(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_pods",
            return_value=_FAKE_PODS,
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.pods_loaded, timeout=3000) as blocker:
            vm.load_pods("default")

        assert len(blocker.args[0]) == 2
        assert blocker.args[0][0].name == "nginx-abc"

    def test_load_pods_not_cancelled_by_load_logs(self, qtbot, mocker) -> None:
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.list_pods",
            return_value=_FAKE_PODS,
        )
        mocker.patch(
            "kuber.viewmodels.monitoring_vm.get_pod_logs",
            return_value="log line",
        )
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel
        vm = MonitoringViewModel()

        with qtbot.waitSignal(vm.pods_loaded, timeout=3000) as blocker:
            vm.load_pods("default")
            vm.load_logs("pod-1", "default")  # must NOT cancel pods worker

        assert len(blocker.args[0]) == 2

