"""
kuber/views/common/error_dialog.py
User-friendly error dialog following the project error message format.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


class ErrorDialog(QDialog):
    """
    Displays a user-friendly error message with optional technical details.

    Error message format: "[What happened]. [Why it happened]. [What to do next]."

    Usage::

        ErrorDialog.show_error(
            parent=self,
            title="Connection Failed",
            message="Could not connect to cluster 'prod-us'.",
            details="The API server is unreachable.",
            fix_hint="Check your VPN connection and try again.",
        )
    """

    def __init__(
        self,
        title: str,
        message: str,
        details: str = "",
        fix_hint: str = "",
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Error — {0}").format(title))
        self.setMinimumWidth(480)
        self.setModal(True)
        self._details = details
        self._setup_ui(title, message, details, fix_hint)

    def _setup_ui(
        self, title: str, message: str, details: str, fix_hint: str
    ) -> None:
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # ── Icon + title row ───────────────────────────────
        title_row = QHBoxLayout()
        icon_label = QLabel("⛔")
        icon_label.setObjectName("errorIcon")
        icon_label.setFixedWidth(36)
        icon_label.setAccessibleName(self.tr("Error icon"))

        title_label = QLabel(f"<b>{title}</b>")
        title_label.setObjectName("errorTitle")
        title_label.setWordWrap(True)
        title_row.addWidget(icon_label)
        title_row.addWidget(title_label, stretch=1)
        layout.addLayout(title_row)

        # ── Main message ───────────────────────────────────
        msg_label = QLabel(message)
        msg_label.setObjectName("errorMessage")
        msg_label.setWordWrap(True)
        msg_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(msg_label)

        # ── Fix hint ───────────────────────────────────────
        if fix_hint:
            hint_label = QLabel(f"💡 {fix_hint}")
            hint_label.setObjectName("errorHint")
            hint_label.setWordWrap(True)
            hint_label.setAccessibleName(self.tr("Suggested action"))
            layout.addWidget(hint_label)

        # ── Technical details (collapsible) ───────────────
        if details:
            self._details_widget = QTextEdit()
            self._details_widget.setObjectName("errorDetails")
            self._details_widget.setReadOnly(True)
            self._details_widget.setPlainText(details)
            self._details_widget.setMaximumHeight(120)
            self._details_widget.setVisible(False)
            self._details_widget.setAccessibleName(self.tr("Technical error details"))

            self._toggle_btn = QPushButton(self.tr("▶ Show Details"))
            self._toggle_btn.setObjectName("btnText")
            self._toggle_btn.setCheckable(True)
            self._toggle_btn.setAccessibleName(self.tr("Toggle error details"))
            self._toggle_btn.toggled.connect(self._on_toggle_details)
            layout.addWidget(self._toggle_btn)
            layout.addWidget(self._details_widget)

        # ── Buttons ────────────────────────────────────────
        buttons = QDialogButtonBox(QDialogButtonBox.Ok)
        buttons.accepted.connect(self.accept)
        buttons.button(QDialogButtonBox.Ok).setAccessibleName(self.tr("Close error dialog"))
        layout.addWidget(buttons)

    def _on_toggle_details(self, checked: bool) -> None:
        self._details_widget.setVisible(checked)
        self._toggle_btn.setText(
            self.tr("▼ Hide Details") if checked else self.tr("▶ Show Details")
        )
        self.adjustSize()

    @classmethod
    def show_error(
        cls,
        title: str,
        message: str,
        details: str = "",
        fix_hint: str = "",
        parent: QWidget | None = None,
    ) -> None:
        """
        Convenience method to create and exec the dialog in one call.

        Args:
            title:    Short title for the error (e.g., "Connection Failed").
            message:  User-facing explanation of what happened and what to do.
            details:  Optional technical details (stack trace, raw error).
            fix_hint: Optional actionable suggestion for the user.
            parent:   Parent widget.
        """
        dialog = cls(title=title, message=message, details=details,
                     fix_hint=fix_hint, parent=parent)
        dialog.exec_()

