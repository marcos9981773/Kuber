"""
kuber/views/backup/backup_view.py
Backup listing with create, restore, and delete actions.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QAbstractItemView,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMessageBox,
    QPushButton,
    QTableView,
    QVBoxLayout,
    QWidget,
)

from kuber.models.resource_model import ResourceTableModel
from kuber.services.backup_service import BackupManifest
from kuber.viewmodels.backup_vm import BackupViewModel
from kuber.views.common.loading_overlay import LoadingOverlay


class BackupView(QWidget):
    """View for managing Kuber backup archives."""

    def __init__(
        self, view_model: BackupViewModel | None = None, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model or BackupViewModel()
        self._model = ResourceTableModel(
            columns=["filename", "timestamp", "resource_count", "size_bytes"],
        )
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
        title = QLabel(self.tr("Backup & Restore"))
        title.setObjectName("pageTitle")
        header.addWidget(title)
        header.addStretch()

        self._btn_refresh = QPushButton(self.tr("↺ Refresh"))
        self._btn_refresh.setObjectName("btnPrimary")
        self._btn_refresh.clicked.connect(self._on_refresh)
        header.addWidget(self._btn_refresh)
        layout.addLayout(header)

        # Table
        self._table = QTableView()
        self._table.setObjectName("backupTable")
        self._table.setModel(self._model)
        self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setSelectionMode(QAbstractItemView.SingleSelection)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.setSortingEnabled(True)
        self._table.verticalHeader().hide()
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        layout.addWidget(self._table, stretch=1)

        # Actions
        actions = QHBoxLayout()

        self._btn_create = QPushButton(self.tr("📦 Create Backup"))
        self._btn_create.setObjectName("btnPrimary")
        self._btn_create.clicked.connect(self._on_create)
        actions.addWidget(self._btn_create)

        self._btn_restore = QPushButton(self.tr("♻ Restore"))
        self._btn_restore.setObjectName("btnPrimary")
        self._btn_restore.setEnabled(False)
        self._btn_restore.clicked.connect(self._on_restore)
        actions.addWidget(self._btn_restore)

        self._btn_delete = QPushButton(self.tr("🗑 Delete"))
        self._btn_delete.setObjectName("btnDanger")
        self._btn_delete.setEnabled(False)
        self._btn_delete.clicked.connect(self._on_delete)
        actions.addWidget(self._btn_delete)

        actions.addStretch()
        layout.addLayout(actions)

        # Status
        self._status = QLabel("")
        self._status.setObjectName("resourceStatus")
        layout.addWidget(self._status)

        self._overlay = LoadingOverlay(self)

    def _setup_accessibility(self) -> None:
        self._table.setAccessibleName(self.tr("Backup archives table"))
        self._table.setAccessibleDescription(
            self.tr("Lists available backup archives. Select one to restore or delete.")
        )
        self._btn_create.setAccessibleName(self.tr("Create new backup"))
        self._btn_restore.setAccessibleName(self.tr("Restore selected backup"))
        self._btn_delete.setAccessibleName(self.tr("Delete selected backup"))
        self._btn_refresh.setAccessibleName(self.tr("Refresh backup list"))

    def _setup_tab_order(self) -> None:
        QWidget.setTabOrder(self._btn_refresh, self._table)
        QWidget.setTabOrder(self._table, self._btn_create)
        QWidget.setTabOrder(self._btn_create, self._btn_restore)
        QWidget.setTabOrder(self._btn_restore, self._btn_delete)

    def _connect_signals(self) -> None:
        self._vm.backups_loaded.connect(self._on_backups_loaded)
        self._vm.backup_created.connect(self._on_backup_created)
        self._vm.restore_completed.connect(self._on_restore_completed)
        self._vm.backup_deleted.connect(self._on_backup_deleted)
        self._vm.loading_changed.connect(self._on_loading_changed)
        self._vm.error_occurred.connect(self._on_error)
        self._table.selectionModel().selectionChanged.connect(
            self._on_selection_changed,
        )

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_backups_loaded(self, backups: list[BackupManifest]) -> None:
        self._model.set_items(backups)
        self._table.resizeColumnsToContents()
        self._status.setText(
            self.tr("{0} backup(s) found.").format(len(backups)),
        )

    def _on_backup_created(self, manifest: BackupManifest) -> None:
        self._status.setText(
            self.tr("Backup created: {0} ({1} resources)").format(
                manifest.filename, manifest.resource_count,
            ),
        )

    def _on_restore_completed(self, count: int) -> None:
        self._status.setText(
            self.tr("{0} resource(s) restored successfully.").format(count),
        )

    def _on_backup_deleted(self, filename: str) -> None:
        self._status.setText(self.tr("Deleted: {0}").format(filename))

    def _on_loading_changed(self, loading: bool) -> None:
        self._btn_refresh.setEnabled(not loading)
        self._btn_create.setEnabled(not loading)
        if loading:
            self._overlay.show_with_message(self.tr("Working…"))
        else:
            self._overlay.hide()

    def _on_error(self, msg: str) -> None:
        from kuber.views.common.error_dialog import ErrorDialog
        ErrorDialog.show_error(
            title=self.tr("Backup"), message=msg, parent=self,
        )

    def _on_selection_changed(self) -> None:
        has = self._table.selectionModel().hasSelection()
        self._btn_restore.setEnabled(has)
        self._btn_delete.setEnabled(has)

    # ── Actions ──────────────────────────────────────────────────────────────

    def _on_refresh(self) -> None:
        self._vm.load_backups()

    def _on_create(self) -> None:
        self._vm.create_new_backup()

    def _on_restore(self) -> None:
        item = self._selected_item()
        if not item:
            return
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Restore"),
            self.tr(
                "Restore from '{0}'? This will create resources in the cluster."
            ).format(item.filename),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._vm.restore_from_backup(item.filename)

    def _on_delete(self) -> None:
        item = self._selected_item()
        if not item:
            return
        reply = QMessageBox.question(
            self,
            self.tr("Confirm Delete"),
            self.tr("Delete backup '{0}'? This cannot be undone.").format(
                item.filename,
            ),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply == QMessageBox.Yes:
            self._vm.delete_backup_file(item.filename)

    def _selected_item(self) -> BackupManifest | None:
        indexes = self._table.selectionModel().selectedRows()
        if indexes:
            return self._model.item_at(indexes[0].row())
        return None

