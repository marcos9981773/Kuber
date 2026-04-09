"""
tests/unit/views/test_resource_views.py
Tests for resource views (Pods, Deployments, Services, ConfigMaps).
"""
from __future__ import annotations

import pytest
from PyQt5.QtCore import QObject, pyqtSignal


@pytest.fixture
def mock_resource_vm():
    """Fake ResourceViewModel with all required signals."""

    class _FakeVM(QObject):
        items_loaded = pyqtSignal(list)
        item_deleted = pyqtSignal(str)
        action_completed = pyqtSignal(str)
        loading_changed = pyqtSignal(bool)
        error_occurred = pyqtSignal(str)
        namespaces_loaded = pyqtSignal(list)

        _namespace = "default"

        def load_items(self): pass
        def load_namespaces(self): pass
        def delete_item(self, name, ns=None): pass
        def set_namespace(self, ns): self._namespace = ns
        def scale(self, *a, **kw): pass
        def update_image(self, *a, **kw): pass
        def save_data(self, *a, **kw): pass

    return _FakeVM()


class TestPodsView:
    def test_pods_view_creates_with_table(self, qtbot, mock_resource_vm) -> None:
        from kuber.views.resources.pods_view import PodsView
        view = PodsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)
        assert view._table is not None
        assert view._title == "Pods"

    def test_pods_view_items_loaded_populates_model(self, qtbot, mock_resource_vm) -> None:
        from kuber.core.kubernetes.pods import PodInfo
        from kuber.views.resources.pods_view import PodsView
        view = PodsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)

        pods = [
            PodInfo("p1", "default", "Running", "1/1", 0, "node1", "nginx", "5m"),
            PodInfo("p2", "default", "Pending", "0/1", 1, "", "redis", "2m"),
        ]
        mock_resource_vm.items_loaded.emit(pods)
        assert view._model.rowCount() == 2

    def test_pods_view_has_context_menu_policy(self, qtbot, mock_resource_vm) -> None:
        """Table has CustomContextMenu policy for right-click support."""
        from PyQt5.QtCore import Qt
        from kuber.views.resources.pods_view import PodsView
        view = PodsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)
        assert view._table.contextMenuPolicy() == Qt.CustomContextMenu

    def test_pods_view_open_monitoring_signal_emitted(self, qtbot, mock_resource_vm) -> None:
        """open_monitoring_requested is emitted with pod name and namespace."""
        from kuber.core.kubernetes.pods import PodInfo
        from kuber.views.resources.pods_view import PodsView
        view = PodsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)

        pods = [
            PodInfo("my-pod", "production", "Running", "1/1", 0, "n1", "nginx", "5m"),
        ]
        mock_resource_vm.items_loaded.emit(pods)

        # Select the first row
        view._table.selectRow(0)

        signals: list[tuple[str, str]] = []
        view.open_monitoring_requested.connect(lambda name, ns: signals.append((name, ns)))

        # Invoke the monitoring action directly (avoids showing the actual menu)
        item = view._selected_item()
        view._on_open_monitoring(item)

        assert len(signals) == 1
        assert signals[0] == ("my-pod", "production")


class TestDeploymentsView:
    def test_deployments_view_has_scale_button(self, qtbot, mock_resource_vm) -> None:
        from kuber.views.resources.deployments_view import DeploymentsView
        view = DeploymentsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)
        assert hasattr(view, "_btn_scale")
        assert not view._btn_scale.isEnabled()

    def test_deployments_view_has_update_button(self, qtbot, mock_resource_vm) -> None:
        from kuber.views.resources.deployments_view import DeploymentsView
        view = DeploymentsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)
        assert hasattr(view, "_btn_update")


class TestServicesView:
    def test_services_view_creates(self, qtbot, mock_resource_vm) -> None:
        from kuber.views.resources.services_view import ServicesView
        view = ServicesView(view_model=mock_resource_vm)
        qtbot.addWidget(view)
        assert view._title == "Services"


class TestConfigMapsView:
    def test_configmaps_view_has_edit_button(self, qtbot, mock_resource_vm) -> None:
        from kuber.views.resources.configmaps_view import ConfigMapsView
        view = ConfigMapsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)
        assert hasattr(view, "_btn_edit")

    def test_configmaps_view_items_loaded(self, qtbot, mock_resource_vm) -> None:
        from kuber.core.kubernetes.configmaps import ConfigMapInfo
        from kuber.views.resources.configmaps_view import ConfigMapsView
        view = ConfigMapsView(view_model=mock_resource_vm)
        qtbot.addWidget(view)

        cms = [
            ConfigMapInfo("cm1", "default", ["k1"], "1d", {"k1": "v1"}),
        ]
        mock_resource_vm.items_loaded.emit(cms)
        assert view._model.rowCount() == 1


class TestNamespaceSelector:
    def test_namespace_selector_emits_change(self, qtbot) -> None:
        from kuber.views.common.namespace_selector import NamespaceSelector
        selector = NamespaceSelector()
        qtbot.addWidget(selector)
        selector.set_namespaces(["default", "kube-system"])

        signals = []
        selector.namespace_changed.connect(signals.append)
        selector._combo.setCurrentIndex(1)
        # The "All Namespaces" is index 0, "default" is 1
        assert len(signals) >= 1


class TestSearchBar:
    def test_search_bar_emits_debounced_signal(self, qtbot) -> None:
        from kuber.views.common.search_bar import SearchBar
        bar = SearchBar(placeholder="Filter…")
        qtbot.addWidget(bar)

        with qtbot.waitSignal(bar.search_changed, timeout=2000) as blocker:
            bar._input.setText("nginx")

        assert "nginx" in blocker.args[0]

