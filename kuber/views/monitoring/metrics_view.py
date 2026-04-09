"""
kuber/views/monitoring/metrics_view.py
Real-time CPU/memory charts using pyqtgraph.
"""
from __future__ import annotations

from PyQt5.QtWidgets import QHBoxLayout, QLabel, QVBoxLayout, QWidget

from kuber.core.kubernetes.metrics import NodeMetrics, PodMetrics
from kuber.viewmodels.monitoring_vm import MonitoringViewModel

try:
    import pyqtgraph as pg
    _HAS_PYQTGRAPH = True
except ImportError:
    _HAS_PYQTGRAPH = False


class MetricsView(QWidget):
    """
    Dashboard with CPU and memory bar charts for pods and nodes.
    Falls back to a text summary if pyqtgraph is unavailable.
    """

    def __init__(self, view_model: MonitoringViewModel, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        title = QLabel(self.tr("Metrics Dashboard"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        charts_row = QHBoxLayout()

        if _HAS_PYQTGRAPH:
            self._cpu_chart = pg.PlotWidget(title="CPU (millicores)")
            self._cpu_chart.setAccessibleName(self.tr("CPU usage chart"))
            self._mem_chart = pg.PlotWidget(title="Memory (MiB)")
            self._mem_chart.setAccessibleName(self.tr("Memory usage chart"))
            charts_row.addWidget(self._cpu_chart)
            charts_row.addWidget(self._mem_chart)
        else:
            self._fallback = QLabel(self.tr("Install pyqtgraph for charts."))
            self._fallback.setWordWrap(True)
            charts_row.addWidget(self._fallback)

        layout.addLayout(charts_row, stretch=1)

        self._summary = QLabel("")
        self._summary.setObjectName("metricsSummary")
        self._summary.setWordWrap(True)
        self._summary.setAccessibleName(self.tr("Metrics summary"))
        layout.addWidget(self._summary)

    def _connect_signals(self) -> None:
        self._vm.metrics_loaded.connect(self._on_metrics)

    def _on_metrics(self, data: dict) -> None:
        pods: list[PodMetrics] = data.get("pods", [])
        nodes: list[NodeMetrics] = data.get("nodes", [])

        if _HAS_PYQTGRAPH:
            self._update_charts(pods, nodes)

        lines = [
            self.tr("{0} pod(s), {1} node(s)").format(len(pods), len(nodes)),
        ]
        if pods:
            total_cpu = sum(p.cpu_millicores for p in pods)
            total_mem = sum(p.memory_mib for p in pods)
            lines.append(self.tr("Pods total: {0}m CPU, {1} MiB mem").format(total_cpu, total_mem))
        if nodes:
            total_cpu = sum(n.cpu_millicores for n in nodes)
            total_mem = sum(n.memory_mib for n in nodes)
            lines.append(
                self.tr("Nodes total: {0}m CPU, {1} MiB mem").format(total_cpu, total_mem)
            )
        self._summary.setText("\n".join(lines))

    def _update_charts(self, pods: list[PodMetrics], nodes: list[NodeMetrics]) -> None:
        if not _HAS_PYQTGRAPH:
            return
        # CPU bar chart — top 10 pods
        self._cpu_chart.clear()
        top_pods = sorted(pods, key=lambda p: p.cpu_millicores, reverse=True)[:10]
        x = list(range(len(top_pods)))
        cpu_vals = [p.cpu_millicores for p in top_pods]
        bg = pg.BarGraphItem(x=x, height=cpu_vals, width=0.6, brush="c")
        self._cpu_chart.addItem(bg)

        # Memory bar chart — top 10 pods
        self._mem_chart.clear()
        mem_vals = [p.memory_mib for p in top_pods]
        bg2 = pg.BarGraphItem(x=x, height=mem_vals, width=0.6, brush="m")
        self._mem_chart.addItem(bg2)

