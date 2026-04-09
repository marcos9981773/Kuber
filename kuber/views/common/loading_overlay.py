"""
kuber/views/common/loading_overlay.py
Non-blocking loading overlay widget.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QFrame, QLabel, QVBoxLayout, QWidget


class LoadingOverlay(QWidget):
    """
    Transparent overlay displayed over a parent widget during async operations.

    Shows a spinner emoji and a configurable message.

    Usage::

        self._overlay = LoadingOverlay(self)

        # show before starting work:
        self._overlay.show_with_message("Loading clusters…")

        # hide when done:
        self._overlay.hide()
    """

    def __init__(self, parent: QWidget) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.setObjectName("loadingOverlay")
        self._setup_ui()
        self.hide()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setAlignment(Qt.AlignCenter)

        card = QFrame(self)
        card.setObjectName("loadingCard")
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignCenter)
        card_layout.setSpacing(8)

        self._spinner_label = QLabel("⏳")
        self._spinner_label.setObjectName("loadingSpinner")
        self._spinner_label.setAlignment(Qt.AlignCenter)
        self._spinner_label.setAccessibleName(self.tr("Loading indicator"))

        self._message_label = QLabel(self.tr("Loading…"))
        self._message_label.setObjectName("loadingMessage")
        self._message_label.setAlignment(Qt.AlignCenter)
        self._message_label.setAccessibleName(self.tr("Loading status message"))

        card_layout.addWidget(self._spinner_label)
        card_layout.addWidget(self._message_label)
        layout.addWidget(card)

    def show_with_message(self, message: str) -> None:
        """Show the overlay with a specific message and resize to parent."""
        self._message_label.setText(message)
        if self.parent():
            self.resize(self.parent().size())  # type: ignore[union-attr]
        self.show()
        self.raise_()

    def resizeEvent(self, event) -> None:  # type: ignore[override]
        """Keep overlay covering the entire parent widget."""
        if self.parent():
            self.resize(self.parent().size())  # type: ignore[union-attr]
        super().resizeEvent(event)

