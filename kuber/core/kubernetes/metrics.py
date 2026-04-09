"""
kuber/core/kubernetes/metrics.py
Kubernetes metrics retrieval via metrics-server API.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry
from kuber.core.exceptions import KuberApiError

logger = logging.getLogger(__name__)


@dataclass
class PodMetrics:
    """CPU and memory metrics for a single pod."""

    name: str
    namespace: str
    cpu_millicores: int
    memory_mib: int


@dataclass
class NodeMetrics:
    """CPU and memory metrics for a single node."""

    name: str
    cpu_millicores: int
    memory_mib: int


def _parse_cpu(raw: str) -> int:
    """Convert k8s CPU string (e.g. '250m', '1') to millicores."""
    raw = raw.strip()
    if raw.endswith("n"):
        return int(raw[:-1]) // 1_000_000
    if raw.endswith("u"):
        return int(raw[:-1]) // 1_000
    if raw.endswith("m"):
        return int(raw[:-1])
    return int(float(raw) * 1000)


def _parse_memory(raw: str) -> int:
    """Convert k8s memory string (e.g. '128Mi', '1Gi') to MiB."""
    raw = raw.strip()
    if raw.endswith("Ki"):
        return int(raw[:-2]) // 1024
    if raw.endswith("Mi"):
        return int(raw[:-2])
    if raw.endswith("Gi"):
        return int(raw[:-2]) * 1024
    if raw.endswith("Ti"):
        return int(raw[:-2]) * 1024 * 1024
    # Plain bytes
    try:
        return int(raw) // (1024 * 1024)
    except ValueError:
        return 0


def list_pod_metrics(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[PodMetrics]:
    """
    Fetch pod metrics from metrics-server.

    Requires metrics-server to be installed in the cluster.
    """
    def _call() -> list[PodMetrics]:
        from kubernetes import client as k8s_client
        api = k8s_client.CustomObjectsApi()
        if namespace == "all":
            raw = api.list_cluster_custom_object(
                "metrics.k8s.io", "v1beta1", "pods",
                _request_timeout=timeout,
            )
        else:
            raw = api.list_namespaced_custom_object(
                "metrics.k8s.io", "v1beta1", namespace, "pods",
                _request_timeout=timeout,
            )
        items: list[PodMetrics] = []
        for pod in raw.get("items", []):
            meta = pod.get("metadata", {})
            total_cpu = 0
            total_mem = 0
            for container in pod.get("containers", []):
                usage = container.get("usage", {})
                total_cpu += _parse_cpu(usage.get("cpu", "0"))
                total_mem += _parse_memory(usage.get("memory", "0"))
            items.append(PodMetrics(
                name=meta.get("name", ""),
                namespace=meta.get("namespace", ""),
                cpu_millicores=total_cpu,
                memory_mib=total_mem,
            ))
        return items

    return call_with_retry(_call)


def list_node_metrics(
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[NodeMetrics]:
    """Fetch node metrics from metrics-server."""
    def _call() -> list[NodeMetrics]:
        from kubernetes import client as k8s_client
        api = k8s_client.CustomObjectsApi()
        raw = api.list_cluster_custom_object(
            "metrics.k8s.io", "v1beta1", "nodes",
            _request_timeout=timeout,
        )
        items: list[NodeMetrics] = []
        for node in raw.get("items", []):
            usage = node.get("usage", {})
            items.append(NodeMetrics(
                name=node.get("metadata", {}).get("name", ""),
                cpu_millicores=_parse_cpu(usage.get("cpu", "0")),
                memory_mib=_parse_memory(usage.get("memory", "0")),
            ))
        return items

    return call_with_retry(_call)

