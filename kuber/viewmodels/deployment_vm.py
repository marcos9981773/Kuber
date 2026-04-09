"""
kuber/viewmodels/deployment_vm.py
ViewModel for Deployments resource view with scale/rolling-update actions.
"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal

from kuber.core.kubernetes.deployments import (
    DeploymentInfo,
    delete_deployment,
    list_deployments,
    scale_deployment,
    update_deployment_image,
)
from kuber.viewmodels.resource_vm import ResourceViewModel


class DeploymentViewModel(ResourceViewModel):
    """Deployments-specific ViewModel with scale and image-update actions."""

    scale_completed: pyqtSignal = pyqtSignal(str)

    def _fetch_items(self, namespace: str) -> list[DeploymentInfo]:
        return list_deployments(namespace=namespace)

    def _delete_item(self, name: str, namespace: str) -> None:
        delete_deployment(name=name, namespace=namespace)

    def scale(self, name: str, namespace: str, replicas: int) -> None:
        """Scale a deployment to ``replicas``."""
        self._run_action(
            scale_deployment,
            description=f"Scale {name} to {replicas}",
            name=name,
            namespace=namespace,
            replicas=replicas,
        )

    def update_image(
        self, name: str, namespace: str, container_name: str, image: str
    ) -> None:
        """Trigger a rolling update with a new image."""
        self._run_action(
            update_deployment_image,
            description=f"Update {name} image to {image}",
            name=name,
            namespace=namespace,
            container_name=container_name,
            image=image,
        )

