"""
tests/unit/core/kubernetes/test_pods.py
Tests for kuber/core/kubernetes/pods.py
"""
from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest

from kuber.core.exceptions import KuberNotFoundError
from kuber.core.kubernetes.pods import PodInfo, delete_pod, get_pod, list_pods


def _make_pod(
    name: str = "pod-1",
    namespace: str = "default",
    phase: str = "Running",
    node_name: str = "node-1",
    ready: bool = True,
    restart_count: int = 0,
    image: str = "nginx:1.25",
    creation_timestamp: datetime | None = None,
) -> MagicMock:
    pod = MagicMock()
    pod.metadata.name = name
    pod.metadata.namespace = namespace
    pod.metadata.creation_timestamp = creation_timestamp

    pod.status.phase = phase
    pod.status.container_statuses = [
        MagicMock(ready=ready, restart_count=restart_count)
    ]

    container = MagicMock()
    container.image = image
    pod.spec.containers = [container]
    pod.spec.node_name = node_name

    return pod


class TestListPods:
    """Tests for list_pods()."""

    def test_list_pods_namespaced_returns_pod_info_list(self, mocker) -> None:
        """list_namespaced_pod is called when namespace is not 'all'."""
        mock_pod = _make_pod()
        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        mock_api.list_namespaced_pod.assert_called_once()
        mock_api.list_pod_for_all_namespaces.assert_not_called()
        assert len(pods) == 1
        assert pods[0].name == "pod-1"
        assert pods[0].namespace == "default"

    def test_list_pods_all_namespaces_calls_correct_api(self, mocker) -> None:
        """list_pod_for_all_namespaces is called when namespace == 'all'."""
        mock_pod = _make_pod(namespace="kube-system")
        mock_api = MagicMock()
        mock_api.list_pod_for_all_namespaces.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="all")

        mock_api.list_pod_for_all_namespaces.assert_called_once()
        mock_api.list_namespaced_pod.assert_not_called()
        assert len(pods) == 1
        assert pods[0].namespace == "kube-system"

    def test_list_pods_node_uses_spec_node_name(self, mocker) -> None:
        """node field is populated from spec.node_name, not status.host_ip."""
        mock_pod = _make_pod(node_name="worker-node-3")
        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        assert pods[0].node == "worker-node-3"

    def test_list_pods_ready_count_correct(self, mocker) -> None:
        """ready field reflects the number of ready containers."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "pod-x"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp = None
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = [
            MagicMock(ready=True, restart_count=0),
            MagicMock(ready=False, restart_count=1),
        ]
        container1 = MagicMock()
        container1.image = "nginx:1.25"
        container2 = MagicMock()
        container2.image = "sidecar:latest"
        mock_pod.spec.containers = [container1, container2]
        mock_pod.spec.node_name = "node-1"

        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        assert pods[0].ready == "1/2"
        assert pods[0].restarts == 1

    def test_list_pods_handles_none_spec(self, mocker) -> None:
        """Pods with no spec (e.g., partially initialised) don't raise."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "partial-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp = None
        mock_pod.status.phase = "Pending"
        mock_pod.status.container_statuses = None
        mock_pod.spec = None

        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        assert len(pods) == 1
        assert pods[0].node == ""
        assert pods[0].ready == "0/0"

    def test_list_pods_unknown_phase_when_status_none(self, mocker) -> None:
        """status field defaults to 'Unknown' when pod.status is None."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "ghost-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp = None
        mock_pod.status = None
        mock_pod.spec = None

        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        assert pods[0].status == "Unknown"

    def test_list_pods_age_computed(self, mocker) -> None:
        """age field is a non-empty string when creation_timestamp is set."""
        ts = datetime(2026, 4, 9, 10, 0, 0, tzinfo=timezone.utc)
        mock_pod = _make_pod(creation_timestamp=ts)
        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        assert pods[0].age != ""

    def test_list_pods_multiple_images_joined(self, mocker) -> None:
        """image field concatenates all container images with ', '."""
        mock_pod = MagicMock()
        mock_pod.metadata.name = "multi-pod"
        mock_pod.metadata.namespace = "default"
        mock_pod.metadata.creation_timestamp = None
        mock_pod.status.phase = "Running"
        mock_pod.status.container_statuses = []
        c1 = MagicMock()
        c1.image = "nginx:1.25"
        c2 = MagicMock()
        c2.image = "envoy:1.28"
        mock_pod.spec.containers = [c1, c2]
        mock_pod.spec.node_name = "node-1"

        mock_api = MagicMock()
        mock_api.list_namespaced_pod.return_value = MagicMock(items=[mock_pod])
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        pods = list_pods(namespace="default")

        assert pods[0].image == "nginx:1.25, envoy:1.28"


class TestGetPod:
    """Tests for get_pod()."""

    def test_get_pod_returns_matching_pod(self, mocker) -> None:
        """Returns the PodInfo whose name matches."""
        mocker.patch(
            "kuber.core.kubernetes.pods.list_pods",
            return_value=[
                PodInfo("pod-1", "default", "Running", "1/1", 0, "node-1", "nginx", "5m"),
                PodInfo("pod-2", "default", "Pending", "0/1", 0, "node-2", "redis", "1m"),
            ],
        )

        pod = get_pod("pod-2", namespace="default")

        assert pod.name == "pod-2"
        assert pod.status == "Pending"

    def test_get_pod_raises_not_found_when_missing(self, mocker) -> None:
        """Raises KuberNotFoundError when the pod doesn't exist."""
        mocker.patch("kuber.core.kubernetes.pods.list_pods", return_value=[])

        with pytest.raises(KuberNotFoundError, match="ghost"):
            get_pod("ghost", namespace="default")


class TestDeletePod:
    """Tests for delete_pod()."""

    def test_delete_pod_calls_api(self, mocker) -> None:
        """delete_namespaced_pod is invoked with the correct arguments."""
        mock_api = MagicMock()
        mocker.patch("kuber.core.kubernetes.pods.core_v1", return_value=mock_api)

        delete_pod("pod-1", namespace="default")

        mock_api.delete_namespaced_pod.assert_called_once_with(
            "pod-1", "default", _request_timeout=mock_api.delete_namespaced_pod.call_args[1].get(
                "_request_timeout", None
            )
        )

