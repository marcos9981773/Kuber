"""
kuber/views/resources/configmaps_view.py
ConfigMaps list view with inline data editor.
"""
from __future__ import annotations

import yaml

from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from kuber.viewmodels.configmap_vm import ConfigMapViewModel
from kuber.views.common.yaml_editor import YamlEditor
from kuber.views.resources.base_resource_view import BaseResourceView


class ConfigMapsView(BaseResourceView):
    """Table view for Kubernetes ConfigMaps with edit dialog."""

    _title = "ConfigMaps"
    _columns = ["name", "namespace", "data_keys", "age"]

    def __init__(
        self, view_model: ConfigMapViewModel | None = None, parent: QWidget | None = None
    ) -> None:
        self._vm_cm: ConfigMapViewModel = view_model or ConfigMapViewModel()
        super().__init__(view_model=self._vm_cm, parent=parent)

    def _add_custom_actions(self, layout: QHBoxLayout) -> None:
        self._btn_edit = QPushButton(self.tr("✏ Edit Data"))
        self._btn_edit.setObjectName("btnPrimary")
        self._btn_edit.setEnabled(False)
        self._btn_edit.setAccessibleName(self.tr("Edit selected ConfigMap data"))
        self._btn_edit.clicked.connect(self._on_edit_clicked)
        layout.addWidget(self._btn_edit)

    def _on_selection_changed(self) -> None:
        super()._on_selection_changed()
        self._btn_edit.setEnabled(self._table.selectionModel().hasSelection())

    def _on_edit_clicked(self) -> None:
        item = self._selected_item()
        if not item:
            return
        dialog = _ConfigMapEditDialog(item.name, item.data, parent=self)
        if dialog.exec_() == QDialog.Accepted:
            new_data = dialog.get_data()
            self._vm_cm.save_data(item.name, item.namespace, new_data)


class _ConfigMapEditDialog(QDialog):
    """Modal YAML editor for ConfigMap data."""

    def __init__(
        self, name: str, data: dict[str, str], parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Edit ConfigMap — {0}").format(name))
        self.setMinimumSize(600, 400)
        self._data = data
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._editor = YamlEditor()
        self._editor.setAccessibleName(self.tr("ConfigMap YAML data editor"))
        self._editor.set_text(yaml.dump(self._data, default_flow_style=False))
        layout.addWidget(self._editor, stretch=1)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def get_data(self) -> dict[str, str]:
        """Parse the editor content back to a dict."""
        try:
            parsed = yaml.safe_load(self._editor.get_text())
            if isinstance(parsed, dict):
                return {str(k): str(v) for k, v in parsed.items()}
        except yaml.YAMLError:
            pass
        return self._data

