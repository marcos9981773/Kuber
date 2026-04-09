"""
kuber/core/kubernetes/pods.py
Pod CRUD and status operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from kubernetes.client.exceptions import ApiException

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.exceptions import KuberNotFoundError
from kuber.core.kubernetes.client import call_with_retry, core_v1

logger = logging.getLogger(__name__)


@dataclass
class PodInfo:
    """Lightweight representation of a Kubernetes Pod."""

    name: str
    namespace: str
    status: str          # Running | Pending | Failed | Succeeded | Unknown
    ready: str           # "x/y" containers ready
    restarts: int
    node: str
    image: str
    age: str


def list_pods(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[PodInfo]:
    """
    List pods in a namespace.

    Args:
        namespace: Target namespace (``"all"`` lists across all namespaces).
        timeout:   Request timeout in seconds.

    Returns:
        List of :class:`PodInfo` objects.
    """
    def _call() -> list[PodInfo]:
        api = core_v1()
        if namespace == "all":
            response = api.list_pod_for_all_namespaces(_request_timeout=timeout)
        else:
            response = api.list_namespaced_pod(namespace, _request_timeout=timeout)

        pods: list[PodInfo] = []
        for pod in response.items:
            meta = pod.metadata
            status = pod.status
            containers = pod.spec.containers or [] if pod.spec else []
            container_statuses = status.container_statuses or [] if status else []
            ready_count = sum(1 for cs in container_statuses if cs.ready)
            total_restarts = sum(cs.restart_count for cs in container_statuses)
            phase = status.phase if status else "Unknown"

            images = ", ".join(c.image or "" for c in containers)
            age = _compute_age(meta.creation_timestamp) if meta else ""

            node_name = pod.spec.node_name or "" if pod.spec else ""
            pods.append(PodInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                status=phase or "Unknown",
                ready=f"{ready_count}/{len(containers)}",
                restarts=total_restarts,
                node=node_name,
                image=images,
                age=age,
            ))
        return pods

    return call_with_retry(_call)


def get_pod(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> PodInfo:
    """
    Get a specific pod by name.

    Raises:
        KuberNotFoundError: If the pod does not exist.
    """
    pods = list_pods(namespace, timeout)
    for pod in pods:
        if pod.name == name:
            return pod
    raise KuberNotFoundError(
        f"Pod '{name}' not found in namespace '{namespace}'.",
    )


def delete_pod(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """
    Delete a pod by name.

    Raises:
        KuberNotFoundError:   If the pod does not exist.
        KuberPermissionError: If the user lacks delete permission.
        KuberApiError:        On unexpected API errors.
    """
    def _call() -> None:
        core_v1().delete_namespaced_pod(name, namespace, _request_timeout=timeout)
        logger.info(f"Deleted pod '{name}' in namespace '{namespace}'.")

    call_with_retry(_call)


# ── Private helpers ──────────────────────────────────────────────────────────

def _compute_age(creation_timestamp: object | None) -> str:
    """Return a human-readable age string from a k8s creation timestamp."""
    if creation_timestamp is None:
        return ""
    from datetime import datetime, timezone

    try:
        now = datetime.now(tz=timezone.utc)
        delta = now - creation_timestamp  # type: ignore[operator]
        total_seconds = int(delta.total_seconds())
        if total_seconds < 3600:
            return f"{total_seconds // 60}m"
        if total_seconds < 86400:
            return f"{total_seconds // 3600}h"
        return f"{total_seconds // 86400}d"
    except Exception:
        return ""

