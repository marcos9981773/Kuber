"""
kuber/views/users/users_view.py
ServiceAccounts list view with create / delete / refresh actions.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QInputDialog,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from kuber.core.kubernetes.rbac import ServiceAccountInfo
from kuber.models.resource_model import ResourceFilterProxy, ResourceTableModel
from kuber.viewmodels.user_vm import UserViewModel
from kuber.views.common.loading_overlay import LoadingOverlay
from kuber.views.common.namespace_selector import NamespaceSelector
from kuber.views.common.search_bar import SearchBar


class UsersView(QWidget):
    """Table view for Kubernetes ServiceAccounts with RBAC actions."""

    def __init__(
        self, view_model: UserViewModel | None = None, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model or UserViewModel()
        self._model = ResourceTableModel(
            columns=["name", "namespace", "secrets", "age"],
        )
        self._proxy = ResourceFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()
        self._connect_signals()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        # Header
        header = QHBoxLayout()
        title = QLabel(self.tr("Service Accounts"))
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        self._btn_refresh = QPushButton(self.tr("↺ Refresh"))
        self._btn_refresh.setObjectName("btnPrimary")
        self._btn_refresh.clicked.connect(self._on_refresh)
        header.addWidget(self._btn_refresh)
        layout.addLayout(header)

        # Filter row
        filter_row = QHBoxLayout()
        self._ns_selector = NamespaceSelector()
        self._ns_selector.namespace_changed.connect(self._on_ns_changed)
        filter_row.addWidget(self._ns_selector)

        self._search = SearchBar(placeholder=self.tr("Filter service accounts…"))
        self._search.search_changed.connect(self._proxy.set_filter_text)
        filter_row.addWidget(self._search, stretch=1)
        layout.addLayout(filter_row)

        # Table
        self._table = QTableView()
        self._table.setObjectName("serviceAccountsTable")
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self._table, stretch=1)

        # Actions row
        actions = QHBoxLayout()
        self._btn_create = QPushButton(self.tr("+ Create SA"))
        self._btn_create.setObjectName("btnPrimary")
        self._btn_create.clicked.connect(self._on_create_clicked)
        actions.addWidget(self._btn_create)

        self._btn_delete = QPushButton(self.tr("🗑 Delete"))
        self._btn_delete.setObjectName("btnDanger")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete_clicked)
        actions.addWidget(self._btn_delete)

        actions.addStretch()
        layout.addLayout(actions)

        # Status
        self._status = QLabel("")
        self._status.setObjectName("resourceStatus")
        layout.addWidget(self._status)

        self._overlay = LoadingOverlay(self)

    def _setup_accessibility(self) -> None:
        self._table.setAccessibleName(self.tr("Service accounts table"))
        self._table.setAccessibleDescription(
            self.tr("Lists Kubernetes service accounts. Use arrow keys to navigate.")
        )
        self._btn_refresh.setAccessibleName(self.tr("Refresh service accounts"))
        self._btn_create.setAccessibleName(self.tr("Create service account"))
        self._btn_delete.setAccessibleName(self.tr("Delete selected service account"))
        self._ns_selector.setAccessibleName(self.tr("Namespace filter"))
        self._search.setAccessibleName(self.tr("Text search filter"))

    def _setup_tab_order(self) -> None:
        QWidget.setTabOrder(self._ns_selector, self._search)
        QWidget.setTabOrder(self._search, self._btn_refresh)
        QWidget.setTabOrder(self._btn_refresh, self._table)
        QWidget.setTabOrder(self._table, self._btn_create)
        QWidget.setTabOrder(self._btn_create, self._btn_delete)

    def _connect_signals(self) -> None:
        self._vm.items_loaded.connect(self._on_items_loaded)
        self._vm.item_deleted.connect(self._on_item_deleted)
        self._vm.action_completed.connect(self._on_action_completed)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._on_error)
        self._table.selectionModel().selectionChanged.connect(
            self._on_selection_changed,
        )

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_items_loaded(self, items: list[ServiceAccountInfo]) -> None:
        self._model.set_items(items)
        self._table.resizeColumnsToContents()
        self._status.setText(
            self.tr("{0} service account(s) found.").format(len(items)),
        )

    def _on_item_deleted(self, name: str) -> None:
        self._status.setText(self.tr("Deleted: {0}").format(name))

    def _on_action_completed(self, desc: str) -> None:
        self._status.setText(self.tr("Done: {0}").format(desc))
        self._vm.load_items()

    def _on_loading_changed(self, loading: bool) -> None:
        self._btn_refresh.setEnabled(not loading)
        if loading:
            self._overlay.show_with_message(self.tr("Loading…"))
        else:
            self._overlay.hide()

    def _on_error(self, msg: str) -> None:
        from kuber.views.common.error_dialog import ErrorDialog
        ErrorDialog.show_error(
            title=self.tr("Service Accounts"), message=msg, parent=self,
        )

    def _on_selection_changed(self) -> None:
        self._btn_delete.setEnabled(
            self._table.selectionModel().hasSelection(),
        )

    def _on_ns_changed(self, ns: str) -> None:
        self._vm.set_namespace(ns)
        self._vm.load_items()

    def _on_refresh(self) -> None:
        self._vm.load_items()

    def _on_create_clicked(self) -> None:
        name, ok = QInputDialog.getText(
            self, self.tr("Create Service Account"),
            self.tr("Service Account name:"),
        )
        if ok and name.strip():
            self._vm.create_sa(name.strip())

    def _on_delete_clicked(self) -> None:
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return
        source_idx = self._proxy.mapToSource(indexes[0])
        item = self._model.item_at(source_idx.row())
        if not item:
            return
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Delete service account '{0}'? This cannot be undone.").format(
                item.name,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._vm.delete_item(item.name, item.namespace)

