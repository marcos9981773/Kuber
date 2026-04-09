"""
kuber/viewmodels/app_deploy_vm.py
ViewModel for the Application Deployment wizard.
Orchestrates Docker-image, Helm-chart, and Manifest deploy modes.
"""
from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

import yaml
from PyQt5.QtCore import QObject, pyqtSignal

from kuber.core.helm.client import install_chart
from kuber.core.kubernetes.deployments import apply_manifest
from kuber.views.common.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class DeployMode(Enum):
    DOCKER_IMAGE = auto()
    HELM_CHART = auto()
    MANIFEST = auto()


@dataclass
class DeploySpec:
    """All data needed to execute a deployment."""

    mode: DeployMode
    namespace: str = "default"
    # Docker-image fields
    image: str = ""
    tag: str = "latest"
    replicas: int = 1
    app_name: str = ""
    # Helm fields
    chart: str = ""
    release_name: str = ""
    helm_values: dict[str, str] | None = None
    values_file: Path | None = None
    # Manifest fields
    manifest_yaml: str = ""
    # Common
    dry_run: bool = False


# ── Workers ──────────────────────────────────────────────────────────────────

class _DeployWorker(BaseWorker):
    """Executes the actual deployment in a background thread."""

    def __init__(self, spec: DeploySpec) -> None:
        super().__init__()
        self._spec = spec

    def run_task(self) -> str:
        s = self._spec
        if s.mode == DeployMode.DOCKER_IMAGE:
            return self._deploy_docker_image(s)
        if s.mode == DeployMode.HELM_CHART:
            return self._deploy_helm(s)
        if s.mode == DeployMode.MANIFEST:
            return self._deploy_manifest(s)
        return "Unknown deploy mode."

    @staticmethod
    def _deploy_docker_image(s: DeploySpec) -> str:
        image_ref = f"{s.image}:{s.tag}" if s.tag else s.image
        name = s.app_name or s.image.split("/")[-1].split(":")[0]
        manifest = {
            "apiVersion": "apps/v1",
            "kind": "Deployment",
            "metadata": {"name": name, "namespace": s.namespace},
            "spec": {
                "replicas": s.replicas,
                "selector": {"matchLabels": {"app": name}},
                "template": {
                    "metadata": {"labels": {"app": name}},
                    "spec": {
                        "containers": [{"name": name, "image": image_ref}]
                    },
                },
            },
        }
        if s.dry_run:
            return f"[DRY RUN] Would deploy '{name}' with image '{image_ref}'."
        apply_manifest(manifest, s.namespace)
        return f"Deployed '{name}' with image '{image_ref}' ({s.replicas} replica(s))."

    @staticmethod
    def _deploy_helm(s: DeploySpec) -> str:
        output = install_chart(
            release_name=s.release_name,
            chart=s.chart,
            namespace=s.namespace,
            values=s.helm_values,
            values_file=s.values_file,
            dry_run=s.dry_run,
        )
        prefix = "[DRY RUN] " if s.dry_run else ""
        return f"{prefix}Helm install '{s.release_name}' from chart '{s.chart}' completed."

    @staticmethod
    def _deploy_manifest(s: DeploySpec) -> str:
        parsed = yaml.safe_load(s.manifest_yaml)
        if not isinstance(parsed, dict):
            return "Invalid YAML manifest."
        if s.dry_run:
            kind = parsed.get("kind", "?")
            name = parsed.get("metadata", {}).get("name", "?")
            return f"[DRY RUN] Would apply {kind} '{name}'."
        apply_manifest(parsed, s.namespace)
        kind = parsed.get("kind", "?")
        name = parsed.get("metadata", {}).get("name", "?")
        return f"Applied {kind} '{name}' to namespace '{s.namespace}'."


# ── ViewModel ────────────────────────────────────────────────────────────────

class AppDeployViewModel(QObject):
    """
    ViewModel for the Application Deployment wizard.

    Signals:
        deploy_started:        Emitted when deployment begins.
        deploy_completed (str): Emitted with a success description.
        deploy_failed (str):   Emitted with an error message.
        progress_log (str):    Emitted with log lines during execution.
    """

    deploy_started: pyqtSignal = pyqtSignal()
    deploy_completed: pyqtSignal = pyqtSignal(str)
    deploy_failed: pyqtSignal = pyqtSignal(str)
    progress_log: pyqtSignal = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker: _DeployWorker | None = None

    def execute(self, spec: DeploySpec) -> None:
        """Start an async deployment."""
        self.deploy_started.emit()
        self.progress_log.emit(f"Starting {spec.mode.name} deployment…")
        self._worker = _DeployWorker(spec)
        self._worker.finished.connect(self._on_finished)
        self._worker.error.connect(self._on_error)
        self._worker.start()

    def _on_finished(self, result: Any) -> None:
        self.progress_log.emit(str(result))
        self.deploy_completed.emit(str(result))

    def _on_error(self, msg: str) -> None:
        self.progress_log.emit(f"ERROR: {msg}")
        self.deploy_failed.emit(msg)

