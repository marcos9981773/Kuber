"""
kuber/core/kubernetes/custom_resources.py
CRD (Custom Resource Definition) operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.kubernetes.client import call_with_retry, custom_objects
from kubernetes import client as k8s_client

logger = logging.getLogger(__name__)


@dataclass
class CRDInfo:
    """Lightweight representation of a Custom Resource Definition."""

    name: str
    group: str
    version: str
    kind: str
    scope: str  # Namespaced | Cluster
    plural: str


@dataclass
class CustomResourceInstance:
    """Lightweight representation of a custom resource instance."""

    name: str
    namespace: str
    kind: str
    api_version: str
    data: dict[str, Any] = field(default_factory=dict)
    age: str = ""


def list_crds(
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[CRDInfo]:
    """List all Custom Resource Definitions in the cluster."""

    def _call() -> list[CRDInfo]:
        api = k8s_client.ApiextensionsV1Api()
        response = api.list_custom_resource_definition(
            _request_timeout=timeout,
        )
        items: list[CRDInfo] = []
        for crd in response.items:
            spec = crd.spec
            names = spec.names
            # Use the first served version
            version = spec.versions[0].name if spec.versions else "v1"
            items.append(CRDInfo(
                name=crd.metadata.name if crd.metadata else "",
                group=spec.group or "",
                version=version,
                kind=names.kind if names else "",
                scope=spec.scope or "Namespaced",
                plural=names.plural if names else "",
            ))
        return items

    return call_with_retry(_call)


def list_custom_resources(
    group: str,
    version: str,
    plural: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[CustomResourceInstance]:
    """List instances of a specific custom resource."""

    def _call() -> list[CustomResourceInstance]:
        api = custom_objects()
        if namespace == "all":
            raw = api.list_cluster_custom_object(
                group, version, plural,
                _request_timeout=timeout,
            )
        else:
            raw = api.list_namespaced_custom_object(
                group, version, namespace, plural,
                _request_timeout=timeout,
            )

        items: list[CustomResourceInstance] = []
        for obj in raw.get("items", []):
            meta = obj.get("metadata", {})
            items.append(CustomResourceInstance(
                name=meta.get("name", ""),
                namespace=meta.get("namespace", ""),
                kind=obj.get("kind", ""),
                api_version=obj.get("apiVersion", f"{group}/{version}"),
                data=obj,
            ))
        return items

    return call_with_retry(_call)


def get_custom_resource(
    group: str,
    version: str,
    plural: str,
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Get a single custom resource by name."""

    def _call() -> dict[str, Any]:
        api = custom_objects()
        return api.get_namespaced_custom_object(
            group, version, namespace, plural, name,
            _request_timeout=timeout,
        )

    return call_with_retry(_call)


def create_custom_resource(
    group: str,
    version: str,
    plural: str,
    namespace: str,
    body: dict[str, Any],
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Create a custom resource instance."""

    def _call() -> dict[str, Any]:
        api = custom_objects()
        result = api.create_namespaced_custom_object(
            group, version, namespace, plural, body,
            _request_timeout=timeout,
        )
        name = body.get("metadata", {}).get("name", "unknown")
        logger.info(f"Created custom resource '{name}' ({group}/{version}/{plural}).")
        return result

    return call_with_retry(_call)


def delete_custom_resource(
    group: str,
    version: str,
    plural: str,
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a custom resource instance."""

    def _call() -> None:
        api = custom_objects()
        api.delete_namespaced_custom_object(
            group, version, namespace, plural, name,
            _request_timeout=timeout,
        )
        logger.info(f"Deleted custom resource '{name}' ({group}/{version}/{plural}).")

    call_with_retry(_call)

