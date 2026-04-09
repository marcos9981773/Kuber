"""
tests/unit/views/test_cluster_views.py
Tests for cluster list view and cluster detail view.
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock


@pytest.fixture
def mock_vm(mocker):
    """Return a MagicMock that mimics ClusterViewModel signals."""
    from PyQt5.QtCore import QObject, pyqtSignal

    class _FakeVM(QObject):
        contexts_loaded = pyqtSignal(list)
        context_switched = pyqtSignal(str)
        cluster_info_loaded = pyqtSignal(object)
        loading_changed = pyqtSignal(bool)
        error_occurred = pyqtSignal(str)

        def load_contexts(self): pass
        def switch_context(self, name): pass
        def refresh_cluster_info(self): pass
        def start_polling(self): pass
        def stop_polling(self): pass

    return _FakeVM()


class TestClusterListView:
    """Tests for ClusterListView widget."""

    def test_cluster_list_view_creates_table(self, qtbot, mock_vm) -> None:
        """The view creates a QTableView bound to ClusterModel."""
        from kuber.views.cluster.cluster_list_view import ClusterListView
        view = ClusterListView(view_model=mock_vm)
        qtbot.addWidget(view)
        assert view._table is not None
        assert view._model is not None

    def test_cluster_list_view_accessible_names_set(self, qtbot, mock_vm) -> None:
        """All interactive widgets have accessible names."""
        from kuber.views.cluster.cluster_list_view import ClusterListView
        view = ClusterListView(view_model=mock_vm)
        qtbot.addWidget(view)
        assert view._table.accessibleName() != ""
        assert view._btn_refresh.accessibleName() != ""
        assert view._btn_switch.accessibleName() != ""

    def test_on_contexts_loaded_populates_model(self, qtbot, mock_vm) -> None:
        """contexts_loaded signal populates the table model."""
        from kuber.config.kube_config import KubeContext
        from kuber.views.cluster.cluster_list_view import ClusterListView
        view = ClusterListView(view_model=mock_vm)
        qtbot.addWidget(view)

        contexts = [
            KubeContext(name="prod", cluster="c1", user="u", is_active=True),
            KubeContext(name="staging", cluster="c2", user="u", is_active=False),
        ]
        mock_vm.contexts_loaded.emit(contexts)
        assert view._model.rowCount() == 2

    def test_loading_changed_true_shows_overlay(self, qtbot, mock_vm) -> None:
        """loading_changed=True shows the loading overlay."""
        from kuber.views.cluster.cluster_list_view import ClusterListView
        view = ClusterListView(view_model=mock_vm)
        qtbot.addWidget(view)
        view.show()

        mock_vm.loading_changed.emit(True)
        assert view._overlay.isVisible()

    def test_loading_changed_false_hides_overlay(self, qtbot, mock_vm) -> None:
        """loading_changed=False hides the loading overlay."""
        from kuber.views.cluster.cluster_list_view import ClusterListView
        view = ClusterListView(view_model=mock_vm)
        qtbot.addWidget(view)
        view.show()

        mock_vm.loading_changed.emit(True)
        mock_vm.loading_changed.emit(False)
        assert not view._overlay.isVisible()


class TestClusterDetailView:
    """Tests for ClusterDetailView widget."""

    def test_cluster_detail_view_initialises(self, qtbot, mock_vm) -> None:
        """Detail view creates without error."""
        from kuber.views.cluster.cluster_detail_view import ClusterDetailView
        view = ClusterDetailView(view_model=mock_vm)
        qtbot.addWidget(view)
        assert view is not None

    def test_cluster_info_loaded_populates_labels(self, qtbot, mock_vm) -> None:
        """cluster_info_loaded signal updates all detail labels."""
        from kuber.core.kubernetes.clusters import ClusterInfo
        from kuber.views.cluster.cluster_detail_view import ClusterDetailView
        view = ClusterDetailView(view_model=mock_vm)
        qtbot.addWidget(view)

        info = ClusterInfo(
            context_name="prod",
            server_url="https://k8s.example.com",
            k8s_version="1.29",
            node_count=3,
            namespace_count=5,
            is_reachable=True,
        )
        mock_vm.cluster_info_loaded.emit(info)

        assert view._lbl_context.text() == "prod"
        assert view._lbl_version.text() == "1.29"
        assert view._lbl_nodes.text() == "3"
        assert "Yes" in view._lbl_reachable.text()

