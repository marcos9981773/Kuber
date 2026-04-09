"""
kuber/views/resources/pods_view.py
Pods list view with status colors and delete action.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QAction, QMenu

from kuber.viewmodels.pod_vm import PodViewModel
from kuber.views.resources.base_resource_view import BaseResourceView


class PodsView(BaseResourceView):
    """Table view for Kubernetes Pods."""

    open_monitoring_requested: pyqtSignal = pyqtSignal(str, str)
    """Emitted with (pod_name, namespace) when the user asks to monitor a pod."""

    _title = "Pods"
    _columns = ["name", "namespace", "status", "ready", "restarts", "node", "image", "age"]

    def __init__(self, view_model: PodViewModel | None = None, parent=None) -> None:
        vm = view_model or PodViewModel()
        super().__init__(view_model=vm, parent=parent)
        self._setup_context_menu()

    def _setup_context_menu(self) -> None:
        """Enable a right-click context menu on the pods table."""
        self._table.setContextMenuPolicy(Qt.CustomContextMenu)
        self._table.customContextMenuRequested.connect(self._show_context_menu)

    def _show_context_menu(self, position) -> None:
        """Build and display the context menu at the cursor position."""
        item = self._selected_item()
        if item is None:
            return

        menu = QMenu(self)

        monitoring_action = QAction(self.tr("📊 Open in Monitoring"), self)
        monitoring_action.setStatusTip(
            self.tr("Open pod in monitoring view")
        )
        monitoring_action.triggered.connect(
            lambda: self._on_open_monitoring(item)
        )
        menu.addAction(monitoring_action)

        menu.exec_(self._table.viewport().mapToGlobal(position))

    def _on_open_monitoring(self, item) -> None:
        """Emit the signal requesting navigation to the Monitoring page."""
        pod_name = getattr(item, "name", "")
        namespace = getattr(item, "namespace", "default")
        if pod_name:
            self.open_monitoring_requested.emit(pod_name, namespace)
