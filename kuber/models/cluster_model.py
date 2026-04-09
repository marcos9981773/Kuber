"""
kuber/models/cluster_model.py
Qt data model for Kubernetes cluster contexts.
"""
from __future__ import annotations

from PyQt5.QtCore import QAbstractTableModel, QModelIndex, Qt

from kuber.config.kube_config import KubeContext

_COLUMNS = ["Name", "Cluster", "Status", "Server", "Namespace"]
_COL_NAME = 0
_COL_CLUSTER = 1
_COL_STATUS = 2
_COL_SERVER = 3
_COL_NAMESPACE = 4


class ClusterModel(QAbstractTableModel):
    """
    Table model that feeds :class:`~kuber.config.kube_config.KubeContext` rows
    to a :class:`~PyQt5.QtWidgets.QTableView`.

    Columns: Name | Cluster | Status | Server | Namespace
    """

    def __init__(self, parent=None) -> None:  # type: ignore[override]
        super().__init__(parent)
        self._contexts: list[KubeContext] = []
        self._active_name: str = ""

    # ── QAbstractTableModel interface ────────────────────────────────────────

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return len(self._contexts)

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:  # noqa: B008
        return len(_COLUMNS)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):  # type: ignore[override]
        if not index.isValid() or not (0 <= index.row() < len(self._contexts)):
            return None

        ctx = self._contexts[index.row()]
        col = index.column()

        if role == Qt.DisplayRole:
            if col == _COL_NAME:
                prefix = "● " if ctx.is_active else "  "
                return f"{prefix}{ctx.name}"
            if col == _COL_CLUSTER:
                return ctx.cluster
            if col == _COL_STATUS:
                return "Active" if ctx.is_active else "Inactive"
            if col == _COL_SERVER:
                return ctx.server
            if col == _COL_NAMESPACE:
                return ctx.namespace

        if role == Qt.UserRole:
            return ctx  # return the raw KubeContext object

        if role == Qt.ToolTipRole and col == _COL_SERVER:
            return ctx.server

        if role == Qt.ForegroundRole and col == _COL_STATUS:
            from PyQt5.QtGui import QColor
            return QColor("#4caf50") if ctx.is_active else QColor("#9e9e9e")

        return None

    def headerData(
        self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole
    ):  # type: ignore[override]
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return _COLUMNS[section]
        return None

    # ── Data update API ──────────────────────────────────────────────────────

    def set_contexts(self, contexts: list[KubeContext], active_name: str = "") -> None:
        """Replace all rows with a fresh list of contexts."""
        self.beginResetModel()
        self._contexts = list(contexts)
        self._active_name = active_name
        for ctx in self._contexts:
            ctx.is_active = ctx.name == active_name
        self.endResetModel()

    def context_at(self, row: int) -> KubeContext | None:
        """Return the KubeContext at the given row index."""
        if 0 <= row < len(self._contexts):
            return self._contexts[row]
        return None

