"""
kuber/viewmodels/service_vm.py
ViewModel for Services resource view.
"""
from __future__ import annotations

from kuber.core.kubernetes.services import ServiceInfo, delete_service, list_services
from kuber.viewmodels.resource_vm import ResourceViewModel


class ServiceViewModel(ResourceViewModel):
    """Services-specific ViewModel."""

    def _fetch_items(self, namespace: str) -> list[ServiceInfo]:
        return list_services(namespace=namespace)

    def _delete_item(self, name: str, namespace: str) -> None:
        delete_service(name=name, namespace=namespace)

