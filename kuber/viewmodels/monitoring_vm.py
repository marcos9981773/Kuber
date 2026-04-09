"""
kuber/viewmodels/monitoring_vm.py
ViewModel for the Monitoring & Logging feature.
"""
from __future__ import annotations

import logging
from typing import Any

from PyQt5.QtCore import QObject, QTimer, pyqtSignal

from kuber.core.kubernetes.clusters import list_namespaces
from kuber.core.kubernetes.events import EventInfo, list_events
from kuber.core.kubernetes.logs import get_pod_logs, stream_pod_logs
from kuber.core.kubernetes.metrics import (
    NodeMetrics,
    PodMetrics,
    list_node_metrics,
    list_pod_metrics,
)
from kuber.core.kubernetes.pods import PodInfo, list_pods
from kuber.views.common.base_worker import BaseWorker

logger = logging.getLogger(__name__)

_METRICS_POLL_MS = 10_000  # 10 seconds


class _MetricsWorker(BaseWorker):
    def __init__(self, namespace: str) -> None:
        super().__init__()
        self._ns = namespace

    def run_task(self) -> dict:
        pods = list_pod_metrics(namespace=self._ns)
        nodes = list_node_metrics()
        return {"pods": pods, "nodes": nodes}


class _EventsWorker(BaseWorker):
    def __init__(self, namespace: str) -> None:
        super().__init__()
        self._ns = namespace

    def run_task(self) -> list[EventInfo]:
        return list_events(namespace=self._ns)


class _LogWorker(BaseWorker):
    def __init__(self, pod: str, ns: str, container: str | None, lines: int) -> None:
        super().__init__()
        self._pod = pod
        self._ns = ns
        self._container = container
        self._lines = lines

    def run_task(self) -> str:
        return get_pod_logs(
            name=self._pod,
            namespace=self._ns,
            container=self._container,
            tail_lines=self._lines,
        )


class _NamespacesWorker(BaseWorker):
    """Fetches all namespace names."""

    def run_task(self) -> list[str]:
        return list_namespaces()


class _PodsWorker(BaseWorker):
    """Fetches pod names for a given namespace."""

    def __init__(self, namespace: str) -> None:
        super().__init__()
        self._ns = namespace

    def run_task(self) -> list[PodInfo]:
        return list_pods(namespace=self._ns)


class MonitoringViewModel(QObject):
    """
    ViewModel for metrics, logs, and events.

    Signals:
        metrics_loaded (dict):  {'pods': list[PodMetrics], 'nodes': list[NodeMetrics]}
        events_loaded (list):   list[EventInfo]
        logs_loaded (str):      Pod log text
        namespaces_loaded (list): Available namespace list
        pods_loaded (list):     Pod list for the current namespace
        loading_changed (bool): True while async op runs
        error_occurred (str):   User-friendly error
    """

    metrics_loaded: pyqtSignal = pyqtSignal(dict)
    events_loaded: pyqtSignal = pyqtSignal(list)
    logs_loaded: pyqtSignal = pyqtSignal(str)
    namespaces_loaded: pyqtSignal = pyqtSignal(list)
    pods_loaded: pyqtSignal = pyqtSignal(list)
    loading_changed: pyqtSignal = pyqtSignal(bool)
    error_occurred: pyqtSignal = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._namespace = "default"
        self._worker: BaseWorker | None = None
        self._ns_worker: BaseWorker | None = None
        self._pods_worker: BaseWorker | None = None
        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self.load_metrics)

    def set_namespace(self, ns: str) -> None:
        self._namespace = ns

    # ── Actions ──────────────────────────────────────────────────────────────

    def load_metrics(self) -> None:
        w = _MetricsWorker(self._namespace)
        self._start(w, self._on_metrics)

    def load_events(self) -> None:
        w = _EventsWorker(self._namespace)
        self._start(w, self._on_events)

    def load_logs(
        self, pod: str, namespace: str, container: str | None = None, lines: int = 200
    ) -> None:
        w = _LogWorker(pod, namespace, container, lines)
        self._start(w, self._on_logs)

    def load_namespaces(self) -> None:
        """Fetch namespace list. Uses a dedicated worker so it is never
        cancelled by other operations."""
        if self._ns_worker and self._ns_worker.isRunning():
            try:
                self._ns_worker.finished.disconnect()
                self._ns_worker.error.disconnect()
            except TypeError:
                pass
        self._ns_worker = _NamespacesWorker()
        self._ns_worker.finished.connect(self._on_namespaces)
        self._ns_worker.error.connect(self._on_error)
        self._ns_worker.start()

    def load_pods(self, namespace: str | None = None) -> None:
        """Fetch pod list for *namespace*. Uses a dedicated worker so it is
        never cancelled by log / metrics operations."""
        ns = namespace or self._namespace
        if self._pods_worker and self._pods_worker.isRunning():
            try:
                self._pods_worker.finished.disconnect()
                self._pods_worker.error.disconnect()
            except TypeError:
                pass
        self._pods_worker = _PodsWorker(ns)
        self._pods_worker.finished.connect(self._on_pods)
        self._pods_worker.error.connect(self._on_error)
        self._pods_worker.start()

    def start_metrics_polling(self) -> None:
        self._poll_timer.start(_METRICS_POLL_MS)

    def stop_metrics_polling(self) -> None:
        self._poll_timer.stop()

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_metrics(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.metrics_loaded.emit(result)

    def _on_events(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.events_loaded.emit(result)

    def _on_logs(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.logs_loaded.emit(str(result))

    def _on_namespaces(self, result: Any) -> None:
        self.namespaces_loaded.emit(result)

    def _on_pods(self, result: Any) -> None:
        self.pods_loaded.emit(result)

    def _on_error(self, msg: str) -> None:
        self.loading_changed.emit(False)
        self.error_occurred.emit(msg)

    def _start(self, worker: BaseWorker, on_finished) -> None:
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except TypeError:
                pass
        self._worker = worker
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(self._on_error)
        self.loading_changed.emit(True)
        self._worker.start()

