"""
kuber/views/monitoring/logs_view.py
Pod log viewer with search, auto-scroll and container selector.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QColor, QFont, QTextCharFormat, QTextCursor
from PyQt5.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from kuber.core.kubernetes.pods import PodInfo
from kuber.viewmodels.monitoring_vm import MonitoringViewModel
from kuber.views.common.ansi_parser import render_ansi, strip_ansi
from kuber.views.common.namespace_selector import NamespaceSelector


class LogsView(QWidget):
    """
    Log viewer for a specific pod.

    Provides:
    - Namespace combo populated from the cluster
    - Pod combo that auto-updates when a namespace is selected
    - Container selector
    - Tail lines control
    - Auto-scrolling log output with ANSI color support
    """

    def __init__(
        self, view_model: MonitoringViewModel, parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self._vm = view_model
        self._pods: list[PodInfo] = []
        self._raw_log: str = ""
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()
        self._connect_signals()
        self._vm.load_namespaces()

    # ── UI setup ─────────────────────────────────────────────────────────────

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        title = QLabel(self.tr("Pod Logs"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # Input row
        input_row = QHBoxLayout()

        self._ns_selector = NamespaceSelector()
        input_row.addWidget(self._ns_selector)

        lbl_pod = QLabel(self.tr("Pod:"))
        input_row.addWidget(lbl_pod)

        self._pod_combo = QComboBox()
        self._pod_combo.setObjectName("podCombo")
        self._pod_combo.setMinimumWidth(200)
        self._pod_combo.setEditable(True)
        self._pod_combo.lineEdit().setPlaceholderText(
            self.tr("Select or type pod name")
        )
        input_row.addWidget(self._pod_combo, stretch=2)

        self._container_input = QLineEdit()
        self._container_input.setPlaceholderText(self.tr("Container (optional)"))
        input_row.addWidget(self._container_input, stretch=1)

        self._lines_spin = QSpinBox()
        self._lines_spin.setRange(10, 5000)
        self._lines_spin.setValue(200)
        input_row.addWidget(self._lines_spin)

        self._btn_fetch = QPushButton(self.tr("📋 Fetch Logs"))
        self._btn_fetch.setObjectName("btnPrimary")
        self._btn_fetch.clicked.connect(self._on_fetch)
        input_row.addWidget(self._btn_fetch)

        layout.addLayout(input_row)

        # Search row
        search_row = QHBoxLayout()
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText(self.tr("Search in logs…"))
        self._search_input.textChanged.connect(self._on_search)
        self._search_input.returnPressed.connect(self._search_next)
        search_row.addWidget(self._search_input, stretch=1)

        self._btn_prev = QPushButton(self.tr("◀ Prev"))
        self._btn_prev.setObjectName("btnSearchPrev")
        self._btn_prev.setEnabled(False)
        self._btn_prev.clicked.connect(self._search_prev)
        search_row.addWidget(self._btn_prev)

        self._btn_next = QPushButton(self.tr("Next ▶"))
        self._btn_next.setObjectName("btnSearchNext")
        self._btn_next.setEnabled(False)
        self._btn_next.clicked.connect(self._search_next)
        search_row.addWidget(self._btn_next)

        self._match_label = QLabel("")
        self._match_label.setObjectName("searchMatchLabel")
        search_row.addWidget(self._match_label)

        self._btn_clear_search = QPushButton(self.tr("✕ Clear"))
        self._btn_clear_search.setObjectName("btnSearchClear")
        self._btn_clear_search.setEnabled(False)
        self._btn_clear_search.clicked.connect(self._clear_search)
        search_row.addWidget(self._btn_clear_search)

        layout.addLayout(search_row)

        # Search state
        self._search_positions: list[int] = []
        self._search_current_idx: int = -1
        self._highlight_fmt = QTextCharFormat()
        self._highlight_fmt.setBackground(QColor("#b3d4fc"))
        self._current_fmt = QTextCharFormat()
        self._current_fmt.setBackground(QColor("#ff9632"))

        # Log output — QTextEdit to support rich (colored) text
        self._log_output = QTextEdit()
        self._log_output.setObjectName("logOutput")
        self._log_output.setReadOnly(True)
        self._log_output.setLineWrapMode(QTextEdit.NoWrap)
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.Monospace)
        self._log_output.setFont(font)
        layout.addWidget(self._log_output, stretch=1)

    def _setup_accessibility(self) -> None:
        self._ns_selector.setAccessibleName(self.tr("Namespace selector"))
        self._pod_combo.setAccessibleName(self.tr("Pod selector"))
        self._pod_combo.setAccessibleDescription(
            self.tr("Select a pod to view its logs.")
        )
        self._container_input.setAccessibleName(self.tr("Container name input"))
        self._lines_spin.setAccessibleName(self.tr("Number of log lines"))
        self._btn_fetch.setAccessibleName(self.tr("Fetch pod logs"))
        self._search_input.setAccessibleName(self.tr("Log search input"))
        self._btn_prev.setAccessibleName(self.tr("Previous search match"))
        self._btn_next.setAccessibleName(self.tr("Next search match"))
        self._btn_clear_search.setAccessibleName(self.tr("Clear search"))
        self._match_label.setAccessibleName(self.tr("Search match counter"))
        self._log_output.setAccessibleName(self.tr("Pod log output"))

    def _setup_tab_order(self) -> None:
        QWidget.setTabOrder(self._ns_selector, self._pod_combo)
        QWidget.setTabOrder(self._pod_combo, self._container_input)
        QWidget.setTabOrder(self._container_input, self._lines_spin)
        QWidget.setTabOrder(self._lines_spin, self._btn_fetch)
        QWidget.setTabOrder(self._btn_fetch, self._search_input)
        QWidget.setTabOrder(self._search_input, self._btn_prev)
        QWidget.setTabOrder(self._btn_prev, self._btn_next)
        QWidget.setTabOrder(self._btn_next, self._btn_clear_search)
        QWidget.setTabOrder(self._btn_clear_search, self._log_output)

    def _connect_signals(self) -> None:
        self._vm.logs_loaded.connect(self._on_logs_loaded)
        self._vm.namespaces_loaded.connect(self._ns_selector.set_namespaces)
        self._vm.pods_loaded.connect(self._on_pods_loaded)
        self._ns_selector.namespace_changed.connect(self._on_namespace_changed)

    # ── Slots ────────────────────────────────────────────────────────────────

    def _on_namespace_changed(self, namespace: str) -> None:
        """Reload the pod list when the user picks a different namespace."""
        self._vm.set_namespace(namespace)
        self._vm.load_pods(namespace)

    def _on_pods_loaded(self, pods: list[PodInfo]) -> None:
        """Populate the pod combo with the fetched pod names."""
        self._pods = pods
        current_text = self._pod_combo.currentText()
        self._pod_combo.blockSignals(True)
        self._pod_combo.clear()
        for pod in pods:
            self._pod_combo.addItem(pod.name, pod.namespace)
        # Restore previous selection if still present
        idx = self._pod_combo.findText(current_text)
        if idx >= 0:
            self._pod_combo.setCurrentIndex(idx)
        self._pod_combo.blockSignals(False)

    def _on_fetch(self) -> None:
        pod = self._pod_combo.currentText().strip()
        ns = (
            self._pod_combo.currentData()
            or self._ns_selector.current_namespace()
        )
        if ns == "all":
            ns = "default"
        container = self._container_input.text().strip() or None
        lines = self._lines_spin.value()
        if pod:
            self._vm.load_logs(pod, ns, container, lines)

    def _on_logs_loaded(self, text: str) -> None:
        self._raw_log = text
        render_ansi(self._log_output, text)
        # Scroll to bottom
        sb = self._log_output.verticalScrollBar()
        if sb:
            sb.setValue(sb.maximum())

    def _on_search(self, text: str) -> None:
        """Find all occurrences, highlight them, and jump to the first."""
        self._clear_highlights()
        self._search_positions.clear()
        self._search_current_idx = -1

        if not text:
            self._update_match_label()
            return

        # Find all occurrences
        doc = self._log_output.document()
        cursor = QTextCursor(doc)
        while True:
            cursor = doc.find(text, cursor)
            if cursor.isNull():
                break
            self._search_positions.append(cursor.selectionStart())
            cursor.mergeCharFormat(self._highlight_fmt)

        self._update_match_label()

        if self._search_positions:
            self._search_current_idx = 0
            self._go_to_match(0)

    def _search_next(self) -> None:
        """Jump to the next search match."""
        if not self._search_positions:
            return
        idx = (self._search_current_idx + 1) % len(self._search_positions)
        self._go_to_match(idx)

    def _search_prev(self) -> None:
        """Jump to the previous search match."""
        if not self._search_positions:
            return
        idx = (self._search_current_idx - 1) % len(self._search_positions)
        self._go_to_match(idx)

    def _clear_search(self) -> None:
        """Clear the search input and all highlights."""
        self._search_input.clear()

    def _go_to_match(self, idx: int) -> None:
        """Highlight the match at *idx* as current and scroll to it."""
        text = self._search_input.text()
        if not text or not self._search_positions:
            return

        # Reset the previous current match to the normal highlight color
        if 0 <= self._search_current_idx < len(self._search_positions):
            self._apply_fmt_at(
                self._search_positions[self._search_current_idx],
                len(text),
                self._highlight_fmt,
            )

        self._search_current_idx = idx

        # Apply the "current" highlight color
        self._apply_fmt_at(
            self._search_positions[idx], len(text), self._current_fmt
        )

        # Move visible cursor to the current match
        cursor = self._log_output.textCursor()
        cursor.setPosition(self._search_positions[idx])
        cursor.movePosition(
            QTextCursor.Right, QTextCursor.KeepAnchor, len(text)
        )
        self._log_output.setTextCursor(cursor)
        self._log_output.ensureCursorVisible()

        self._update_match_label()

    def _apply_fmt_at(
        self, position: int, length: int, fmt: QTextCharFormat
    ) -> None:
        """Apply *fmt* to *length* characters starting at *position*."""
        cursor = self._log_output.textCursor()
        cursor.setPosition(position)
        cursor.movePosition(QTextCursor.Right, QTextCursor.KeepAnchor, length)
        cursor.mergeCharFormat(fmt)

    def _clear_highlights(self) -> None:
        """Remove all search highlight formatting."""
        cursor = self._log_output.textCursor()
        cursor.select(QTextCursor.Document)
        default_fmt = QTextCharFormat()
        default_fmt.setBackground(QColor(Qt.transparent))
        cursor.mergeCharFormat(default_fmt)
        cursor.clearSelection()
        self._log_output.setTextCursor(cursor)

    def _update_match_label(self) -> None:
        """Refresh the '3/42' counter label and enable/disable buttons."""
        total = len(self._search_positions)
        has_matches = total > 0
        has_text = bool(self._search_input.text())
        self._btn_prev.setEnabled(has_matches)
        self._btn_next.setEnabled(has_matches)
        self._btn_clear_search.setEnabled(has_text)

        if total == 0:
            if has_text:
                self._match_label.setText(self.tr("No matches"))
            else:
                self._match_label.setText("")
        else:
            current = self._search_current_idx + 1
            self._match_label.setText(
                self.tr("{0}/{1}").format(current, total)
            )

    # ── Public API ───────────────────────────────────────────────────────────

    def set_pod(self, pod_name: str, namespace: str = "default") -> None:
        """Pre-fill the pod name and namespace, then fetch logs immediately.

        Clears stale log output first so the user never sees logs from
        a previously selected pod while the new fetch is in-flight.
        """
        # 1. Clear stale logs immediately
        self._raw_log = ""
        self._log_output.clear()

        # 2. Update namespace selector without triggering a pod-list reload
        #    that would overwrite the pod combo text we're about to set.
        self._ns_selector.blockSignals(True)
        ns_idx = self._ns_selector._combo.findData(namespace)
        if ns_idx >= 0:
            self._ns_selector._combo.setCurrentIndex(ns_idx)
        self._ns_selector.blockSignals(False)
        self._vm.set_namespace(namespace)

        # 2b. Sync the global namespace store so other views update
        from kuber.views.common.namespace_store import NamespaceStore
        NamespaceStore.instance().set_namespace(namespace)

        # 3. Set the pod name in the combo
        self._pod_combo.setCurrentText(pod_name)

        # 4. Fetch logs directly with the explicit namespace, bypassing
        #    _on_fetch() which reads combo data that may be stale.
        container = self._container_input.text().strip() or None
        lines = self._lines_spin.value()
        ns = namespace if namespace != "all" else "default"
        self._vm.load_logs(pod_name, ns, container, lines)

        # 5. Refresh the pod list in background (won't affect the fetch above)
        self._vm.load_pods(namespace)

    def toPlainText(self) -> str:
        """Return the raw log text without ANSI codes (for testing)."""
        return strip_ansi(self._raw_log)

