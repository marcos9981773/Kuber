"""
tests/unit/views/test_deploy_wizard.py
Tests for the deploy wizard pages and deploy progress dialog.
"""
from __future__ import annotations

import pytest
from PyQt5.QtCore import QObject, pyqtSignal


@pytest.fixture
def mock_deploy_vm():
    """Fake AppDeployViewModel with all required signals."""
    class _FakeVM(QObject):
        deploy_started = pyqtSignal()
        deploy_completed = pyqtSignal(str)
        deploy_failed = pyqtSignal(str)
        progress_log = pyqtSignal(str)
        def execute(self, spec): pass
    return _FakeVM()


class TestDockerDeployPage:
    def test_page_creates_with_fields(self, qtbot) -> None:
        from kuber.views.deployment.pages.docker_deploy_page import DockerDeployPage
        page = DockerDeployPage()
        qtbot.addWidget(page)
        assert page._image_input is not None
        assert page._replicas_spin.value() == 1

    def test_page_accessible_names(self, qtbot) -> None:
        from kuber.views.deployment.pages.docker_deploy_page import DockerDeployPage
        page = DockerDeployPage()
        qtbot.addWidget(page)
        assert page._image_input.accessibleName() != ""
        assert page._tag_input.accessibleName() != ""


class TestHelmDeployPage:
    def test_page_creates_with_fields(self, qtbot) -> None:
        from kuber.views.deployment.pages.helm_deploy_page import HelmDeployPage
        page = HelmDeployPage()
        qtbot.addWidget(page)
        assert page._chart_input is not None
        assert page._release_input is not None

    def test_get_values_yaml_returns_text(self, qtbot) -> None:
        from kuber.views.deployment.pages.helm_deploy_page import HelmDeployPage
        page = HelmDeployPage()
        qtbot.addWidget(page)
        page._values_editor.set_text("replicaCount: 3")
        assert "replicaCount" in page.get_values_yaml()


class TestManifestDeployPage:
    def test_page_not_complete_when_empty(self, qtbot) -> None:
        from kuber.views.deployment.pages.manifest_deploy_page import ManifestDeployPage
        page = ManifestDeployPage()
        qtbot.addWidget(page)
        assert not page.isComplete()

    def test_page_complete_with_yaml(self, qtbot) -> None:
        from kuber.views.deployment.pages.manifest_deploy_page import ManifestDeployPage
        page = ManifestDeployPage()
        qtbot.addWidget(page)
        page._editor.set_text("apiVersion: v1\nkind: Pod\nmetadata:\n  name: test")
        assert page.isComplete()


class TestReviewDeployPage:
    def test_set_summary_text(self, qtbot) -> None:
        from kuber.views.deployment.pages.review_deploy_page import ReviewDeployPage
        page = ReviewDeployPage()
        qtbot.addWidget(page)
        page.set_summary_text("Deploy nginx to default")
        assert "nginx" in page._summary.text()

    def test_dry_run_checkbox_default_unchecked(self, qtbot) -> None:
        from kuber.views.deployment.pages.review_deploy_page import ReviewDeployPage
        page = ReviewDeployPage()
        qtbot.addWidget(page)
        assert not page.is_dry_run()


class TestDeployProgressDialog:
    def test_dialog_creates_with_log(self, qtbot, mock_deploy_vm) -> None:
        from kuber.views.deployment.deploy_progress_dialog import DeployProgressDialog
        dialog = DeployProgressDialog(view_model=mock_deploy_vm)
        qtbot.addWidget(dialog)
        assert dialog._log is not None

    def test_progress_log_appends_text(self, qtbot, mock_deploy_vm) -> None:
        from kuber.views.deployment.deploy_progress_dialog import DeployProgressDialog
        dialog = DeployProgressDialog(view_model=mock_deploy_vm)
        qtbot.addWidget(dialog)
        mock_deploy_vm.progress_log.emit("Step 1 done")
        assert "Step 1 done" in dialog._log.toPlainText()

    def test_completed_enables_close(self, qtbot, mock_deploy_vm) -> None:
        from PyQt5.QtWidgets import QDialogButtonBox
        from kuber.views.deployment.deploy_progress_dialog import DeployProgressDialog
        dialog = DeployProgressDialog(view_model=mock_deploy_vm)
        qtbot.addWidget(dialog)
        mock_deploy_vm.deploy_completed.emit("Success!")
        assert dialog._buttons.button(QDialogButtonBox.Close).isEnabled()

    def test_failed_enables_close(self, qtbot, mock_deploy_vm) -> None:
        from PyQt5.QtWidgets import QDialogButtonBox
        from kuber.views.deployment.deploy_progress_dialog import DeployProgressDialog
        dialog = DeployProgressDialog(view_model=mock_deploy_vm)
        qtbot.addWidget(dialog)
        mock_deploy_vm.deploy_failed.emit("Error!")
        assert dialog._buttons.button(QDialogButtonBox.Close).isEnabled()

