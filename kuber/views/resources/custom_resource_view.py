"""
kuber/views/resources/custom_resource_view.py
Dynamic view for browsing any Custom Resource Definition.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QComboBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from kuber.core.kubernetes.custom_resources import CRDInfo, CustomResourceInstance
from kuber.models.resource_model import ResourceFilterProxy, ResourceTableModel
from kuber.views.common.loading_overlay import LoadingOverlay
from kuber.views.common.namespace_selector import NamespaceSelector
from kuber.views.common.resource_detail_panel import ResourceDetailPanel
from kuber.views.common.search_bar import SearchBar


class CustomResourceView(QWidget):
    """
    Dynamic table view for any CRD selected from a dropdown.

    The CRD list must be loaded externally and passed via :meth:`set_crds`.
    When the user selects a CRD the view emits a signal / calls a callback
    so the parent (or ViewModel) can fetch instances.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._crds: list[CRDInfo] = []
        self._model = ResourceTableModel(
            columns=["name", "namespace", "kind", "api_version"],
        )
        self._proxy = ResourceFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._setup_ui()
        self._setup_accessibility()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(self.tr("Custom Resources"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # CRD selector row
        selector_row = QHBoxLayout()

        self._crd_combo = QComboBox()
        self._crd_combo.setMinimumWidth(250)
        self._crd_combo.currentIndexChanged.connect(self._on_crd_changed)
        selector_row.addWidget(QLabel(self.tr("CRD:")))
        selector_row.addWidget(self._crd_combo, stretch=1)

        self._ns_selector = NamespaceSelector()
        selector_row.addWidget(self._ns_selector)

        self._search = SearchBar(placeholder=self.tr("Filter…"))
        self._search.search_changed.connect(self._proxy.set_filter_text)
        selector_row.addWidget(self._search, stretch=1)

        self._btn_refresh = QPushButton(self.tr("↺ Refresh"))
        self._btn_refresh.setObjectName("btnPrimary")
        selector_row.addWidget(self._btn_refresh)

        layout.addLayout(selector_row)

        # Table + detail panel
        from PyQt5.QtCore import Qt
        from PyQt5.QtWidgets import QSplitter

        self._table = QTableView()
        self._table.setObjectName("customResourceTable")
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)

        self._detail = ResourceDetailPanel()

        splitter = QSplitter(Qt.Horizontal)
        splitter.addWidget(self._table)
        splitter.addWidget(self._detail)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)

        # Status
        self._status = QLabel("")
        self._status.setObjectName("resourceStatus")
        layout.addWidget(self._status)

        self._overlay = LoadingOverlay(self)

    def _setup_accessibility(self) -> None:
        self._crd_combo.setAccessibleName(self.tr("Custom Resource Definition selector"))
        self._table.setAccessibleName(self.tr("Custom resource instances table"))
        self._btn_refresh.setAccessibleName(self.tr("Refresh custom resources"))
        self._ns_selector.setAccessibleName(self.tr("Namespace filter"))

    # ── Public API ───────────────────────────────────────────────────────────

    def set_crds(self, crds: list[CRDInfo]) -> None:
        """Populate the CRD selector dropdown."""
        self._crds = crds
        self._crd_combo.blockSignals(True)
        self._crd_combo.clear()
        for crd in crds:
            label = f"{crd.kind} ({crd.group}/{crd.version})"
            self._crd_combo.addItem(label)
        self._crd_combo.blockSignals(False)
        if crds:
            self._crd_combo.setCurrentIndex(0)

    def set_instances(self, instances: list[CustomResourceInstance]) -> None:
        """Populate the table with custom resource instances."""
        self._model.set_items(instances)
        self._table.resizeColumnsToContents()
        self._status.setText(
            self.tr("{0} resource(s)").format(len(instances)),
        )

    def selected_crd(self) -> CRDInfo | None:
        """Return the currently selected CRD, if any."""
        idx = self._crd_combo.currentIndex()
        if 0 <= idx < len(self._crds):
            return self._crds[idx]
        return None

    def set_loading(self, loading: bool) -> None:
        """Toggle loading overlay."""
        if loading:
            self._overlay.show_with_message(self.tr("Loading…"))
        else:
            self._overlay.hide()

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_crd_changed(self, index: int) -> None:
        """Called when the user picks a different CRD."""
        self._model.set_items([])
        self._detail.clear()

