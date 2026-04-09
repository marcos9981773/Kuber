"""
tests/unit/core/kubernetes/test_clusters.py
Tests for kuber/core/kubernetes/clusters.py
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock, patch

from kuber.core.exceptions import KuberConnectionError
from kuber.core.kubernetes.clusters import get_cluster_info, list_namespaces, list_nodes


class TestListNodes:
    """Tests for list_nodes()."""

    def test_list_nodes_returns_node_info_list(self, mocker) -> None:
        """Returns a list of NodeInfo for each node in the response."""
        mock_node = MagicMock()
        mock_node.metadata.name = "node-1"
        mock_node.metadata.creation_timestamp = None
        mock_node.status.conditions = [MagicMock(type="Ready", status="True")]
        mock_node.metadata.labels = {"node-role.kubernetes.io/control-plane": ""}
        mock_node.status.node_info.kubelet_version = "v1.29.0"
        mock_node.status.node_info.os_image = "Ubuntu 22.04"
        mock_node.status.node_info.architecture = "amd64"
        mock_node.status.capacity = {"cpu": "4", "memory": "8Gi"}

        mock_api = MagicMock()
        mock_api.list_node.return_value = MagicMock(items=[mock_node])
        mocker.patch("kuber.core.kubernetes.clusters.core_v1", return_value=mock_api)

        nodes = list_nodes()
        assert len(nodes) == 1
        assert nodes[0].name == "node-1"
        assert nodes[0].status == "Ready"
        assert "control-plane" in nodes[0].roles

    def test_list_nodes_not_ready_status(self, mocker) -> None:
        """Node with Ready=False gets status 'NotReady'."""
        mock_node = MagicMock()
        mock_node.metadata.name = "node-bad"
        mock_node.metadata.creation_timestamp = None
        mock_node.status.conditions = [MagicMock(type="Ready", status="False")]
        mock_node.metadata.labels = {}
        mock_node.status.node_info = MagicMock()
        mock_node.status.capacity = {}

        mock_api = MagicMock()
        mock_api.list_node.return_value = MagicMock(items=[mock_node])
        mocker.patch("kuber.core.kubernetes.clusters.core_v1", return_value=mock_api)

        nodes = list_nodes()
        assert nodes[0].status == "NotReady"


class TestListNamespaces:
    """Tests for list_namespaces()."""

    def test_list_namespaces_returns_sorted_names(self, mocker) -> None:
        """Returns namespace names sorted alphabetically."""
        ns_items = [MagicMock(), MagicMock(), MagicMock()]
        ns_items[0].metadata.name = "kube-system"
        ns_items[1].metadata.name = "default"
        ns_items[2].metadata.name = "monitoring"

        mock_api = MagicMock()
        mock_api.list_namespace.return_value = MagicMock(items=ns_items)
        mocker.patch("kuber.core.kubernetes.clusters.core_v1", return_value=mock_api)

        namespaces = list_namespaces()
        assert namespaces == ["default", "kube-system", "monitoring"]


class TestGetClusterInfo:
    """Tests for get_cluster_info()."""

    def test_get_cluster_info_returns_populated_info(self, mocker) -> None:
        """Returns ClusterInfo with nodes and namespaces when API is reachable."""
        mocker.patch(
            "kuber.core.kubernetes.clusters.get_server_version", return_value="1.29"
        )
        mocker.patch(
            "kuber.core.kubernetes.clusters.list_nodes", return_value=[]
        )
        mocker.patch(
            "kuber.core.kubernetes.clusters.list_namespaces", return_value=["default"]
        )

        info = get_cluster_info("my-context", "https://example.com")
        assert info.is_reachable is True
        assert info.k8s_version == "1.29"
        assert info.namespace_count == 1

    def test_get_cluster_info_unreachable_marks_not_reachable(self, mocker) -> None:
        """Sets is_reachable=False when the API is unreachable."""
        mocker.patch(
            "kuber.core.kubernetes.clusters.get_server_version",
            side_effect=KuberConnectionError("unreachable"),
        )

        info = get_cluster_info("ctx", "https://example.com")
        assert info.is_reachable is False

