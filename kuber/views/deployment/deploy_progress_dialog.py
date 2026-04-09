"""
kuber/views/deployment/deploy_progress_dialog.py
Modal dialog showing real-time deployment progress log.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QLabel,
    QPlainTextEdit,
    QVBoxLayout,
    QWidget,
)

from kuber.viewmodels.app_deploy_vm import AppDeployViewModel


class DeployProgressDialog(QDialog):
    """
    Modal dialog that streams deployment log lines in real time.

    Closes automatically on success or enables Close on failure.
    """

    def __init__(
        self,
        view_model: AppDeployViewModel,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self.setWindowTitle(self.tr("Deploying…"))
        self.setMinimumSize(520, 340)
        self.setModal(True)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        self._status = QLabel(self.tr("Deployment in progress…"))
        self._status.setObjectName("deployStatus")
        self._status.setAccessibleName(self.tr("Deployment status"))
        layout.addWidget(self._status)

        self._log = QPlainTextEdit()
        self._log.setObjectName("deployLog")
        self._log.setReadOnly(True)
        self._log.setAccessibleName(self.tr("Deployment log output"))
        layout.addWidget(self._log, stretch=1)

        self._buttons = QDialogButtonBox(QDialogButtonBox.Close)
        self._buttons.button(QDialogButtonBox.Close).setEnabled(False)
        self._buttons.rejected.connect(self.reject)
        layout.addWidget(self._buttons)

    def _connect_signals(self) -> None:
        self._vm.progress_log.connect(self._append_log)
        self._vm.deploy_completed.connect(self._on_completed)
        self._vm.deploy_failed.connect(self._on_failed)

    def _append_log(self, line: str) -> None:
        self._log.appendPlainText(line)
        # Auto-scroll to bottom
        sb = self._log.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def _on_completed(self, msg: str) -> None:
        self._status.setText(self.tr("✅ Deployment completed successfully."))
        self._buttons.button(QDialogButtonBox.Close).setEnabled(True)

    def _on_failed(self, msg: str) -> None:
        self._status.setText(self.tr("❌ Deployment failed."))
        self._buttons.button(QDialogButtonBox.Close).setEnabled(True)

