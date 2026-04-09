"""
tests/unit/viewmodels/test_cluster_vm.py
Tests for kuber/viewmodels/cluster_vm.py
"""
from __future__ import annotations

import pytest
from unittest.mock import MagicMock

from kuber.config.kube_config import KubeConfigInfo, KubeContext
from kuber.core.exceptions import KuberConnectionError


@pytest.fixture
def vm(qtbot, mocker):
    """ClusterViewModel with all external calls mocked."""
    mocker.patch("kuber.viewmodels.cluster_vm.load_kube_config")
    mocker.patch("kuber.viewmodels.cluster_vm.switch_context")
    mocker.patch("kuber.viewmodels.cluster_vm.get_cluster_info")
    from kuber.viewmodels.cluster_vm import ClusterViewModel
    instance = ClusterViewModel()
    qtbot.addWidget(instance)
    return instance


class TestClusterViewModelLoad:
    """Tests for load_contexts()."""

    def test_load_contexts_emits_contexts_loaded_signal(self, qtbot, mocker) -> None:
        """contexts_loaded signal is emitted with the list of KubeContexts."""
        mock_info = KubeConfigInfo(
            contexts=[KubeContext(name="ctx-a", cluster="c", user="u")],
            active_context_name="ctx-a",
        )
        mocker.patch(
            "kuber.viewmodels.cluster_vm.load_kube_config",
            return_value=mock_info,
        )
        mocker.patch("kuber.viewmodels.cluster_vm.get_cluster_info")

        from kuber.viewmodels.cluster_vm import ClusterViewModel
        vm = ClusterViewModel()

        with qtbot.waitSignal(vm.contexts_loaded, timeout=3000) as blocker:
            vm.load_contexts()

        contexts = blocker.args[0]
        assert len(contexts) == 1
        assert contexts[0].name == "ctx-a"

    def test_load_contexts_loading_changed_sequence(self, qtbot, mocker) -> None:
        """loading_changed emits True then False during load."""
        mock_info = KubeConfigInfo(contexts=[], active_context_name="")
        mocker.patch(
            "kuber.viewmodels.cluster_vm.load_kube_config",
            return_value=mock_info,
        )
        mocker.patch("kuber.viewmodels.cluster_vm.get_cluster_info")

        from kuber.viewmodels.cluster_vm import ClusterViewModel
        vm = ClusterViewModel()

        loading_states: list[bool] = []
        vm.loading_changed.connect(loading_states.append)

        with qtbot.waitSignal(vm.contexts_loaded, timeout=3000):
            vm.load_contexts()

        assert True in loading_states
        assert False in loading_states

    def test_load_contexts_error_emits_error_occurred(self, qtbot, mocker) -> None:
        """If load_kube_config raises, error_occurred is emitted."""
        mocker.patch(
            "kuber.viewmodels.cluster_vm.load_kube_config",
            side_effect=Exception("config missing"),
        )
        from kuber.viewmodels.cluster_vm import ClusterViewModel
        vm = ClusterViewModel()

        with qtbot.waitSignal(vm.error_occurred, timeout=3000) as blocker:
            vm.load_contexts()

        assert "config missing" in blocker.args[0]


class TestClusterViewModelSwitch:
    """Tests for switch_context()."""

    def test_switch_context_emits_context_switched(self, qtbot, mocker) -> None:
        """context_switched is emitted with the new context name."""
        from kuber.core.kubernetes.clusters import ClusterInfo

        mocker.patch("kuber.viewmodels.cluster_vm.switch_context")
        mocker.patch(
            "kuber.viewmodels.cluster_vm.get_cluster_info",
            return_value=ClusterInfo(context_name="ctx-b", server_url=""),
        )

        from kuber.viewmodels.cluster_vm import ClusterViewModel
        vm = ClusterViewModel()
        vm._config_info = KubeConfigInfo(
            contexts=[KubeContext(name="ctx-b", cluster="c", user="u", server="")],
            active_context_name="ctx-a",
        )

        # Wait for context_switched AND the subsequent cluster_info_loaded
        with qtbot.waitSignals(
            [vm.context_switched, vm.cluster_info_loaded], timeout=5000
        ):
            vm.switch_context("ctx-b")

        assert vm._config_info.active_context_name == "ctx-b"

