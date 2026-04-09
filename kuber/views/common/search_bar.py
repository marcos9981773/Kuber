"""
kuber/views/common/search_bar.py
Reusable search/filter bar with debounce for resource tables.
"""
from __future__ import annotations

from PyQt5.QtCore import QTimer, pyqtSignal
from PyQt5.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget


class SearchBar(QWidget):
    """
    Text input that emits a debounced ``search_changed`` signal.

    Signals:
        search_changed (str): Emitted 300ms after the user stops typing.
    """

    search_changed: pyqtSignal = pyqtSignal(str)

    _DEBOUNCE_MS = 300

    def __init__(self, placeholder: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui(placeholder)

        self._debounce = QTimer(self)
        self._debounce.setSingleShot(True)
        self._debounce.timeout.connect(self._emit_search)

    def _setup_ui(self, placeholder: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(6)

        self._input = QLineEdit()
        self._input.setObjectName("searchInput")
        self._input.setPlaceholderText(placeholder or self.tr("Search…"))
        self._input.setClearButtonEnabled(True)
        self._input.setAccessibleName(self.tr("Search filter input"))
        self._input.setAccessibleDescription(
            self.tr("Type to filter the resource table by name, namespace, or status.")
        )
        self._input.textChanged.connect(self._on_text_changed)
        layout.addWidget(self._input, stretch=1)

    def _on_text_changed(self) -> None:
        self._debounce.start(self._DEBOUNCE_MS)

    def _emit_search(self) -> None:
        self.search_changed.emit(self._input.text())

    def clear(self) -> None:
        self._input.clear()

    def text(self) -> str:
        return self._input.text()

