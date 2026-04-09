"""
tests/unit/services/test_monitoring_service.py
Tests for kuber/services/monitoring_service.py
"""
from __future__ import annotations

import pytest

from kuber.core.kubernetes.events import EventInfo
from kuber.core.kubernetes.metrics import NodeMetrics, PodMetrics


_FAKE_POD_METRICS = [
    PodMetrics(name="pod-1", namespace="default", cpu_millicores=100, memory_mib=64),
    PodMetrics(name="pod-2", namespace="default", cpu_millicores=200, memory_mib=128),
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
    EventInfo(
        namespace="default", name="ev-2", type="Normal", reason="Scheduled",
        message="Successfully assigned", source="scheduler",
        involved_object="Pod/pod-2", count=1, age="1m",
    ),
]


class TestMonitoringServiceMetrics:
    def test_get_pod_metrics_returns_list(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        pods = svc.get_pod_metrics("default")
        assert len(pods) == 2
        assert pods[0].name == "pod-1"

    def test_get_node_metrics_returns_list(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        nodes = svc.get_node_metrics()
        assert len(nodes) == 1
        assert nodes[0].cpu_millicores == 500

    def test_get_all_metrics_returns_dict(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        data = svc.get_all_metrics("default")
        assert "pods" in data
        assert "nodes" in data
        assert len(data["pods"]) == 2

    def test_cache_avoids_repeated_api_calls(self, mocker) -> None:
        mock_pods = mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService(cache_ttl=60)
        svc.get_pod_metrics("default")
        svc.get_pod_metrics("default")
        assert mock_pods.call_count == 1

    def test_force_refresh_bypasses_cache(self, mocker) -> None:
        mock_pods = mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService(cache_ttl=60)
        svc.get_pod_metrics("default")
        svc.get_pod_metrics("default", force=True)
        assert mock_pods.call_count == 2

    def test_invalidate_cache_forces_refresh(self, mocker) -> None:
        mock_pods = mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService(cache_ttl=60)
        svc.get_pod_metrics("default")
        svc.invalidate_cache()
        svc.get_pod_metrics("default")
        assert mock_pods.call_count == 2


class TestMonitoringServiceSummary:
    def test_get_summary_returns_aggregated_data(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=_FAKE_POD_METRICS,
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=_FAKE_NODE_METRICS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        summary = svc.get_summary("default")
        assert summary.pod_count == 2
        assert summary.node_count == 1
        assert summary.total_pod_cpu_millicores == 300
        assert summary.total_pod_memory_mib == 192
        assert summary.total_node_cpu_millicores == 500
        assert summary.avg_pod_cpu_millicores == 150.0

    def test_get_summary_empty_metrics(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_pod_metrics",
            return_value=[],
        )
        mocker.patch(
            "kuber.services.monitoring_service.list_node_metrics",
            return_value=[],
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        summary = svc.get_summary("default")
        assert summary.pod_count == 0
        assert summary.avg_pod_cpu_millicores == 0.0


class TestMonitoringServiceEvents:
    def test_get_events_returns_list(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_events",
            return_value=_FAKE_EVENTS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        events = svc.get_events("default")
        assert len(events) == 2

    def test_get_warning_events_filters(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.list_events",
            return_value=_FAKE_EVENTS,
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        warnings = svc.get_warning_events("default")
        assert len(warnings) == 1
        assert warnings[0].type == "Warning"


class TestMonitoringServiceLogs:
    def test_fetch_pod_logs_returns_text(self, mocker) -> None:
        mocker.patch(
            "kuber.services.monitoring_service.get_pod_logs",
            return_value="line1\nline2\n",
        )
        from kuber.services.monitoring_service import MonitoringService
        svc = MonitoringService()
        text = svc.fetch_pod_logs("pod-1", "default")
        assert "line1" in text

