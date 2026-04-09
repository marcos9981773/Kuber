"""
kuber/views/resources/deployments_view.py
Deployments list view with scale and rolling-update actions.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QInputDialog, QPushButton, QWidget

from kuber.viewmodels.deployment_vm import DeploymentViewModel
from kuber.views.resources.base_resource_view import BaseResourceView


class DeploymentsView(BaseResourceView):
    """Table view for Kubernetes Deployments with scale and image update."""

    _title = "Deployments"
    _columns = ["name", "namespace", "replicas", "ready_replicas", "image", "strategy", "age"]

    def __init__(
        self, view_model: DeploymentViewModel | None = None, parent: QWidget | None = None
    ) -> None:
        self._vm_deploy: DeploymentViewModel = view_model or DeploymentViewModel()
        super().__init__(view_model=self._vm_deploy, parent=parent)

    def _add_custom_actions(self, layout: QHBoxLayout) -> None:
        self._btn_scale = QPushButton(self.tr("⚖ Scale"))
        self._btn_scale.setObjectName("btnPrimary")
        self._btn_scale.setEnabled(False)
        self._btn_scale.setAccessibleName(self.tr("Scale selected deployment"))
        self._btn_scale.clicked.connect(self._on_scale_clicked)
        layout.addWidget(self._btn_scale)

        self._btn_update = QPushButton(self.tr("🔄 Update Image"))
        self._btn_update.setObjectName("btnPrimary")
        self._btn_update.setEnabled(False)
        self._btn_update.setAccessibleName(self.tr("Update image of selected deployment"))
        self._btn_update.clicked.connect(self._on_update_image_clicked)
        layout.addWidget(self._btn_update)

    def _on_selection_changed(self) -> None:
        super()._on_selection_changed()
        has = self._table.selectionModel().hasSelection()
        self._btn_scale.setEnabled(has)
        self._btn_update.setEnabled(has)

    def _on_scale_clicked(self) -> None:
        item = self._selected_item()
        if not item:
            return
        replicas, ok = QInputDialog.getInt(
            self,
            self.tr("Scale Deployment"),
            self.tr("Replicas for '{0}':").format(item.name),
            value=item.replicas,
            min=0,
            max=100,
        )
        if ok:
            self._vm_deploy.scale(item.name, item.namespace, replicas)

    def _on_update_image_clicked(self) -> None:
        item = self._selected_item()
        if not item:
            return
        image, ok = QInputDialog.getText(
            self,
            self.tr("Update Image"),
            self.tr("New image for '{0}':").format(item.name),
            text=item.image,
        )
        if ok and image:
            # Use the first container name (from deployment spec)
            container_name = item.name
            self._vm_deploy.update_image(item.name, item.namespace, container_name, image)

