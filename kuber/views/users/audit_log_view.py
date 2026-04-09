"""
kuber/views/users/audit_log_view.py
View for RBAC-related audit events from the Kubernetes cluster.

Note: True audit logs require kube-apiserver audit policy configuration.
This view filters cluster Events for RBAC-related items (Forbidden, Unauthorized, etc.).
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

from kuber.core.kubernetes.events import EventInfo
from kuber.models.resource_model import ResourceFilterProxy, ResourceTableModel
from kuber.viewmodels.user_vm import UserViewModel
from kuber.views.common.loading_overlay import LoadingOverlay
from kuber.views.common.namespace_selector import NamespaceSelector


class AuditLogView(QWidget):
    """Table view for RBAC-related cluster events (audit-style)."""

    def __init__(
        self, view_model: UserViewModel, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._model = ResourceTableModel(
            columns=[
                "namespace", "type", "reason", "involved_object",
                "message", "source", "count", "age",
            ],
        )
        self._proxy = ResourceFilterProxy(self)
        self._proxy.setSourceModel(self._model)
        self._setup_ui()
        self._setup_accessibility()
        self._connect_signals()

    # ── UI ────────────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(self.tr("Audit Log"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        info = QLabel(self.tr(
            "Shows cluster events filtered for RBAC-related activity. "
            "Full audit logging requires kube-apiserver audit policy configuration."
        ))
        info.setWordWrap(True)
        info.setObjectName("infoLabel")
        layout.addWidget(info)

        # Filters
        filter_row = QHBoxLayout()
        self._ns_selector = NamespaceSelector()
        self._ns_selector.namespace_changed.connect(self._on_ns_changed)
        filter_row.addWidget(self._ns_selector)

        self._type_combo = QComboBox()
        self._type_combo.addItem(self.tr("All Types"), "")
        self._type_combo.addItem(self.tr("⚠ Warning"), "Warning")
        self._type_combo.addItem(self.tr("ℹ Normal"), "Normal")
        self._type_combo.setAccessibleName(self.tr("Event type filter"))
        self._type_combo.currentTextChanged.connect(self._on_type_changed)
        filter_row.addWidget(self._type_combo)

        filter_row.addStretch()

        self._btn_refresh = QPushButton(self.tr("↺ Refresh"))
        self._btn_refresh.setObjectName("btnPrimary")
        self._btn_refresh.setAccessibleName(self.tr("Refresh audit events"))
        self._btn_refresh.clicked.connect(lambda: self._vm.load_audit_events())
        filter_row.addWidget(self._btn_refresh)

        layout.addLayout(filter_row)

        # Table
        self._table = QTableView()
        self._table.setObjectName("auditLogTable")
        self._table.setModel(self._proxy)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self._table, stretch=1)

        self._status = QLabel("")
        layout.addWidget(self._status)

        self._overlay = LoadingOverlay(self)

    def _setup_accessibility(self) -> None:
        self._table.setAccessibleName(self.tr("Audit log table"))
        self._table.setAccessibleDescription(
            self.tr("Lists RBAC-related cluster events for audit purposes."),
        )
        self._ns_selector.setAccessibleName(self.tr("Namespace filter"))

    def _connect_signals(self) -> None:
        self._vm.audit_events_loaded.connect(self._on_events_loaded)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._on_error)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_events_loaded(self, events: list[EventInfo]) -> None:
        self._model.set_items(events)
        self._table.resizeColumnsToContents()
        self._status.setText(self.tr("{0} event(s)").format(len(events)))

    def _on_loading_changed(self, loading: bool) -> None:
        if loading:
            self._overlay.show_with_message(self.tr("Loading audit events…"))
        else:
            self._overlay.hide()

    def _on_error(self, msg: str) -> None:
        from kuber.views.common.error_dialog import ErrorDialog
        ErrorDialog.show_error(
            title=self.tr("Audit Log"), message=msg, parent=self,
        )

    def _on_ns_changed(self, ns: str) -> None:
        self._vm.set_namespace(ns)
        self._vm.load_audit_events()

    def _on_type_changed(self) -> None:
        type_val = self._type_combo.currentData() or ""
        self._proxy.set_filter_text(type_val)

