"""
kuber/viewmodels/pod_vm.py
ViewModel for Pods resource view.
"""
from __future__ import annotations

from kuber.core.kubernetes.pods import PodInfo, delete_pod, list_pods
from kuber.viewmodels.resource_vm import ResourceViewModel


class PodViewModel(ResourceViewModel):
    """Pods-specific ViewModel."""

    def _fetch_items(self, namespace: str) -> list[PodInfo]:
        return list_pods(namespace=namespace)

    def _delete_item(self, name: str, namespace: str) -> None:
        delete_pod(name=name, namespace=namespace)

