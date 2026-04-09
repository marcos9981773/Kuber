"""
kuber/views/common/base_worker.py
Base QThread worker for all async operations in Kuber.
"""
from __future__ import annotations

import logging
import traceback
from typing import Any, ClassVar

from PyQt5.QtCore import QThread, pyqtSignal

logger = logging.getLogger(__name__)


class BaseWorker(QThread):
    """
    Abstract base class for all background operations.

    Subclass and implement :meth:`run_task` to perform work off the main thread.
    Results and errors are communicated back via Qt signals.

    A class-level ``_active`` set keeps strong references to every running
    worker so that Python's GC never destroys a ``QThread`` that is still
    executing.

    Signals:
        started:          Emitted when the worker begins execution.
        finished (object): Emitted with the return value of :meth:`run_task`.
        error (str):      Emitted with a user-friendly error message on failure.
        progress (int):   Emitted with a 0-100 progress value (optional).

    Example::

        class LoadPodsWorker(BaseWorker):
            def run_task(self) -> list:
                return pods_core.list_pods(namespace="default")

        worker = LoadPodsWorker()
        worker.finished.connect(self._on_pods_loaded)
        worker.error.connect(self._on_error)
        worker.start()
    """

    # Prevent running workers from being garbage-collected
    _active: ClassVar[set[BaseWorker]] = set()

    finished: pyqtSignal = pyqtSignal(object)
    error: pyqtSignal = pyqtSignal(str)
    progress: pyqtSignal = pyqtSignal(int)

    def start(self, priority: QThread.Priority = QThread.InheritPriority) -> None:  # type: ignore[attr-defined]
        """Register self before starting so GC cannot destroy a running thread."""
        BaseWorker._active.add(self)
        super().start(priority)

    def run(self) -> None:
        """QThread entry point — calls run_task and emits results."""
        try:
            result = self.run_task()
            self.finished.emit(result)
        except Exception as exc:
            logger.error(
                f"Worker {self.__class__.__name__} failed: {exc}\n{traceback.format_exc()}"
            )
            self.error.emit(str(exc))
        finally:
            BaseWorker._active.discard(self)

    def run_task(self) -> Any:
        """
        Override this method to implement the background work.

        Returns:
            Any value — will be emitted via the ``finished`` signal.

        Raises:
            Any exception — will be caught and emitted via the ``error`` signal.
        """
        raise NotImplementedError(f"{self.__class__.__name__} must implement run_task()")

