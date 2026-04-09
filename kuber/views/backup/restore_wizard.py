"""
kuber/views/backup/restore_wizard.py
Multi-step wizard for selective restore from backup archives.
"""
from __future__ import annotations

from PyQt5.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QLabel,
    QVBoxLayout,
    QWizard,
    QWizardPage,
    QWidget,
)

from kuber.services.backup_service import BACKUP_RESOURCE_TYPES, BackupManifest


class RestoreWizard(QWizard):
    """Wizard for selecting namespaces and resource types to restore."""

    def __init__(
        self, manifest: BackupManifest, parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Restore from Backup"))
        self.setMinimumWidth(500)
        self._manifest = manifest

        self._ns_page = _NamespaceSelectionPage(manifest)
        self._type_page = _ResourceTypeSelectionPage(manifest)
        self._review_page = _RestoreReviewPage()

        self.addPage(self._ns_page)
        self.addPage(self._type_page)
        self.addPage(self._review_page)

    def get_selected_namespaces(self) -> list[str] | None:
        """Return selected namespaces (None = all)."""
        return self._ns_page.get_selected()

    def get_selected_types(self) -> list[str] | None:
        """Return selected resource types (None = all)."""
        return self._type_page.get_selected()

    def is_dry_run(self) -> bool:
        """Return whether the user chose dry-run mode."""
        return self._review_page.is_dry_run()


class _NamespaceSelectionPage(QWizardPage):
    """Select namespaces to restore."""

    def __init__(self, manifest: BackupManifest, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Select Namespaces"))
        self.setSubTitle(self.tr("Choose which namespaces to restore."))
        self._checks: dict[str, QCheckBox] = {}
        self._setup_ui(manifest)

    def _setup_ui(self, manifest: BackupManifest) -> None:
        layout = QVBoxLayout(self)

        self._all_check = QCheckBox(self.tr("All namespaces"))
        self._all_check.setChecked(True)
        self._all_check.setAccessibleName(self.tr("Select all namespaces"))
        self._all_check.toggled.connect(self._on_all_toggled)
        layout.addWidget(self._all_check)

        group = QGroupBox(self.tr("Namespaces"))
        group_layout = QVBoxLayout(group)
        for ns in manifest.namespaces:
            cb = QCheckBox(ns)
            cb.setChecked(True)
            self._checks[ns] = cb
            group_layout.addWidget(cb)
        layout.addWidget(group)
        layout.addStretch()

    def _on_all_toggled(self, checked: bool) -> None:
        for cb in self._checks.values():
            cb.setChecked(checked)
            cb.setEnabled(not checked)

    def get_selected(self) -> list[str] | None:
        if self._all_check.isChecked():
            return None
        return [ns for ns, cb in self._checks.items() if cb.isChecked()]


class _ResourceTypeSelectionPage(QWizardPage):
    """Select resource types to restore."""

    def __init__(self, manifest: BackupManifest, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Select Resource Types"))
        self.setSubTitle(self.tr("Choose which resource types to restore."))
        self._checks: dict[str, QCheckBox] = {}
        self._setup_ui(manifest)

    def _setup_ui(self, manifest: BackupManifest) -> None:
        layout = QVBoxLayout(self)

        self._all_check = QCheckBox(self.tr("All resource types"))
        self._all_check.setChecked(True)
        self._all_check.setAccessibleName(self.tr("Select all resource types"))
        self._all_check.toggled.connect(self._on_all_toggled)
        layout.addWidget(self._all_check)

        types = manifest.resource_types or BACKUP_RESOURCE_TYPES
        group = QGroupBox(self.tr("Resource Types"))
        group_layout = QVBoxLayout(group)
        for rtype in types:
            cb = QCheckBox(rtype)
            cb.setChecked(True)
            self._checks[rtype] = cb
            group_layout.addWidget(cb)
        layout.addWidget(group)
        layout.addStretch()

    def _on_all_toggled(self, checked: bool) -> None:
        for cb in self._checks.values():
            cb.setChecked(checked)
            cb.setEnabled(not checked)

    def get_selected(self) -> list[str] | None:
        if self._all_check.isChecked():
            return None
        return [t for t, cb in self._checks.items() if cb.isChecked()]


class _RestoreReviewPage(QWizardPage):
    """Final review page with dry-run option."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Review & Confirm"))
        self.setSubTitle(
            self.tr("Review your selections. Enable dry-run to validate without applying.")
        )
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._info = QLabel(
            self.tr("Click 'Finish' to start the restore process.")
        )
        self._info.setWordWrap(True)
        layout.addWidget(self._info)

        self._dry_run_check = QCheckBox(self.tr("Dry run (validate only)"))
        self._dry_run_check.setAccessibleName(self.tr("Dry run mode"))
        self._dry_run_check.setAccessibleDescription(
            self.tr("Validate the restore without actually applying resources.")
        )
        layout.addWidget(self._dry_run_check)
        layout.addStretch()

    def is_dry_run(self) -> bool:
        return self._dry_run_check.isChecked()

