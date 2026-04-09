"""
kuber/core/openshift/client.py
OpenShift cluster detection and Route operations.
No PyQt5 imports.

Falls back gracefully when the cluster is not OpenShift.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry, custom_objects

logger = logging.getLogger(__name__)

_ROUTE_GROUP = "route.openshift.io"
_ROUTE_VERSION = "v1"
_ROUTE_PLURAL = "routes"


@dataclass
class RouteInfo:
    """Lightweight representation of an OpenShift Route."""

    name: str
    namespace: str
    host: str
    path: str
    service: str
    tls: bool


def is_openshift_cluster(timeout: int = K8S_API_TIMEOUT_SECONDS) -> bool:
    """
    Detect whether the current cluster is an OpenShift cluster.

    Checks for the ``route.openshift.io`` API group.
    """
    try:
        from kubernetes import client as k8s_client
        api = k8s_client.ApisApi()
        groups = api.get_api_versions(_request_timeout=timeout)
        for g in groups.groups:
            if g.name == _ROUTE_GROUP:
                return True
    except Exception as exc:
        logger.debug(f"OpenShift detection failed: {exc}")
    return False


def list_routes(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[RouteInfo]:
    """List OpenShift Routes in a namespace."""

    def _call() -> list[RouteInfo]:
        api = custom_objects()
        if namespace == "all":
            raw = api.list_cluster_custom_object(
                _ROUTE_GROUP, _ROUTE_VERSION, _ROUTE_PLURAL,
                _request_timeout=timeout,
            )
        else:
            raw = api.list_namespaced_custom_object(
                _ROUTE_GROUP, _ROUTE_VERSION, namespace, _ROUTE_PLURAL,
                _request_timeout=timeout,
            )

        items: list[RouteInfo] = []
        for obj in raw.get("items", []):
            meta = obj.get("metadata", {})
            spec = obj.get("spec", {})
            to = spec.get("to", {})
            tls = spec.get("tls") is not None
            items.append(RouteInfo(
                name=meta.get("name", ""),
                namespace=meta.get("namespace", ""),
                host=spec.get("host", ""),
                path=spec.get("path", "/"),
                service=to.get("name", ""),
                tls=tls,
            ))
        return items

    return call_with_retry(_call)

