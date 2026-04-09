"""
kuber/viewmodels/cluster_vm.py
ViewModel for cluster management — loads contexts, switches clusters, polls status.
"""
from __future__ import annotations

import logging
from typing import Any

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from kuber.config.kube_config import (
    KubeConfigInfo,
    KubeContext,
    load_kube_config,
    switch_context,
)
from kuber.constants import CLUSTER_STATUS_POLL_INTERVAL_MS, KUBE_CONFIG_DEFAULT
from kuber.core.kubernetes.clusters import ClusterInfo, get_cluster_info
from kuber.views.common.base_worker import BaseWorker

logger = logging.getLogger(__name__)


# ── Workers ───────────────────────────────────────────────────────────────────

class _LoadConfigWorker(BaseWorker):
    """Loads kubeconfig from disk in a background thread."""

    def run_task(self) -> KubeConfigInfo:
        return load_kube_config(KUBE_CONFIG_DEFAULT)


class _SwitchContextWorker(BaseWorker):
    """Switches the active kubeconfig context in a background thread."""

    def __init__(self, context_name: str) -> None:
        super().__init__()
        self._context_name = context_name

    def run_task(self) -> str:
        switch_context(self._context_name)
        return self._context_name


class _LoadClusterInfoWorker(BaseWorker):
    """Fetches live cluster info (nodes, version) in a background thread."""

    def __init__(self, context_name: str, server_url: str) -> None:
        super().__init__()
        self._context_name = context_name
        self._server_url = server_url

    def run_task(self) -> ClusterInfo:
        return get_cluster_info(self._context_name, self._server_url)


# ── ViewModel ─────────────────────────────────────────────────────────────────

class ClusterViewModel(QObject):
    """
    ViewModel for the Cluster Management feature.

    Signals:
        contexts_loaded (list):   Emitted with list[KubeContext] after config load.
        context_switched (str):   Emitted with the new active context name.
        cluster_info_loaded (ClusterInfo): Emitted after live cluster data is fetched.
        loading_changed (bool):   True while an async operation is running.
        error_occurred (str):     User-friendly error message.
    """

    contexts_loaded: pyqtSignal = pyqtSignal(list)
    context_switched: pyqtSignal = pyqtSignal(str)
    cluster_info_loaded: pyqtSignal = pyqtSignal(object)
    loading_changed: pyqtSignal = pyqtSignal(bool)
    error_occurred: pyqtSignal = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._config_info: KubeConfigInfo | None = None
        self._worker: BaseWorker | None = None
        self._poll_timer = QTimer(self)
        self._connect_signals()

    def _connect_signals(self) -> None:
        self._poll_timer.timeout.connect(self._on_poll_timer)

    # ── Public actions ────────────────────────────────────────────────────────

    def load_contexts(self) -> None:
        """Trigger async loading of kubeconfig contexts."""
        self._start_worker(_LoadConfigWorker(), self._on_config_loaded)

    def switch_context(self, context_name: str) -> None:
        """Switch the active kubeconfig context asynchronously."""
        self._start_worker(
            _SwitchContextWorker(context_name),
            self._on_context_switched,
        )

    def refresh_cluster_info(self) -> None:
        """Fetch live cluster info for the currently active context."""
        if self._config_info and self._config_info.active_context_name:
            active = next(
                (c for c in self._config_info.contexts
                 if c.name == self._config_info.active_context_name),
                None,
            )
            if active:
                self._start_worker(
                    _LoadClusterInfoWorker(active.name, active.server),
                    self._on_cluster_info_loaded,
                )

    def start_polling(self) -> None:
        """Start polling cluster status every CLUSTER_STATUS_POLL_INTERVAL_MS."""
        self._poll_timer.start(CLUSTER_STATUS_POLL_INTERVAL_MS)

    def stop_polling(self) -> None:
        """Stop the cluster status polling timer."""
        self._poll_timer.stop()

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_config_loaded(self, result: Any) -> None:
        self._config_info = result
        self.loading_changed.emit(False)
        self.contexts_loaded.emit(result.contexts)
        logger.info(f"Loaded {len(result.contexts)} kubeconfig context(s).")

    def _on_context_switched(self, result: Any) -> None:
        context_name: str = result
        if self._config_info:
            for ctx in self._config_info.contexts:
                ctx.is_active = ctx.name == context_name
            self._config_info.active_context_name = context_name
        self.loading_changed.emit(False)
        self.context_switched.emit(context_name)
        self.refresh_cluster_info()

    def _on_cluster_info_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.cluster_info_loaded.emit(result)

    def _on_poll_timer(self) -> None:
        if self._worker is None or not self._worker.isRunning():
            self.refresh_cluster_info()

    def _on_worker_error(self, message: str) -> None:
        self.loading_changed.emit(False)
        self.error_occurred.emit(message)

    # ── Helper ───────────────────────────────────────────────────────────────

    def _start_worker(self, worker: BaseWorker, on_finished) -> None:  # type: ignore[type-arg]
        """Start a worker, replacing any existing one."""
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except TypeError:
                pass
        self._worker = worker
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(self._on_worker_error)
        self.loading_changed.emit(True)
        self._worker.start()

