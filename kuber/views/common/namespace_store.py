"""
kuber/views/common/namespace_store.py
Singleton that holds the globally selected namespace.

When a user picks a namespace in *any* NamespaceSelector, the store
broadcasts the change so every other selector (and its parent view)
stays in sync.
"""
from __future__ import annotations

from PyQt5.QtCore import QObject, pyqtSignal


class NamespaceStore(QObject):
    """
    Application-wide namespace state.

    Signals:
        namespace_changed (str): Emitted when the global namespace changes.
    """

    namespace_changed: pyqtSignal = pyqtSignal(str)

    _instance: NamespaceStore | None = None

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._namespace: str = "all"

    # ── Singleton access ─────────────────────────────────────────────────────

    @classmethod
    def instance(cls) -> NamespaceStore:
        """Return the single shared instance, creating it on first call."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance  # type: ignore[return-value]

    @classmethod
    def reset(cls) -> None:
        """Destroy the singleton — useful for test isolation."""
        if cls._instance is not None:
            cls._instance.deleteLater()
            cls._instance = None

    # ── Public API ───────────────────────────────────────────────────────────

    def set_namespace(self, namespace: str) -> None:
        """Update the global namespace. No-op if the value is unchanged."""
        if self._namespace != namespace:
            self._namespace = namespace
            self.namespace_changed.emit(namespace)

    def current_namespace(self) -> str:
        """Return the currently selected global namespace."""
        return self._namespace

