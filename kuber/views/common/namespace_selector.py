"""
kuber/views/common/namespace_selector.py
Reusable namespace combo box that loads namespaces from the cluster.

Every instance auto-syncs with the global :class:`NamespaceStore` so that
selecting a namespace in *any* view updates all the others.
"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from kuber.views.common.namespace_store import NamespaceStore


class NamespaceSelector(QWidget):
    """
    Compact widget with a label + QComboBox for picking a namespace.

    Always includes an "all" option at the top.

    Signals:
        namespace_changed (str): Emitted when the user picks a different namespace.
    """

    namespace_changed: pyqtSignal = pyqtSignal(str)

    _ALL_NS = "all"

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._updating = False
        self._setup_ui()
        self._connect_store()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        label = QLabel(self.tr("Namespace:"))
        label.setObjectName("nsLabel")
        layout.addWidget(label)

        self._combo = QComboBox()
        self._combo.setObjectName("nsCombo")
        self._combo.setMinimumWidth(160)
        self._combo.setAccessibleName(self.tr("Namespace selector"))
        self._combo.setAccessibleDescription(
            self.tr("Choose a namespace to filter resources.")
        )
        self._combo.currentTextChanged.connect(self._on_changed)
        layout.addWidget(self._combo)

    def _connect_store(self) -> None:
        """Subscribe to the global namespace store."""
        store = NamespaceStore.instance()
        store.namespace_changed.connect(self._on_store_changed)

    def set_namespaces(self, namespaces: list[str]) -> None:
        """Populate the combo box with a namespace list (adds 'all' at top)."""
        self._updating = True
        current = self._combo.currentData() or self._ALL_NS

        # If the combo had no items yet, honour the global store namespace
        store = NamespaceStore.instance()
        if self._combo.count() == 0:
            current = store.current_namespace()

        self._combo.clear()
        self._combo.addItem(self.tr("All Namespaces"), self._ALL_NS)
        for ns in namespaces:
            self._combo.addItem(ns, ns)

        # Restore previous / global selection if still present
        idx = self._combo.findData(current)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        self._updating = False

    def current_namespace(self) -> str:
        """Return the currently selected namespace (or 'all')."""
        return self._combo.currentData() or self._ALL_NS

    def _on_changed(self) -> None:
        """Handle local combo change (user interaction or set_pod)."""
        if not self._updating:
            ns = self.current_namespace()
            self.namespace_changed.emit(ns)
            # Propagate to all other selectors via the store.
            # NamespaceStore.set_namespace is a no-op when the value is unchanged,
            # so this won't cause an infinite loop.
            NamespaceStore.instance().set_namespace(ns)

    def _on_store_changed(self, namespace: str) -> None:
        """Called when another selector changed the global namespace."""
        if self.current_namespace() != namespace:
            self._updating = True
            idx = self._combo.findData(namespace)
            if idx >= 0:
                self._combo.setCurrentIndex(idx)
            self._updating = False
            # Fire our own signal so the parent view reloads data
            self.namespace_changed.emit(namespace)

