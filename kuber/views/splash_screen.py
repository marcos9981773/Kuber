"""
kuber/views/splash_screen.py
Startup splash screen that runs pre-flight checks with progress feedback.
"""
from __future__ import annotations

import logging

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from kuber.utils.validators import CheckStatus, PreflightReport, run_preflight_checks

logger = logging.getLogger(__name__)


class SplashScreen(QWidget):
    """
    Startup splash that runs the 5 pre-flight checks sequentially.

    Displays each check name and result with a progress bar.
    On critical errors, shows a blocking error dialog before exit.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(self.tr("Starting Kuber…"))
        self.setWindowFlags(Qt.SplashScreen | Qt.FramelessWindowHint)
        self.setObjectName("splashScreen")
        self.setMinimumSize(480, 280)
        self._setup_ui()
        self._center_on_screen()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(32, 32, 32, 32)
        layout.setSpacing(16)
        layout.setAlignment(Qt.AlignCenter)

        # App logo / name
        title = QLabel("☸  Kuber")
        title.setObjectName("splashTitle")
        title.setAlignment(Qt.AlignCenter)
        title.setAccessibleName(self.tr("Kuber application name"))
        layout.addWidget(title)

        subtitle = QLabel(self.tr("Kubernetes Desktop Manager"))
        subtitle.setObjectName("splashSubtitle")
        subtitle.setAlignment(Qt.AlignCenter)
        layout.addWidget(subtitle)

        layout.addSpacing(16)

        # Check status label
        self._status_label = QLabel(self.tr("Initializing…"))
        self._status_label.setObjectName("splashStatus")
        self._status_label.setAlignment(Qt.AlignCenter)
        self._status_label.setAccessibleName(self.tr("Pre-flight check status"))
        layout.addWidget(self._status_label)

        # Progress bar
        self._progress = QProgressBar()
        self._progress.setObjectName("splashProgress")
        self._progress.setRange(0, 5)
        self._progress.setValue(0)
        self._progress.setTextVisible(False)
        self._progress.setAccessibleName(self.tr("Pre-flight checks progress"))
        layout.addWidget(self._progress)

        # Detail label
        self._detail_label = QLabel("")
        self._detail_label.setObjectName("splashDetail")
        self._detail_label.setAlignment(Qt.AlignCenter)
        self._detail_label.setWordWrap(True)
        layout.addWidget(self._detail_label)

    def run_checks(self) -> bool:
        """
        Execute all pre-flight checks with visual feedback.

        Returns:
            ``True`` if no critical errors were found, ``False`` otherwise.
        """
        check_names = [
            self.tr("Loading Kubernetes config…"),
            self.tr("Verifying cluster permissions…"),
            self.tr("Checking internet connectivity…"),
            self.tr("Checking Docker installation…"),
            self.tr("Validating Git configuration…"),
        ]

        results = []
        for i, name in enumerate(check_names):
            self._status_label.setText(name)
            self._progress.setValue(i)
            from PyQt5.QtWidgets import QApplication
            QApplication.processEvents()

            # Run individual check
            from kuber.utils import validators
            check_fns = [
                validators.check_kube_config,
                validators.check_kubernetes_permissions,
                validators.check_internet_connectivity,
                validators.check_docker,
                validators.check_git,
            ]
            result = check_fns[i]()
            results.append(result)

            icon = "✅" if result.status == CheckStatus.OK else (
                "⚠️" if result.status == CheckStatus.WARNING else "❌"
            )
            self._detail_label.setText(f"{icon} {result.message}")
            QApplication.processEvents()

        self._progress.setValue(5)
        self._status_label.setText(self.tr("Ready"))
        QApplication.processEvents()

        # Show error dialog for blocking failures
        errors = [r for r in results if r.status == CheckStatus.ERROR]
        if errors:
            from kuber.views.common.error_dialog import ErrorDialog
            for err in errors:
                ErrorDialog.show_error(
                    title=err.name,
                    message=err.message,
                    details=err.details,
                    fix_hint=err.fix_hint,
                    parent=self,
                )
            return False

        return True

    def _center_on_screen(self) -> None:
        from PyQt5.QtWidgets import QApplication
        screen = QApplication.primaryScreen()
        if screen:
            geo = screen.availableGeometry()
            self.move(
                geo.center().x() - self.width() // 2,
                geo.center().y() - self.height() // 2,
            )

