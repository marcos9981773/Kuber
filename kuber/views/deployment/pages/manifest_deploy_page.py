"""
kuber/views/deployment/pages/manifest_deploy_page.py
Wizard page for deploying via raw Kubernetes manifest YAML.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWizardPage,
)

from kuber.views.common.yaml_editor import YamlEditor


class ManifestDeployPage(QWizardPage):
    """Wizard page: deploy from a YAML/JSON manifest."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Deploy from Manifest"))
        self.setSubTitle(
            self.tr("Paste or load a Kubernetes manifest (YAML or JSON).")
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        btn_row = QHBoxLayout()
        self._btn_load = QPushButton(self.tr("📂 Load File…"))
        self._btn_load.setAccessibleName(self.tr("Load manifest from file"))
        self._btn_load.clicked.connect(self._on_load_file)
        btn_row.addWidget(self._btn_load)
        btn_row.addStretch()
        layout.addLayout(btn_row)

        self._editor = YamlEditor(
            placeholder=self.tr(
                "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: my-app"
            ),
        )
        self._editor.setAccessibleName(self.tr("YAML manifest editor"))
        layout.addWidget(self._editor, stretch=1)

    def isComplete(self) -> bool:
        """Page is complete when there's at least some YAML text."""
        return len(self._editor.get_text().strip()) > 10

    def get_manifest_yaml(self) -> str:
        """Return the raw YAML text."""
        return self._editor.get_text()

    def _on_load_file(self) -> None:
        path, _ = QFileDialog.getOpenFileName(
            self,
            self.tr("Open Manifest File"),
            "",
            self.tr("YAML Files (*.yaml *.yml);;JSON Files (*.json);;All Files (*)"),
        )
        if path:
            try:
                from pathlib import Path
                content = Path(path).read_text(encoding="utf-8")
                self._editor.set_text(content)
            except OSError:
                pass
        self.completeChanged.emit()

