"""
kuber/views/cluster/cluster_switcher.py
Toolbar widget for switching the active Kubernetes context.
"""
from __future__ import annotations

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QComboBox, QHBoxLayout, QLabel, QWidget

from kuber.config.kube_config import KubeContext
from kuber.viewmodels.cluster_vm import ClusterViewModel


class ClusterSwitcher(QWidget):
    """
    Compact toolbar widget showing the active context in a QComboBox.

    Emits :attr:`context_selected` when the user picks a different context.
    Designed to be embedded directly in :class:`~kuber.views.main_window.MainWindow`.
    """

    context_selected: pyqtSignal = pyqtSignal(str)

    def __init__(self, view_model: ClusterViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._updating = False
        self._setup_ui()
        self._setup_accessibility()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        icon = QLabel("☸")
        icon.setObjectName("switcherIcon")
        layout.addWidget(icon)

        self._combo = QComboBox()
        self._combo.setObjectName("clusterCombo")
        self._combo.setMinimumWidth(200)
        self._combo.setMaximumWidth(320)
        self._combo.currentTextChanged.connect(self._on_combo_changed)
        layout.addWidget(self._combo)

    def _setup_accessibility(self) -> None:
        self._combo.setAccessibleName(self.tr("Active Kubernetes context selector"))
        self._combo.setAccessibleDescription(
            self.tr("Select a cluster context to switch to it.")
        )

    def _connect_signals(self) -> None:
        self._vm.contexts_loaded.connect(self._on_contexts_loaded)
        self._vm.context_switched.connect(self._on_context_switched)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_contexts_loaded(self, contexts: list[KubeContext]) -> None:
        self._updating = True
        self._combo.clear()
        active_idx = 0
        for i, ctx in enumerate(contexts):
            self._combo.addItem(ctx.name)
            if ctx.is_active:
                active_idx = i
        self._combo.setCurrentIndex(active_idx)
        self._updating = False

    def _on_context_switched(self, context_name: str) -> None:
        self._updating = True
        idx = self._combo.findText(context_name)
        if idx >= 0:
            self._combo.setCurrentIndex(idx)
        self._updating = False

    def _on_combo_changed(self, text: str) -> None:
        if not self._updating and text:
            self.context_selected.emit(text)
            self._vm.switch_context(text)

