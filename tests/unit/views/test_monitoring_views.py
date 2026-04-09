"""
tests/unit/views/test_monitoring_views.py
Tests for kuber/views/monitoring/ (MetricsView, LogsView, EventsView).
"""
from __future__ import annotations

import pytest
from PyQt5.QtCore import QObject, pyqtSignal

from kuber.core.kubernetes.events import EventInfo
from kuber.core.kubernetes.metrics import NodeMetrics, PodMetrics
from kuber.core.kubernetes.pods import PodInfo


@pytest.fixture
def mock_monitoring_vm():
    """Fake MonitoringViewModel with all required signals."""

    class _FakeVM(QObject):
        metrics_loaded = pyqtSignal(dict)
        events_loaded = pyqtSignal(list)
        logs_loaded = pyqtSignal(str)
        namespaces_loaded = pyqtSignal(list)
        pods_loaded = pyqtSignal(list)
        loading_changed = pyqtSignal(bool)
        error_occurred = pyqtSignal(str)

        _namespace = "default"

        def load_metrics(self) -> None:
            pass

        def load_events(self) -> None:
            pass

        def load_logs(self, pod: str, ns: str, container=None, lines: int = 200) -> None:
            pass

        def load_namespaces(self) -> None:
            pass

        def load_pods(self, namespace: str | None = None) -> None:
            pass

        def set_namespace(self, ns: str) -> None:
            self._namespace = ns

        def start_metrics_polling(self) -> None:
            pass

        def stop_metrics_polling(self) -> None:
            pass

    return _FakeVM()


