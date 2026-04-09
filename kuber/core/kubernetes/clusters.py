"""
kuber/core/kubernetes/clusters.py
Cluster-level Kubernetes operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.exceptions import KuberApiError, KuberConnectionError
from kuber.core.kubernetes.client import call_with_retry, core_v1, version_api

logger = logging.getLogger(__name__)


@dataclass
class NodeInfo:
    """Lightweight representation of a cluster node."""

    name: str
    status: str          # "Ready" | "NotReady" | "Unknown"
    roles: list[str]
    version: str
    os: str
    architecture: str
    cpu: str
    memory: str


@dataclass
class ClusterInfo:
    """Aggregated information about a Kubernetes cluster."""

    context_name: str
    server_url: str
    k8s_version: str = ""
    node_count: int = 0
    nodes: list[NodeInfo] = field(default_factory=list)
    namespace_count: int = 0
    is_reachable: bool = False


def get_server_version(timeout: int = K8S_API_TIMEOUT_SECONDS) -> str:
    """
    Retrieve the Kubernetes server version string.

    Returns:
        Version string such as ``"v1.29.2"``.

    Raises:
        KuberConnectionError: If the API is unreachable.
        KuberApiError:        On unexpected API errors.
    """
    def _call() -> str:
        info = version_api().get_code(_request_timeout=timeout)
        return f"{info.major}.{info.minor}"

    return call_with_retry(_call)


def list_nodes(timeout: int = K8S_API_TIMEOUT_SECONDS) -> list[NodeInfo]:
    """
    List all nodes in the current cluster context.

    Returns:
        List of :class:`NodeInfo` objects.

    Raises:
        KuberConnectionError: If the API is unreachable.
        KuberPermissionError: If the user lacks list-nodes permission.
        KuberApiError:        On unexpected API errors.
    """
    def _call() -> list[NodeInfo]:
        response = core_v1().list_node(_request_timeout=timeout)
        nodes: list[NodeInfo] = []
        for node in response.items:
            conditions = {c.type: c.status for c in (node.status.conditions or [])}
            ready_status = (
                "Ready" if conditions.get("Ready") == "True"
                else "NotReady" if conditions.get("Ready") == "False"
                else "Unknown"
            )
            labels = node.metadata.labels or {}
            roles = [
                k.split("/")[-1]
                for k in labels
                if k.startswith("node-role.kubernetes.io/")
            ] or ["worker"]

            node_info = node.status.node_info
            capacity = node.status.capacity or {}

            nodes.append(NodeInfo(
                name=node.metadata.name or "",
                status=ready_status,
                roles=roles,
                version=node_info.kubelet_version if node_info else "",
                os=node_info.os_image if node_info else "",
                architecture=node_info.architecture if node_info else "",
                cpu=capacity.get("cpu", ""),
                memory=capacity.get("memory", ""),
            ))
        return nodes

    return call_with_retry(_call)


def list_namespaces(timeout: int = K8S_API_TIMEOUT_SECONDS) -> list[str]:
    """
    List all namespace names visible to the current user.

    Returns:
        Sorted list of namespace name strings.

    Raises:
        KuberConnectionError: If the API is unreachable.
        KuberPermissionError: If the user cannot list namespaces.
        KuberApiError:        On unexpected API errors.
    """
    def _call() -> list[str]:
        response = core_v1().list_namespace(_request_timeout=timeout)
        return sorted(ns.metadata.name or "" for ns in response.items)

    return call_with_retry(_call)


def get_cluster_info(
    context_name: str,
    server_url: str,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> ClusterInfo:
    """
    Retrieve aggregated information about the current cluster.

    Args:
        context_name: The kubeconfig context name.
        server_url:   The API server URL.
        timeout:      Request timeout in seconds.

    Returns:
        Populated :class:`ClusterInfo` dataclass.
    """
    info = ClusterInfo(context_name=context_name, server_url=server_url)
    try:
        info.k8s_version = get_server_version(timeout)
        info.nodes = list_nodes(timeout)
        info.node_count = len(info.nodes)
        namespaces = list_namespaces(timeout)
        info.namespace_count = len(namespaces)
        info.is_reachable = True
    except (KuberConnectionError, KuberApiError) as exc:
        logger.warning(f"Could not fetch full cluster info for '{context_name}': {exc}")
        info.is_reachable = False
    return info

