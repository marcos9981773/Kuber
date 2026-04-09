"""
kuber/views/resources/services_view.py
Services list view.
"""
from __future__ import annotations

from kuber.viewmodels.service_vm import ServiceViewModel
from kuber.views.resources.base_resource_view import BaseResourceView


class ServicesView(BaseResourceView):
    """Table view for Kubernetes Services."""

    _title = "Services"
    _columns = ["name", "namespace", "type", "cluster_ip", "external_ip", "ports", "age"]

    def __init__(self, view_model: ServiceViewModel | None = None, parent=None) -> None:
        vm = view_model or ServiceViewModel()
        super().__init__(view_model=vm, parent=parent)

