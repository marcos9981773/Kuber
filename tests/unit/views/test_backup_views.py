"""
tests/unit/views/test_backup_views.py
Tests for kuber/views/backup/ (BackupView, RestoreWizard).
"""
from __future__ import annotations

import pytest
from PyQt5.QtCore import QObject, pyqtSignal

from kuber.services.backup_service import BackupManifest


@pytest.fixture
def mock_backup_vm():
    """Fake BackupViewModel with all required signals."""

    class _FakeVM(QObject):
        backups_loaded = pyqtSignal(list)
        backup_created = pyqtSignal(object)
        restore_completed = pyqtSignal(int)
        backup_deleted = pyqtSignal(str)
        loading_changed = pyqtSignal(bool)
        error_occurred = pyqtSignal(str)

        def load_backups(self) -> None: pass
        def create_new_backup(self, ns=None, types=None) -> None: pass
        def restore_from_backup(self, fn, ns=None, types=None, dry=False) -> None: pass
        def delete_backup_file(self, fn) -> None: pass

    return _FakeVM()


class TestBackupView:
    def test_backup_view_creates(self, qtbot, mock_backup_vm) -> None:
        from kuber.views.backup.backup_view import BackupView
        view = BackupView(view_model=mock_backup_vm)
        qtbot.addWidget(view)
        assert view._table is not None

    def test_backups_loaded_populates_model(self, qtbot, mock_backup_vm) -> None:
        from kuber.views.backup.backup_view import BackupView
        view = BackupView(view_model=mock_backup_vm)
        qtbot.addWidget(view)

        backups = [
            BackupManifest(
                filename="kuber_backup_20260401_120000.tar.gz",
                timestamp="20260401_120000",
                namespaces=["default"],
                resource_types=["configmaps"],
                resource_count=5,
                size_bytes=1024,
            ),
        ]
        mock_backup_vm.backups_loaded.emit(backups)
        assert view._model.rowCount() == 1
        assert "1 backup(s)" in view._status.text()

    def test_buttons_disabled_without_selection(self, qtbot, mock_backup_vm) -> None:
        from kuber.views.backup.backup_view import BackupView
        view = BackupView(view_model=mock_backup_vm)
        qtbot.addWidget(view)
        assert not view._btn_restore.isEnabled()
        assert not view._btn_delete.isEnabled()

    def test_accessible_names_set(self, qtbot, mock_backup_vm) -> None:
        from kuber.views.backup.backup_view import BackupView
        view = BackupView(view_model=mock_backup_vm)
        qtbot.addWidget(view)
        assert view._table.accessibleName() != ""
        assert view._btn_create.accessibleName() != ""
        assert view._btn_restore.accessibleName() != ""


class TestRestoreWizard:
    def _make_manifest(self) -> BackupManifest:
        return BackupManifest(
            filename="test.tar.gz",
            timestamp="20260401_120000",
            namespaces=["default", "kube-system"],
            resource_types=["configmaps", "deployments"],
            resource_count=10,
            size_bytes=2048,
        )

    def test_wizard_creates_with_pages(self, qtbot) -> None:
        from kuber.views.backup.restore_wizard import RestoreWizard
        wizard = RestoreWizard(self._make_manifest())
        qtbot.addWidget(wizard)
        assert wizard.pageIds()

    def test_get_selected_namespaces_all_by_default(self, qtbot) -> None:
        from kuber.views.backup.restore_wizard import RestoreWizard
        wizard = RestoreWizard(self._make_manifest())
        qtbot.addWidget(wizard)
        assert wizard.get_selected_namespaces() is None  # None = all

    def test_get_selected_types_all_by_default(self, qtbot) -> None:
        from kuber.views.backup.restore_wizard import RestoreWizard
        wizard = RestoreWizard(self._make_manifest())
        qtbot.addWidget(wizard)
        assert wizard.get_selected_types() is None  # None = all

    def test_dry_run_default_false(self, qtbot) -> None:
        from kuber.views.backup.restore_wizard import RestoreWizard
        wizard = RestoreWizard(self._make_manifest())
        qtbot.addWidget(wizard)
        assert wizard.is_dry_run() is False

