"""
kuber/views/cluster/cluster_list_view.py
Table view for listing and switching Kubernetes contexts.
"""
from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from kuber.models.cluster_model import ClusterModel
from kuber.viewmodels.cluster_vm import ClusterViewModel
from kuber.views.common.loading_overlay import LoadingOverlay

logger = logging.getLogger(__name__)


class ClusterListView(QWidget):
    """
    Displays all available Kubernetes contexts in a table.

    Allows the user to switch the active context and refresh cluster status.
    """

    def __init__(self, view_model: ClusterViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._model = ClusterModel(self)
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()
        self._connect_signals()
        self._vm.load_contexts()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Header row ────────────────────────────────────────────────────
        header_row = QHBoxLayout()
        title = QLabel(self.tr("Clusters"))
        title.setObjectName("pageTitle")
        header_row.addWidget(title)
        header_row.addStretch()

        self._btn_refresh = QPushButton(self.tr("↺ Refresh"))
        self._btn_refresh.setObjectName("btnPrimary")
        self._btn_refresh.clicked.connect(self._on_refresh_clicked)
        header_row.addWidget(self._btn_refresh)

        layout.addLayout(header_row)

        # ── Status label ──────────────────────────────────────────────────
        self._status_label = QLabel("")
        self._status_label.setObjectName("clusterStatusLabel")
        layout.addWidget(self._status_label)

        # ── Table ─────────────────────────────────────────────────────────
        self._table = QTableView()
        self._table.setObjectName("clusterTable")
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self._table.doubleClicked.connect(self._on_row_double_clicked)
        layout.addWidget(self._table)

        # ── Action buttons ─────────────────────────────────────────────────
        action_row = QHBoxLayout()
        self._btn_switch = QPushButton(self.tr("Switch Context"))
        self._btn_switch.setObjectName("btnPrimary")
        self._btn_switch.setEnabled(False)
        self._btn_switch.clicked.connect(self._on_switch_clicked)
        action_row.addWidget(self._btn_switch)
        action_row.addStretch()
        layout.addLayout(action_row)

        # ── Loading overlay ────────────────────────────────────────────────
        self._overlay = LoadingOverlay(self)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    def _setup_accessibility(self) -> None:
        self._table.setAccessibleName(self.tr("Kubernetes clusters table"))
        self._table.setAccessibleDescription(
            self.tr("Lists all available Kubernetes contexts. Double-click to switch context.")
        )
        self._btn_refresh.setAccessibleName(self.tr("Refresh clusters button"))
        self._btn_switch.setAccessibleName(self.tr("Switch to selected cluster context"))

    def _setup_tab_order(self) -> None:
        # Tab: Refresh → Table → Switch
        QWidget.setTabOrder(self._btn_refresh, self._table)
        QWidget.setTabOrder(self._table, self._btn_switch)

    def _connect_signals(self) -> None:
        self._vm.contexts_loaded.connect(self._on_contexts_loaded)
        self._vm.context_switched.connect(self._on_context_switched)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._on_error)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_contexts_loaded(self, contexts: list) -> None:
        from kuber.config.kube_config import KubeConfigInfo
        active = next((c.name for c in contexts if c.is_active), "")
        self._model.set_contexts(contexts, active)
        self._table.resizeColumnsToContents()
        count = len(contexts)
        self._status_label.setText(
            self.tr("{0} cluster context(s) found.").format(count)
        )

    def _on_context_switched(self, context_name: str) -> None:
        self._status_label.setText(
            self.tr("Switched to context: {0}").format(context_name)
        )
        self._model.set_contexts(
            self._model._contexts,
            context_name,
        )

    def _on_loading_changed(self, is_loading: bool) -> None:
        self._btn_refresh.setEnabled(not is_loading)
        self._btn_switch.setEnabled(not is_loading and self._has_selection())
        if is_loading:
            self._overlay.show_with_message(self.tr("Loading clusters…"))
        else:
            self._overlay.hide()

    def _on_error(self, message: str) -> None:
        from kuber.views.common.error_dialog import ErrorDialog
        ErrorDialog.show_error(
            title=self.tr("Cluster Error"),
            message=message,
            parent=self,
        )

    def _on_selection_changed(self) -> None:
        self._btn_switch.setEnabled(self._has_selection())

    def _on_switch_clicked(self) -> None:
        ctx = self._selected_context()
        if ctx:
            self._vm.switch_context(ctx.name)

    def _on_refresh_clicked(self) -> None:
        self._vm.load_contexts()

    def _on_row_double_clicked(self, index) -> None:
        ctx = self._model.context_at(index.row())
        if ctx and not ctx.is_active:
            self._vm.switch_context(ctx.name)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _has_selection(self) -> bool:
        return self._table.selectionModel().hasSelection()

    def _selected_context(self):  # type: ignore[return]
        indexes = self._table.selectedIndexes()
        if indexes:
            return self._model.context_at(indexes[0].row())
        return None

