"""
tests/unit/views/test_base_worker.py
Tests for kuber/views/common/base_worker.py
"""
from __future__ import annotations

import pytest


class TestBaseWorker:
    """Tests for BaseWorker QThread abstraction."""

    def test_base_worker_finished_signal_emitted_with_result(self, qtbot) -> None:
        """finished signal carries the return value of run_task."""
        from kuber.views.common.base_worker import BaseWorker

        class _Worker(BaseWorker):
            def run_task(self):
                return [1, 2, 3]

        worker = _Worker()
        results = []
        worker.finished.connect(lambda r: results.append(r))
        with qtbot.waitSignal(worker.finished, timeout=3000):
            worker.start()

        assert results == [[1, 2, 3]]

    def test_base_worker_error_signal_emitted_on_exception(self, qtbot) -> None:
        """error signal is emitted when run_task raises."""
        from kuber.views.common.base_worker import BaseWorker

        class _Worker(BaseWorker):
            def run_task(self):
                raise ValueError("boom")

        worker = _Worker()
        errors = []
        worker.error.connect(lambda e: errors.append(e))
        with qtbot.waitSignal(worker.error, timeout=3000):
            worker.start()

        assert len(errors) == 1
        assert "boom" in errors[0]

    def test_base_worker_run_task_not_implemented_raises(self, qtbot) -> None:
        """Unoverridden run_task emits an error signal."""
        from kuber.views.common.base_worker import BaseWorker

        worker = BaseWorker()
        errors = []
        worker.error.connect(lambda e: errors.append(e))
        with qtbot.waitSignal(worker.error, timeout=3000):
            worker.start()

        assert len(errors) == 1
        assert "run_task" in errors[0]


class TestThemeManager:
    """Tests for ThemeManager."""

    def test_apply_unknown_theme_raises_value_error(self, qtbot) -> None:
        """Applying an unknown theme name raises ValueError."""
        from PyQt5.QtWidgets import QApplication
        from kuber.views.common.theme_manager import ThemeManager

        with pytest.raises(ValueError, match="Unknown theme"):
            ThemeManager.apply(QApplication.instance(), theme="neon_rainbow")

    def test_apply_valid_theme_sets_current_theme(self, qtbot, tmp_path, mocker) -> None:
        """After apply(), current_theme() returns the new theme name."""
        from PyQt5.QtWidgets import QApplication
        from kuber.views.common.theme_manager import ThemeManager

        # Mock _load_qss so we don't need actual files
        mocker.patch.object(ThemeManager, "_load_qss", return_value="")
        ThemeManager.apply(QApplication.instance(), theme="light")
        assert ThemeManager.current_theme() == "light"


class TestErrorDialog:
    """Tests for ErrorDialog widget."""

    def test_error_dialog_creates_without_details(self, qtbot) -> None:
        """Dialog can be created with message only (no details or hint)."""
        from kuber.views.common.error_dialog import ErrorDialog

        dialog = ErrorDialog(title="Test Error", message="Something went wrong.")
        qtbot.addWidget(dialog)
        assert dialog.windowTitle().startswith("Error")

    def test_error_dialog_creates_with_all_fields(self, qtbot) -> None:
        """Dialog accepts title, message, details, and fix_hint."""
        from kuber.views.common.error_dialog import ErrorDialog

        dialog = ErrorDialog(
            title="Connect Failed",
            message="Could not connect.",
            details="Connection refused",
            fix_hint="Check your VPN.",
        )
        qtbot.addWidget(dialog)
        assert dialog is not None

