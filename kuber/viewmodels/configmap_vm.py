"""
kuber/viewmodels/configmap_vm.py
ViewModel for ConfigMaps resource view with edit support.
"""
from __future__ import annotations

from kuber.core.kubernetes.configmaps import (
    ConfigMapInfo,
    delete_configmap,
    get_configmap,
    list_configmaps,
    update_configmap,
)
from kuber.viewmodels.resource_vm import ResourceViewModel


class ConfigMapViewModel(ResourceViewModel):
    """ConfigMaps-specific ViewModel with data editing."""

    def _fetch_items(self, namespace: str) -> list[ConfigMapInfo]:
        return list_configmaps(namespace=namespace)

    def _delete_item(self, name: str, namespace: str) -> None:
        delete_configmap(name=name, namespace=namespace)

    def save_data(self, name: str, namespace: str, data: dict[str, str]) -> None:
        """Save edited ConfigMap data."""
        self._run_action(
            update_configmap,
            description=f"Save ConfigMap {name}",
            name=name,
            namespace=namespace,
            data=data,
        )

