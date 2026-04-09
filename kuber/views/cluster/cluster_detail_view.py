"""
kuber/views/cluster/cluster_detail_view.py
Detail panel for a selected Kubernetes cluster.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QFrame,
    QGridLayout,
    QLabel,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from kuber.core.kubernetes.clusters import ClusterInfo, NodeInfo
from kuber.viewmodels.cluster_vm import ClusterViewModel


class ClusterDetailView(QWidget):
    """
    Shows live cluster information: server version, node count, node list.
    Updated whenever ClusterViewModel emits cluster_info_loaded.
    """

    def __init__(self, view_model: ClusterViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._setup_ui()
        self._setup_accessibility()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # ── Title ────────────────────────────────────────────────────────
        title = QLabel(self.tr("Cluster Details"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ── Summary card ─────────────────────────────────────────────────
        summary_frame = QFrame()
        summary_frame.setObjectName("detailCard")
        summary_layout = QGridLayout(summary_frame)
        summary_layout.setColumnMinimumWidth(0, 140)

        def _add_row(row: int, label_text: str, value_widget: QLabel) -> None:
            lbl = QLabel(label_text)
            lbl.setObjectName("detailLabel")
            summary_layout.addWidget(lbl, row, 0)
            summary_layout.addWidget(value_widget, row, 1)

        self._lbl_context = QLabel("—")
        self._lbl_server = QLabel("—")
        self._lbl_version = QLabel("—")
        self._lbl_nodes = QLabel("—")
        self._lbl_namespaces = QLabel("—")
        self._lbl_reachable = QLabel("—")

        for w in (
            self._lbl_context, self._lbl_server, self._lbl_version,
            self._lbl_nodes, self._lbl_namespaces, self._lbl_reachable,
        ):
            w.setObjectName("detailValue")
            w.setWordWrap(True)

        _add_row(0, self.tr("Context:"),    self._lbl_context)
        _add_row(1, self.tr("Server:"),     self._lbl_server)
        _add_row(2, self.tr("Version:"),    self._lbl_version)
        _add_row(3, self.tr("Nodes:"),      self._lbl_nodes)
        _add_row(4, self.tr("Namespaces:"), self._lbl_namespaces)
        _add_row(5, self.tr("Reachable:"),  self._lbl_reachable)

        layout.addWidget(summary_frame)

        # ── Node list ─────────────────────────────────────────────────────
        node_title = QLabel(self.tr("Nodes"))
        node_title.setObjectName("sectionTitle")
        layout.addWidget(node_title)

        self._nodes_container = QWidget()
        self._nodes_layout = QVBoxLayout(self._nodes_container)
        self._nodes_layout.setContentsMargins(0, 0, 0, 0)
        self._nodes_layout.setSpacing(4)

        scroll = QScrollArea()
        scroll.setWidget(self._nodes_container)
        scroll.setWidgetResizable(True)
        scroll.setObjectName("nodesScroll")
        layout.addWidget(scroll, stretch=1)

    def _setup_accessibility(self) -> None:
        self.setAccessibleName(self.tr("Cluster detail panel"))
        self._lbl_context.setAccessibleName(self.tr("Active context name"))
        self._lbl_server.setAccessibleName(self.tr("API server URL"))
        self._lbl_version.setAccessibleName(self.tr("Kubernetes server version"))
        self._lbl_nodes.setAccessibleName(self.tr("Node count"))
        self._lbl_namespaces.setAccessibleName(self.tr("Namespace count"))
        self._lbl_reachable.setAccessibleName(self.tr("Cluster reachability status"))

    def _connect_signals(self) -> None:
        self._vm.cluster_info_loaded.connect(self._on_cluster_info_loaded)
        self._vm.context_switched.connect(lambda _: self._clear())

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_cluster_info_loaded(self, info: ClusterInfo) -> None:
        self._lbl_context.setText(info.context_name)
        self._lbl_server.setText(info.server_url or "—")
        self._lbl_version.setText(info.k8s_version or "—")
        self._lbl_nodes.setText(str(info.node_count))
        self._lbl_namespaces.setText(str(info.namespace_count))
        reachable_text = self.tr("✅ Yes") if info.is_reachable else self.tr("❌ No")
        self._lbl_reachable.setText(reachable_text)
        self._populate_nodes(info.nodes)

    def _populate_nodes(self, nodes: list[NodeInfo]) -> None:
        # Clear existing node widgets
        while self._nodes_layout.count():
            child = self._nodes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        for node in nodes:
            row = QFrame()
            row.setObjectName("nodeRow")
            row_layout = QGridLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)

            status_icon = "✅" if node.status == "Ready" else "❌"
            name_lbl = QLabel(f"{status_icon}  {node.name}")
            name_lbl.setObjectName("nodeNameLabel")
            name_lbl.setAccessibleName(
                self.tr("Node {0}, status {1}").format(node.name, node.status)
            )

            roles_lbl = QLabel(", ".join(node.roles))
            roles_lbl.setObjectName("nodeRolesLabel")

            version_lbl = QLabel(node.version)
            version_lbl.setObjectName("nodeVersionLabel")

            row_layout.addWidget(name_lbl, 0, 0)
            row_layout.addWidget(roles_lbl, 0, 1)
            row_layout.addWidget(version_lbl, 0, 2)
            self._nodes_layout.addWidget(row)

        if not nodes:
            empty = QLabel(self.tr("No node information available."))
            empty.setAlignment(Qt.AlignCenter)
            self._nodes_layout.addWidget(empty)

        self._nodes_layout.addStretch()

    def _clear(self) -> None:
        for lbl in (
            self._lbl_context, self._lbl_server, self._lbl_version,
            self._lbl_nodes, self._lbl_namespaces, self._lbl_reachable,
        ):
            lbl.setText("—")
        while self._nodes_layout.count():
            child = self._nodes_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

