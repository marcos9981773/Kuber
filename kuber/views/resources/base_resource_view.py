"""
kuber/views/resources/base_resource_view.py
Abstract base view for any Kubernetes resource table page.
Subclasses only override _columns(), _on_delete(), and optionally add action buttons.
"""
from __future__ import annotations

import logging
from typing import Any

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QSplitter,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from kuber.models.resource_model import ResourceFilterProxy, ResourceTableModel
from kuber.viewmodels.resource_vm import ResourceViewModel
from kuber.views.common.loading_overlay import LoadingOverlay
from kuber.views.common.namespace_selector import NamespaceSelector
from kuber.views.common.resource_detail_panel import ResourceDetailPanel
from kuber.views.common.search_bar import SearchBar

logger = logging.getLogger(__name__)


class BaseResourceView(QWidget):
    """
    Reusable resource list page with:
    - Namespace selector
    - Search bar with debounce
    - QTableView with sort + filter proxy
    - Refresh / Delete buttons
    - Loading overlay

    Subclasses must set ``_title`` and ``_columns`` before calling ``super().__init__``.
    """

    _title: str = "Resources"
    _columns: list[str] = []

    def __init__(self, view_model: ResourceViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._model = ResourceTableModel(columns=list(self._columns))
        self._proxy = ResourceFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()
        self._connect_signals()
        self._vm.load_namespaces()
        self._vm.load_items()

    # ── UI setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Row 1: title + refresh
        header = QHBoxLayout()
        title = QLabel(self.tr(self._title))
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        self._btn_refresh = QPushButton(self.tr("↺ Refresh"))
        self._btn_refresh.setObjectName("btnPrimary")
        self._btn_refresh.clicked.connect(self._on_refresh)
        header.addWidget(self._btn_refresh)
        layout.addLayout(header)

        # Row 2: namespace selector + search bar
        filter_row = QHBoxLayout()
        self._ns_selector = NamespaceSelector()
        self._ns_selector.namespace_changed.connect(self._on_namespace_changed)
        filter_row.addWidget(self._ns_selector)

        self._search = SearchBar(placeholder=self.tr("Filter resources…"))
        self._search.search_changed.connect(self._proxy.set_filter_text)
        filter_row.addWidget(self._search, stretch=1)
        layout.addLayout(filter_row)

        # Table + detail panel in a splitter
        self._table = QTableView()
        self._table.setObjectName("resourceTable")
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)

        self._detail_panel = ResourceDetailPanel()

        self._splitter = QSplitter(Qt.Horizontal)
        self._splitter.setObjectName("resourceSplitter")
        self._splitter.addWidget(self._table)
        self._splitter.addWidget(self._detail_panel)
        self._splitter.setStretchFactor(0, 3)
        self._splitter.setStretchFactor(1, 1)
        layout.addWidget(self._splitter, stretch=1)

        # Action row
        self._action_row = QHBoxLayout()
        self._btn_delete = QPushButton(self.tr("🗑 Delete"))
        self._btn_delete.setObjectName("btnDanger")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        self._action_row.addWidget(self._btn_delete)
        self._add_custom_actions(self._action_row)
        self._action_row.addStretch()
        layout.addLayout(self._action_row)

        # Status label
        self._status_label = QLabel("")
        self._status_label.setObjectName("resourceStatus")
        layout.addWidget(self._status_label)

        # Loading overlay
        self._overlay = LoadingOverlay(self)

    def _add_custom_actions(self, layout: QHBoxLayout) -> None:
        """Override to add extra action buttons (scale, edit, etc.)."""

    def _setup_accessibility(self) -> None:
        self._table.setAccessibleName(
            self.tr("{0} table").format(self._title)
        )
        self._table.setAccessibleDescription(
            self.tr("Lists Kubernetes {0}. Use arrow keys to navigate rows.").format(
                self._title.lower()
            )
        )
        self._btn_refresh.setAccessibleName(self.tr("Refresh {0}").format(self._title))
        self._btn_delete.setAccessibleName(self.tr("Delete selected resource"))
        self._ns_selector.setAccessibleName(self.tr("Namespace filter"))
        self._search.setAccessibleName(self.tr("Text search filter"))

    def _setup_tab_order(self) -> None:
        QWidget.setTabOrder(self._ns_selector, self._search)
        QWidget.setTabOrder(self._search, self._btn_refresh)
        QWidget.setTabOrder(self._btn_refresh, self._table)
        QWidget.setTabOrder(self._table, self._btn_delete)

    def _connect_signals(self) -> None:
        self._vm.items_loaded.connect(self._on_items_loaded)
        self._vm.item_deleted.connect(self._on_item_deleted)
        self._vm.action_completed.connect(self._on_action_completed)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._on_error)
        self._vm.namespaces_loaded.connect(self._ns_selector.set_namespaces)
        self._table.selectionModel().selectionChanged.connect(self._on_selection_changed)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_items_loaded(self, items: list) -> None:
        self._model.set_items(items)
        self._table.resizeColumnsToContents()
        self._status_label.setText(
            self.tr("{0} {1} found.").format(len(items), self._title.lower())
        )

    def _on_item_deleted(self, name: str) -> None:
        self._status_label.setText(self.tr("Deleted: {0}").format(name))

    def _on_action_completed(self, desc: str) -> None:
        self._status_label.setText(self.tr("Done: {0}").format(desc))

    def _on_loading_changed(self, loading: bool) -> None:
        self._btn_refresh.setEnabled(not loading)
        if loading:
            self._overlay.show_with_message(self.tr("Loading {0}…").format(self._title.lower()))
        else:
            self._overlay.hide()

    def _on_error(self, msg: str) -> None:
        from kuber.views.common.error_dialog import ErrorDialog
        ErrorDialog.show_error(title=self._title, message=msg, parent=self)

    def _on_selection_changed(self) -> None:
        has = self._table.selectionModel().hasSelection()
        self._btn_delete.setEnabled(has)
        item = self._selected_item()
        self._detail_panel.set_resource(item)

    def _on_namespace_changed(self, namespace: str) -> None:
        self._vm.set_namespace(namespace)
        self._vm.load_items()

    def _on_refresh(self) -> None:
        self._vm.load_items()

    def _on_delete_clicked(self) -> None:
        item = self._selected_item()
        if not item:
            return
        name = getattr(item, "name", str(item))
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Delete '{0}'? This action cannot be undone.").format(name),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            ns = getattr(item, "namespace", self._vm._namespace)
            self._vm.delete_item(name, ns)

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _selected_item(self) -> Any | None:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            source_idx = self._proxy.mapToSource(indexes[0])
            return self._model.item_at(source_idx.row())
        return None

