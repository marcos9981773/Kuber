"""
kuber/views/deployment/deploy_wizard.py
Multi-step QWizard for deploying applications to Kubernetes.
"""
from __future__ import annotations

import logging

import yaml
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QComboBox,
    QFormLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
    QWizard,
    QWizardPage,
    QWidget,
)

from kuber.viewmodels.app_deploy_vm import AppDeployViewModel, DeployMode, DeploySpec
from kuber.views.deployment.deploy_progress_dialog import DeployProgressDialog
from kuber.views.deployment.pages.docker_deploy_page import DockerDeployPage
from kuber.views.deployment.pages.helm_deploy_page import HelmDeployPage
from kuber.views.deployment.pages.manifest_deploy_page import ManifestDeployPage
from kuber.views.deployment.pages.review_deploy_page import ReviewDeployPage

logger = logging.getLogger(__name__)

# Page IDs
_PAGE_MODE = 0
_PAGE_DOCKER = 1
_PAGE_HELM = 2
_PAGE_MANIFEST = 3
_PAGE_REVIEW = 4


class _ModeSelectionPage(QWizardPage):
    """First page: pick the deployment mode and target namespace."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Select Deployment Method"))
        self.setSubTitle(
            self.tr("Choose how you want to deploy your application.")
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QFormLayout(self)

        self._mode_combo = QComboBox()
        self._mode_combo.addItem(self.tr("Docker Image"), DeployMode.DOCKER_IMAGE.value)
        self._mode_combo.addItem(self.tr("Helm Chart"), DeployMode.HELM_CHART.value)
        self._mode_combo.addItem(self.tr("Kubernetes Manifest"), DeployMode.MANIFEST.value)
        self._mode_combo.setAccessibleName(self.tr("Deployment method selector"))
        layout.addRow(self.tr("Method:"), self._mode_combo)

        self._ns_input = QLineEdit("default")
        self._ns_input.setAccessibleName(self.tr("Target namespace"))
        self.registerField("deploy_namespace", self._ns_input)
        layout.addRow(self.tr("Namespace:"), self._ns_input)

    def selected_mode(self) -> DeployMode:
        val = self._mode_combo.currentData()
        return DeployMode(val)

    def nextId(self) -> int:
        mode = self.selected_mode()
        if mode == DeployMode.DOCKER_IMAGE:
            return _PAGE_DOCKER
        if mode == DeployMode.HELM_CHART:
            return _PAGE_HELM
        return _PAGE_MANIFEST


class DeployWizard(QWizard):
    """
    Multi-step wizard for deploying applications.

    Flow:
        Mode Selection → (Docker | Helm | Manifest) → Review → Execute
    """

    def __init__(
        self,
        view_model: AppDeployViewModel | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model or AppDeployViewModel()
        self.setWindowTitle(self.tr("Deploy Application"))
        self.setMinimumSize(640, 480)
        self.setWizardStyle(QWizard.ModernStyle)
        self._setup_pages()
        self._connect_signals()

    def _setup_pages(self) -> None:
        self._mode_page = _ModeSelectionPage()
        self._docker_page = DockerDeployPage()
        self._helm_page = HelmDeployPage()
        self._manifest_page = ManifestDeployPage()
        self._review_page = ReviewDeployPage()

        self.setPage(_PAGE_MODE, self._mode_page)
        self.setPage(_PAGE_DOCKER, self._docker_page)
        self.setPage(_PAGE_HELM, self._helm_page)
        self.setPage(_PAGE_MANIFEST, self._manifest_page)
        self.setPage(_PAGE_REVIEW, self._review_page)

        # Docker/Helm/Manifest pages always go to Review
        self._docker_page.nextId = lambda: _PAGE_REVIEW  # type: ignore[assignment]
        self._helm_page.nextId = lambda: _PAGE_REVIEW  # type: ignore[assignment]
        self._manifest_page.nextId = lambda: _PAGE_REVIEW  # type: ignore[assignment]
        self._review_page.nextId = lambda: -1  # type: ignore[assignment]

    def _connect_signals(self) -> None:
        self.currentIdChanged.connect(self._on_page_changed)

    def _on_page_changed(self, page_id: int) -> None:
        if page_id == _PAGE_REVIEW:
            self._review_page.set_summary_text(self._build_summary())

    def accept(self) -> None:
        """Execute the deployment when the user clicks Finish."""
        spec = self._build_spec()
        progress = DeployProgressDialog(self._vm, parent=self)
        self._vm.execute(spec)
        progress.exec_()
        super().accept()

    # ── Spec building ────────────────────────────────────────────────────────

    def _build_spec(self) -> DeploySpec:
        mode = self._mode_page.selected_mode()
        ns = self.field("deploy_namespace") or "default"
        dry_run = self._review_page.is_dry_run()

        if mode == DeployMode.DOCKER_IMAGE:
            return DeploySpec(
                mode=mode,
                namespace=ns,
                image=self.field("docker_image") or "",
                tag=self.field("docker_tag") or "latest",
                app_name=self.field("docker_app_name") or "",
                replicas=self.field("docker_replicas") or 1,
                dry_run=dry_run,
            )
        if mode == DeployMode.HELM_CHART:
            values_yaml = self._helm_page.get_values_yaml()
            helm_values = None
            if values_yaml.strip():
                try:
                    parsed = yaml.safe_load(values_yaml)
                    if isinstance(parsed, dict):
                        helm_values = {str(k): str(v) for k, v in parsed.items()}
                except yaml.YAMLError:
                    pass
            return DeploySpec(
                mode=mode,
                namespace=ns,
                chart=self.field("helm_chart") or "",
                release_name=self.field("helm_release") or "",
                helm_values=helm_values,
                dry_run=dry_run,
            )
        # Manifest
        return DeploySpec(
            mode=mode,
            namespace=ns,
            manifest_yaml=self._manifest_page.get_manifest_yaml(),
            dry_run=dry_run,
        )

    def _build_summary(self) -> str:
        mode = self._mode_page.selected_mode()
        ns = self.field("deploy_namespace") or "default"
        lines = [f"Namespace: {ns}", f"Mode: {mode.name}", ""]

        if mode == DeployMode.DOCKER_IMAGE:
            img = self.field("docker_image") or "?"
            tag = self.field("docker_tag") or "latest"
            name = self.field("docker_app_name") or "(auto)"
            reps = self.field("docker_replicas") or 1
            lines += [f"Image: {img}:{tag}", f"App name: {name}", f"Replicas: {reps}"]
        elif mode == DeployMode.HELM_CHART:
            chart = self.field("helm_chart") or "?"
            rel = self.field("helm_release") or "?"
            lines += [f"Chart: {chart}", f"Release: {rel}"]
        else:
            yaml_text = self._manifest_page.get_manifest_yaml()
            preview = yaml_text[:200] + ("…" if len(yaml_text) > 200 else "")
            lines += [f"Manifest preview:\n{preview}"]

        return "\n".join(lines)

