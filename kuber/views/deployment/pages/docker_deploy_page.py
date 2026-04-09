"""
kuber/views/deployment/pages/docker_deploy_page.py
Wizard page for deploying via Docker image.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QFormLayout,
    QLabel,
    QLineEdit,
    QSpinBox,
    QWizardPage,
)


class DockerDeployPage(QWizardPage):
    """Wizard page: deploy from a Docker image reference."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Deploy from Docker Image"))
        self.setSubTitle(
            self.tr("Specify the Docker image, tag, and replica count.")
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self._image_input = QLineEdit()
        self._image_input.setPlaceholderText("nginx")
        self._image_input.setAccessibleName(self.tr("Docker image name"))
        self.registerField("docker_image*", self._image_input)
        layout.addRow(self.tr("Image:"), self._image_input)

        self._tag_input = QLineEdit("latest")
        self._tag_input.setAccessibleName(self.tr("Docker image tag"))
        self.registerField("docker_tag", self._tag_input)
        layout.addRow(self.tr("Tag:"), self._tag_input)

        self._name_input = QLineEdit()
        self._name_input.setPlaceholderText(self.tr("(auto from image)"))
        self._name_input.setAccessibleName(self.tr("Application name"))
        self.registerField("docker_app_name", self._name_input)
        layout.addRow(self.tr("App Name:"), self._name_input)

        self._replicas_spin = QSpinBox()
        self._replicas_spin.setRange(1, 100)
        self._replicas_spin.setValue(1)
        self._replicas_spin.setAccessibleName(self.tr("Replica count"))
        self.registerField("docker_replicas", self._replicas_spin)
        layout.addRow(self.tr("Replicas:"), self._replicas_spin)

