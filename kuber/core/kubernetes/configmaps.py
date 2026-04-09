"""
kuber/core/kubernetes/configmaps.py
ConfigMap CRUD operations.
No PyQt5 imports.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import yaml

from kuber.constants import K8S_API_TIMEOUT_SECONDS
from kuber.core.exceptions import KuberValidationError
from kuber.core.kubernetes.client import call_with_retry, core_v1
from kuber.core.kubernetes.pods import _compute_age

logger = logging.getLogger(__name__)


@dataclass
class ConfigMapInfo:
    """Lightweight representation of a Kubernetes ConfigMap."""

    name: str
    namespace: str
    data_keys: list[str] = field(default_factory=list)
    age: str = ""
    data: dict[str, str] = field(default_factory=dict)


def list_configmaps(
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> list[ConfigMapInfo]:
    """List ConfigMaps in a namespace."""
    def _call() -> list[ConfigMapInfo]:
        api = core_v1()
        if namespace == "all":
            response = api.list_config_map_for_all_namespaces(_request_timeout=timeout)
        else:
            response = api.list_namespaced_config_map(namespace, _request_timeout=timeout)

        items: list[ConfigMapInfo] = []
        for cm in response.items:
            meta = cm.metadata
            data = cm.data or {}
            items.append(ConfigMapInfo(
                name=meta.name or "" if meta else "",
                namespace=meta.namespace or "" if meta else "",
                data_keys=sorted(data.keys()),
                age=_compute_age(meta.creation_timestamp) if meta else "",
                data=dict(data),
            ))
        return items

    return call_with_retry(_call)


def get_configmap(
    name: str,
    namespace: str = "default",
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> ConfigMapInfo:
    """Get a specific ConfigMap by name."""
    def _call() -> ConfigMapInfo:
        cm = core_v1().read_namespaced_config_map(name, namespace, _request_timeout=timeout)
        meta = cm.metadata
        data = cm.data or {}
        return ConfigMapInfo(
            name=meta.name or "" if meta else "",
            namespace=meta.namespace or "" if meta else "",
            data_keys=sorted(data.keys()),
            age=_compute_age(meta.creation_timestamp) if meta else "",
            data=dict(data),
        )

    return call_with_retry(_call)


def update_configmap(
    name: str,
    namespace: str,
    data: dict[str, str],
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Replace a ConfigMap's data payload."""
    if not isinstance(data, dict):
        raise KuberValidationError("ConfigMap data must be a dict[str, str].")

    def _call() -> None:
        body = {"data": data}
        core_v1().patch_namespaced_config_map(name, namespace, body, _request_timeout=timeout)
        logger.info(f"Updated ConfigMap '{name}' in '{namespace}'.")

    call_with_retry(_call)


def delete_configmap(
    name: str,
    namespace: str,
    timeout: int = K8S_API_TIMEOUT_SECONDS,
) -> None:
    """Delete a ConfigMap by name."""
    def _call() -> None:
        core_v1().delete_namespaced_config_map(name, namespace, _request_timeout=timeout)
        logger.info(f"Deleted ConfigMap '{name}' in '{namespace}'.")

    call_with_retry(_call)