class TestMetricsView:
    def test_metrics_view_creates(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.metrics_view import MetricsView
        view = MetricsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)
        assert view._summary is not None

    def test_metrics_loaded_updates_summary(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.metrics_view import MetricsView
        view = MetricsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        data = {
            "pods": [PodMetrics("pod-1", "default", 100, 64)],
            "nodes": [NodeMetrics("node-1", 500, 1024)],
        }
        mock_monitoring_vm.metrics_loaded.emit(data)
        text = view._summary.text()
        assert "1 pod(s)" in text
        assert "1 node(s)" in text

    def test_metrics_empty_data(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.metrics_view import MetricsView
        view = MetricsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.metrics_loaded.emit({"pods": [], "nodes": []})
        assert "0 pod(s)" in view._summary.text()


class TestLogsView:
    def test_logs_view_creates(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)
        assert view._log_output is not None
        assert view._pod_combo is not None

    def test_logs_loaded_populates_output(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("line1\nline2\nline3")
        assert "line1" in view._log_output.toPlainText()
        assert "line3" in view._log_output.toPlainText()

    def test_set_pod_prefills_inputs(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        view.set_pod("my-pod", "kube-system")
        assert view._pod_combo.currentText() == "my-pod"

    def test_set_pod_clears_previous_logs(self, qtbot, mock_monitoring_vm) -> None:
        """Switching pods via set_pod must clear stale log output immediately."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        # Simulate logs from first pod
        mock_monitoring_vm.logs_loaded.emit("old-pod log line 1\nold-pod log line 2")
        assert "old-pod log line 1" in view._log_output.toPlainText()

        # Switch to a different pod
        view.set_pod("new-pod", "production")

        # Old logs must be gone before the new fetch completes
        assert view._log_output.toPlainText() == ""
        assert view._raw_log == ""

    def test_set_pod_fetches_with_correct_namespace(
        self, qtbot, mock_monitoring_vm, mocker
    ) -> None:
        """set_pod must call load_logs with the explicit namespace, not stale combo data."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        spy = mocker.spy(mock_monitoring_vm, "load_logs")

        view.set_pod("my-pod", "staging")

        spy.assert_called_once()
        _, kwargs_or_args = spy.call_args
        # load_logs(pod, ns, container, lines)
        assert spy.call_args[0][0] == "my-pod"
        assert spy.call_args[0][1] == "staging"

    def test_fetch_button_accessible(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)
        assert view._btn_fetch.accessibleName() != ""

    def test_namespaces_loaded_populates_selector(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.namespaces_loaded.emit(["default", "kube-system", "prod"])
        combo = view._ns_selector._combo
        # "All Namespaces" + 3 real namespaces
        assert combo.count() == 4

    def test_pods_loaded_populates_pod_combo(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        pods = [
            PodInfo(
                name="nginx-abc", namespace="default", status="Running",
                ready="1/1", restarts=0, node="node-1", image="nginx", age="5m",
            ),
            PodInfo(
                name="redis-xyz", namespace="default", status="Running",
                ready="1/1", restarts=0, node="node-1", image="redis", age="3m",
            ),
        ]
        mock_monitoring_vm.pods_loaded.emit(pods)
        assert view._pod_combo.count() == 2
        assert view._pod_combo.itemText(0) == "nginx-abc"
        assert view._pod_combo.itemText(1) == "redis-xyz"

    def test_namespace_change_triggers_pod_reload(
        self, qtbot, mock_monitoring_vm
    ) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        # Populate namespaces first
        mock_monitoring_vm.namespaces_loaded.emit(["default", "kube-system"])
        # Switch to kube-system (index 2 = after "All Namespaces")
        view._ns_selector._combo.setCurrentIndex(2)
        assert mock_monitoring_vm._namespace == "kube-system"

    def test_ansi_colors_rendered_and_stripped(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        # Emit logs with ANSI codes: red "ERROR" + reset + normal text
        ansi_log = "\x1b[31mERROR\x1b[0m something went wrong"
        mock_monitoring_vm.logs_loaded.emit(ansi_log)

        plain = view._log_output.toPlainText()
        # ANSI codes must NOT appear in the rendered output
        assert "\x1b[" not in plain
        # The actual text content must be present
        assert "ERROR" in plain
        assert "something went wrong" in plain

    def test_ansi_bold_and_colors_no_raw_escapes(
        self, qtbot, mock_monitoring_vm
    ) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        ansi_log = (
            "\x1b[1;32m2024-01-01T00:00:00Z\x1b[0m "
            "\x1b[33mWARN\x1b[0m message here"
        )
        mock_monitoring_vm.logs_loaded.emit(ansi_log)

        plain = view._log_output.toPlainText()
        assert "\x1b[" not in plain
        assert "2024-01-01T00:00:00Z" in plain
        assert "WARN" in plain
        assert "message here" in plain

    def test_plain_logs_without_ansi_render_correctly(
        self, qtbot, mock_monitoring_vm
    ) -> None:
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        plain_log = "no ansi here\njust plain text"
        mock_monitoring_vm.logs_loaded.emit(plain_log)

        assert view._log_output.toPlainText() == plain_log

    def test_search_finds_all_occurrences(self, qtbot, mock_monitoring_vm) -> None:
        """Searching highlights all matches and shows the correct count."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("ERROR line1\nINFO line2\nERROR line3\nERROR line4")
        view._search_input.setText("ERROR")

        assert len(view._search_positions) == 3
        assert view._search_current_idx == 0
        assert "1/3" in view._match_label.text()

    def test_search_next_cycles_through_matches(self, qtbot, mock_monitoring_vm) -> None:
        """Next button advances through matches and wraps around."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("AAA BBB AAA BBB AAA")
        view._search_input.setText("AAA")
        assert view._search_current_idx == 0

        view._search_next()
        assert view._search_current_idx == 1
        assert "2/3" in view._match_label.text()

        view._search_next()
        assert view._search_current_idx == 2
        assert "3/3" in view._match_label.text()

        # Wrap around to first
        view._search_next()
        assert view._search_current_idx == 0
        assert "1/3" in view._match_label.text()

    def test_search_prev_cycles_backwards(self, qtbot, mock_monitoring_vm) -> None:
        """Prev button goes backwards through matches and wraps around."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("XX YY XX YY XX")
        view._search_input.setText("XX")
        assert view._search_current_idx == 0

        # Wrap around to last
        view._search_prev()
        assert view._search_current_idx == 2
        assert "3/3" in view._match_label.text()

        view._search_prev()
        assert view._search_current_idx == 1
        assert "2/3" in view._match_label.text()

    def test_search_no_matches_shows_label(self, qtbot, mock_monitoring_vm) -> None:
        """When there are no matches, the label shows 'No matches'."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("nothing relevant here")
        view._search_input.setText("MISSING")

        assert len(view._search_positions) == 0
        assert "No matches" in view._match_label.text()
        assert not view._btn_next.isEnabled()
        assert not view._btn_prev.isEnabled()

    def test_search_buttons_enabled_only_with_matches(
        self, qtbot, mock_monitoring_vm
    ) -> None:
        """Next/Prev buttons are disabled until there are search matches."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        assert not view._btn_next.isEnabled()
        assert not view._btn_prev.isEnabled()

        mock_monitoring_vm.logs_loaded.emit("foo bar foo")
        view._search_input.setText("foo")
        assert view._btn_next.isEnabled()
        assert view._btn_prev.isEnabled()

        # Clear search
        view._search_input.setText("")
        assert not view._btn_next.isEnabled()
        assert not view._btn_prev.isEnabled()

    def test_search_cleared_resets_state(self, qtbot, mock_monitoring_vm) -> None:
        """Clearing the search input resets highlights and counter."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("aaa bbb aaa")
        view._search_input.setText("aaa")
        assert len(view._search_positions) == 2

        view._search_input.setText("")
        assert len(view._search_positions) == 0
        assert view._search_current_idx == -1
        assert view._match_label.text() == ""

    def test_clear_button_clears_search(self, qtbot, mock_monitoring_vm) -> None:
        """Clear button empties the search input and resets all search state."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        mock_monitoring_vm.logs_loaded.emit("foo bar foo baz foo")
        view._search_input.setText("foo")
        assert len(view._search_positions) == 3
        assert view._btn_clear_search.isEnabled()

        view._btn_clear_search.click()

        assert view._search_input.text() == ""
        assert len(view._search_positions) == 0
        assert view._search_current_idx == -1
        assert view._match_label.text() == ""
        assert not view._btn_clear_search.isEnabled()
        assert not view._btn_next.isEnabled()
        assert not view._btn_prev.isEnabled()

    def test_clear_button_disabled_when_search_empty(
        self, qtbot, mock_monitoring_vm
    ) -> None:
        """Clear button starts disabled and stays disabled with no search text."""
        from kuber.views.monitoring.logs_view import LogsView
        view = LogsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        assert not view._btn_clear_search.isEnabled()


class TestEventsView:
    def test_events_view_creates(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.events_view import EventsView
        view = EventsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)
        assert view._table is not None

    def test_events_loaded_populates_model(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.events_view import EventsView
        view = EventsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)

        events = [
            EventInfo(
                namespace="default", name="ev-1", type="Warning",
                reason="BackOff", message="Back-off pulling image",
                source="kubelet", involved_object="Pod/pod-1",
                count=5, age="2m",
            ),
            EventInfo(
                namespace="default", name="ev-2", type="Normal",
                reason="Scheduled", message="Successfully assigned",
                source="scheduler", involved_object="Pod/pod-2",
                count=1, age="1m",
            ),
        ]
        mock_monitoring_vm.events_loaded.emit(events)
        assert view._model.rowCount() == 2
        assert "2 event(s)" in view._status.text()

    def test_loading_shows_overlay(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.events_view import EventsView
        view = EventsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)
        view.show()

        mock_monitoring_vm.loading_changed.emit(True)
        assert view._overlay.isVisible()

        mock_monitoring_vm.loading_changed.emit(False)
        assert not view._overlay.isVisible()

    def test_type_filter_accessible_name(self, qtbot, mock_monitoring_vm) -> None:
        from kuber.views.monitoring.events_view import EventsView
        view = EventsView(view_model=mock_monitoring_vm)
        qtbot.addWidget(view)
        assert view._type_combo.accessibleName() != ""

