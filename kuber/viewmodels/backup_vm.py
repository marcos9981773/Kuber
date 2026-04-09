"""
kuber/viewmodels/backup_vm.py
ViewModel for Backup & Restore operations.
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from PyQt5.QtCore import QObject, pyqtSignal

from kuber.services.backup_service import (
    BackupManifest,
    create_backup,
    delete_backup,
    list_backups,
    restore_backup,
)
from kuber.views.common.base_worker import BaseWorker

logger = logging.getLogger(__name__)


class _ListBackupsWorker(BaseWorker):
    def run_task(self) -> list[BackupManifest]:
        return list_backups()


class _CreateBackupWorker(BaseWorker):
    def __init__(
        self,
        namespaces: list[str] | None,
        resource_types: list[str] | None,
    ) -> None:
        super().__init__()
        self._ns = namespaces
        self._types = resource_types

    def run_task(self) -> BackupManifest:
        return create_backup(namespaces=self._ns, resource_types=self._types)


class _RestoreWorker(BaseWorker):
    def __init__(
        self,
        filename: str,
        namespaces: list[str] | None,
        resource_types: list[str] | None,
        dry_run: bool,
    ) -> None:
        super().__init__()
        self._filename = filename
        self._ns = namespaces
        self._types = resource_types
        self._dry_run = dry_run

    def run_task(self) -> int:
        return restore_backup(
            filename=self._filename,
            namespaces=self._ns,
            resource_types=self._types,
            dry_run=self._dry_run,
        )


class BackupViewModel(QObject):
    """
    ViewModel for backup listing, creation, restoration, and deletion.

    Signals:
        backups_loaded (list):          list[BackupManifest]
        backup_created (object):        BackupManifest of new backup
        restore_completed (int):        Number of resources restored
        backup_deleted (str):           Filename that was deleted
        loading_changed (bool):         True during async ops
        error_occurred (str):           User-friendly error message
    """

    backups_loaded: pyqtSignal = pyqtSignal(list)
    backup_created: pyqtSignal = pyqtSignal(object)
    restore_completed: pyqtSignal = pyqtSignal(int)
    backup_deleted: pyqtSignal = pyqtSignal(str)
    loading_changed: pyqtSignal = pyqtSignal(bool)
    error_occurred: pyqtSignal = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._worker: BaseWorker | None = None

    # ── Actions ──────────────────────────────────────────────────────────────

    def load_backups(self) -> None:
        """List available backups."""
        self._start(_ListBackupsWorker(), self._on_backups_loaded)

    def create_new_backup(
        self,
        namespaces: list[str] | None = None,
        resource_types: list[str] | None = None,
    ) -> None:
        """Create a new backup archive."""
        w = _CreateBackupWorker(namespaces, resource_types)
        self._start(w, self._on_backup_created)

    def restore_from_backup(
        self,
        filename: str,
        namespaces: list[str] | None = None,
        resource_types: list[str] | None = None,
        dry_run: bool = False,
    ) -> None:
        """Restore resources from a backup."""
        w = _RestoreWorker(filename, namespaces, resource_types, dry_run)
        self._start(w, self._on_restore_completed)

    def delete_backup_file(self, filename: str) -> None:
        """Delete a backup file and refresh."""
        delete_backup(filename)
        self.backup_deleted.emit(filename)
        self.load_backups()

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_backups_loaded(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.backups_loaded.emit(result)

    def _on_backup_created(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.backup_created.emit(result)
        self.load_backups()

    def _on_restore_completed(self, result: Any) -> None:
        self.loading_changed.emit(False)
        self.restore_completed.emit(int(result))

    def _on_error(self, msg: str) -> None:
        self.loading_changed.emit(False)
        self.error_occurred.emit(msg)

    def _start(self, worker: BaseWorker, on_finished) -> None:
        if self._worker and self._worker.isRunning():
            try:
                self._worker.finished.disconnect()
                self._worker.error.disconnect()
            except TypeError:
                pass
        self._worker = worker
        self._worker.finished.connect(on_finished)
        self._worker.error.connect(self._on_error)
        self.loading_changed.emit(True)
        self._worker.start()

