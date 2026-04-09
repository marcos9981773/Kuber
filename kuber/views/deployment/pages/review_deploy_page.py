"""
kuber/views/deployment/pages/review_deploy_page.py
Wizard page showing a summary before the deploy is executed.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QLabel,
    QVBoxLayout,
    QWizardPage,
)


class ReviewDeployPage(QWizardPage):
    """Final wizard page: review deploy parameters and optionally dry-run."""

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setTitle(self.tr("Review & Deploy"))
        self.setSubTitle(self.tr("Confirm the deployment details below."))
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._summary = QLabel(self.tr("Loading summary…"))
        self._summary.setObjectName("deploySummary")
        self._summary.setWordWrap(True)
        self._summary.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        self._summary.setAccessibleName(self.tr("Deployment summary"))
        layout.addWidget(self._summary, stretch=1)

        self._dry_run_cb = QCheckBox(self.tr("Dry-run only (do NOT apply changes)"))
        self._dry_run_cb.setAccessibleName(self.tr("Dry-run checkbox"))
        self.registerField("deploy_dry_run", self._dry_run_cb)
        layout.addWidget(self._dry_run_cb)

    def set_summary_text(self, text: str) -> None:
        """Set the human-readable deployment summary."""
        self._summary.setText(text)

    def is_dry_run(self) -> bool:
        return self._dry_run_cb.isChecked()

