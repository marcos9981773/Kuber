"""
kuber/views/deployment/pages/helm_deploy_page.py
Wizard page for deploying via Helm chart.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QFormLayout,
    QLineEdit,
    QWizardPage,
)

from kuber.views.common.yaml_editor import YamlEditor


class HelmDeployPage(QWizardPage):
    """Wizard page: deploy from a Helm chart reference."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Deploy from Helm Chart"))
        self.setSubTitle(
            self.tr("Specify the Helm chart, release name, and optional values.")
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self._chart_input = QLineEdit()
        self._chart_input.setPlaceholderText("bitnami/nginx")
        self._chart_input.setAccessibleName(self.tr("Helm chart reference"))
        self.registerField("helm_chart*", self._chart_input)
        layout.addRow(self.tr("Chart:"), self._chart_input)

        self._release_input = QLineEdit()
        self._release_input.setPlaceholderText("my-release")
        self._release_input.setAccessibleName(self.tr("Helm release name"))
        self.registerField("helm_release*", self._release_input)
        layout.addRow(self.tr("Release Name:"), self._release_input)

        self._values_editor = YamlEditor(
            placeholder=self.tr("# Optional YAML values\nreplicaCount: 2"),
        )
        self._values_editor.setAccessibleName(self.tr("Helm values YAML editor"))
        self._values_editor.setMaximumHeight(160)
        layout.addRow(self.tr("Values (YAML):"), self._values_editor)

    def get_values_yaml(self) -> str:
        """Return the raw YAML text from the values editor."""
        return self._values_editor.get_text()

