"""
kuber/viewmodels/resource_vm.py
Base ViewModel for Kubernetes resource views (Pods, Deployments, Services, ConfigMaps).
Subclasses only override _fetch_items() and _delete_item().
"""
from __future__ import annotations

import logging
from typing import Any

from PyQt5.QtCore import QObject, pyqtSignal

from kuber.core.kubernetes.clusters import list_namespaces
from kuber.views.common.base_worker import BaseWorker

logger = logging.getLogger(__name__)


# ── Generic workers ──────────────────────────────────────────────────────────

class _FetchWorker(BaseWorker):
    """Fetches a list of resources in a background thread."""

    def __init__(self, fetch_fn, namespace: str) -> None:
        super().__init__()
        self._fetch_fn = fetch_fn
        self._namespace = namespace

    def run_task(self) -> list:
        return self._fetch_fn(namespace=self._namespace)


class _DeleteWorker(BaseWorker):
    """Deletes a single resource in a background thread."""

    def __init__(self, delete_fn, name: str, namespace: str) -> None:
        super().__init__()
        self._delete_fn = delete_fn
        self._name = name
        self._namespace = namespace

    def run_task(self) -> str:
        self._delete_fn(name=self._name, namespace=self._namespace)
        return self._name


class _ActionWorker(BaseWorker):
    """Executes an arbitrary action (scale, update, etc.) in background."""

    def __init__(self, action_fn, **kwargs: Any) -> None:
        super().__init__()
        self._action_fn = action_fn
        self._kwargs = kwargs

    def run_task(self) -> Any:
        return self._action_fn(**self._kwargs)


# ── Base ViewModel ───────────────────────────────────────────────────────────

class ResourceViewModel(QObject):
    """
    Abstract base ViewModel for any Kubernetes resource list.

    Signals:
        items_loaded (list):         Resource items loaded.
        item_deleted (str):          Resource name that was deleted.
        action_completed (str):      Description of completed action.
        loading_changed (bool):      True while a background op runs.
        error_occurred (str):        User-friendly error message.
        namespaces_loaded (list):    Available namespace list.
    """

    items_loaded: pyqtSignal = pyqtSignal(list)
    item_deleted: pyqtSignal = pyqtSignal(str)
    action_completed: pyqtSignal = pyqtSignal(str)
    loading_changed: pyqtSignal = pyqtSignal(bool)
    error_occurred: pyqtSignal = pyqtSignal(str)
    namespaces_loaded: pyqtSignal = pyqtSignal(list)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._namespace: str = "all"
        self._worker: BaseWorker | None = None
        self._ns_worker: BaseWorker | None = None

    # ── Public actions ────────────────────────────────────────────────────────

    def set_namespace(self, namespace: str) -> None:
        self._namespace = namespace

    def load_items(self) -> None:
        """Fetch items for the current namespace."""
        worker = _FetchWorker(self._fetch_items, self._namespace)
        self._start(worker, self._on_items_loaded)

    def delete_item(self, name: str, namespace: str | None = None) -> None:
        """Delete a resource by name."""
        ns = namespace or self._namespace
        worker = _DeleteWorker(self._delete_item, name, ns)
        self._start(worker, self._on_item_deleted)

    def load_namespaces(self) -> None:
        """Fetch the namespace list from the cluster.

        Uses a dedicated worker so namespace loading is never cancelled
        by concurrent item or delete operations.
        """

        def _fetch(**_: Any) -> list[str]:
            return list_namespaces()

        if self._ns_worker and self._ns_worker.isRunning():
            try:
                self._ns_worker.finished.disconnect()
                self._ns_worker.error.disconnect()
            except TypeError:
                pass
        self._ns_worker = _FetchWorker(_fetch, self._namespace)
        self._ns_worker.finished.connect(self._on_ns_loaded)
        self._ns_worker.error.connect(self._on_error)
        self._ns_worker.start()

    # ── Override hooks ────────────────────────────────────────────────────────

    def _fetch_items(self, namespace: str) -> list:
        raise NotImplementedError

    def _delete_item(self, name: str, namespace: str) -> None:
        raise NotImplementedError

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_items_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.items_loaded.emit(result)

    def _on_item_deleted(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.item_deleted.emit(str(result))
        self.load_items()  # auto-refresh

    def _on_ns_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.namespaces_loaded.emit(result)

    def _on_action_done(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.action_completed.emit(str(result))
        self.load_items()

    def _on_error(self, message: str) -> None:
        self.loading_changed.emit(False)
        self.error_occurred.emit(message)

    # ── Worker management ─────────────────────────────────────────────────────

    def _start(self, worker: BaseWorker, on_finished) -> None:
        if self._worker and self._worker.isRunning():
            # Disconnect signals from old worker so stale results are ignored.
            # BaseWorker._active keeps the reference alive until run() finishes.
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

    def _run_action(self, action_fn, description: str = "", **kwargs: Any) -> None:
        """Convenience: run an arbitrary action in background."""
        worker = _ActionWorker(action_fn, **kwargs)
        self._start(worker, self._on_action_done)

