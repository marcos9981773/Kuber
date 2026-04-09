"""
kuber/models/resource_model.py
Generic QAbstractTableModel for any Kubernetes resource dataclass.
"""
from __future__ import annotations

from dataclasses import fields as dc_fields
from typing import Any

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, QSortFilterProxyModel, Qt


class ResourceTableModel(QAbstractTableModel):
    """
    Generic table model that displays rows of dataclass instances.

    Columns are auto-derived from the dataclass field names at set_data() time.
    Used by Pods, Deployments, Services, ConfigMaps views.
    """

    def __init__(self, columns: list[str] | None = None, parent=None) -> None:
        super().__init__(parent)
        self._items: list[Any] = []
        self._columns: list[str] = columns or []

    # ── QAbstractTableModel interface ────────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._items)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._columns)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole) -> Any:
        if not index.isValid() or not (0 <= index.row() < len(self._items)):
            return None

        item = self._items[index.row()]
        col_name = self._columns[index.column()]

        if role == Qt.DisplayRole:
            value = getattr(item, col_name, "")
            if isinstance(value, list):
                return ", ".join(str(v) for v in value)
            return str(value)

        if role == Qt.UserRole:
            return item

        if role == Qt.ToolTipRole:
            value = getattr(item, col_name, "")
            return str(value) if value else None

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ) -> Any:
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            raw = self._columns[section]
            return raw.replace("_", " ").title()
        return None

    # ── Data update API ──────────────────────────────────────────────────────

    def set_items(self, items: list[Any]) -> None:
        """Replace all rows with a fresh list of dataclass instances."""
        self.beginResetModel()
        self._items = list(items)
        if items and not self._columns:
            self._columns = [f.name for f in dc_fields(items[0])]
        self.endResetModel()

    def item_at(self, row: int) -> Any | None:
        if 0 <= row < len(self._items):
            return self._items[row]
        return None

    def clear(self) -> None:
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()


class ResourceFilterProxy(QSortFilterProxyModel):
    """
    Proxy model that filters resource rows by a text search string.
    Searches across all columns (name, namespace, status, etc.).
    """

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._filter_text: str = ""
        self.setFilterCaseSensitivity(Qt.CaseInsensitive)

    def set_filter_text(self, text: str) -> None:
        self._filter_text = text.strip().lower()
        self.invalidateFilter()

    def filterAcceptsRow(self, source_row: int, source_parent: QModelIndex) -> bool:
        if not self._filter_text:
            return True
        model = self.sourceModel()
        for col in range(model.columnCount()):
            idx = model.index(source_row, col, source_parent)
            value = str(model.data(idx, Qt.DisplayRole) or "").lower()
            if self._filter_text in value:
                return True
        return False

