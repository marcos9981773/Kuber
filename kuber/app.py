"""
kuber/app.py
QApplication bootstrap — theme, i18n, exception handling, splash screen.
"""
from __future__ import annotations

import logging
import sys
import traceback

from PyQt5.QtCore import Qt, QTranslator, QLocale, QLibraryInfo
from PyQt5.QtWidgets import QApplication, QMessageBox

from kuber.config.settings import AppSettings
from kuber.constants import APP_DOMAIN, APP_NAME, APP_ORGANIZATION, LOGS_DIR
from kuber.utils.logger import setup_logging
from kuber.views.common.theme_manager import ThemeManager

logger = logging.getLogger(__name__)


class KuberApplication:
    """
    Bootstraps the Kuber desktop application.

    Responsibilities:
    - Set up structured logging
    - Apply the saved theme
    - Load i18n translations
    - Install a global exception handler
    - Show the splash screen and run pre-flight checks
    - Launch the main window
    """

    def __init__(self, app: QApplication) -> None:
        self._app = app
        self._settings = AppSettings()
        self._setup_app_metadata()
        self._setup_logging()
        self._install_exception_handler()
        self._setup_theme()
        self._setup_i18n()

    # ── Public API ──────────────────────────────────────────────────────────

    def run(self) -> int:
        """
        Start the application event loop.

        Shows the splash screen for pre-flight checks, then the main window.

        Returns:
            Process exit code.
        """
        from kuber.views.splash_screen import SplashScreen
        from kuber.views.main_window import MainWindow

        splash = SplashScreen()
        splash.show()
        self._app.processEvents()

        if splash.run_checks():
            splash.close()
            window = MainWindow(settings=self._settings)
            self._setup_views(window)
            window.show()
            return self._app.exec_()

        # Pre-flight failed — splash already showed errors, exit cleanly
        splash.close()
        return 1

    def _setup_views(self, window: MainWindow) -> None:  # type: ignore[name-defined]
        """Create all ViewModels and Views and wire them into the MainWindow."""
        from kuber.views.main_window import (
            PAGE_CLUSTERS,
            PAGE_PODS,
            PAGE_DEPLOYMENTS,
            PAGE_SERVICES,
            PAGE_CONFIGMAPS,
            PAGE_DEPLOYMENT_WIZARD,
            PAGE_MONITORING,
            PAGE_USERS,
            PAGE_BACKUP,
            PAGE_SETTINGS,
        )

        # ── ViewModels ────────────────────────────────────────────────────────
        from kuber.viewmodels.cluster_vm import ClusterViewModel
        from kuber.viewmodels.monitoring_vm import MonitoringViewModel

        cluster_vm = ClusterViewModel()
        monitoring_vm = MonitoringViewModel()

        # ── Cluster page ──────────────────────────────────────────────────────
        from kuber.views.cluster.cluster_list_view import ClusterListView

        cluster_view = ClusterListView(view_model=cluster_vm)
        window.replace_page(PAGE_CLUSTERS, cluster_view)

        # Update toolbar cluster label when context changes
        cluster_vm.context_switched.connect(window.set_cluster_label)
        cluster_vm.contexts_loaded.connect(
            lambda ctxs: window.set_cluster_label(
                next((c.name for c in ctxs if c.is_active), "")
            )
        )

        # ── Resource pages (Pods, Deployments, Services, ConfigMaps) ─────────
        from kuber.views.resources.pods_view import PodsView
        from kuber.views.resources.deployments_view import DeploymentsView
        from kuber.views.resources.services_view import ServicesView
        from kuber.views.resources.configmaps_view import ConfigMapsView

        pods_view = PodsView()
        window.replace_page(PAGE_PODS, pods_view)
        window.replace_page(PAGE_DEPLOYMENTS, DeploymentsView())
        window.replace_page(PAGE_SERVICES, ServicesView())
        window.replace_page(PAGE_CONFIGMAPS, ConfigMapsView())

        # ── Deploy wizard launcher page ───────────────────────────────────────
        from kuber.views.deployment.deploy_wizard import DeployWizard
        from PyQt5.QtWidgets import QPushButton, QVBoxLayout, QWidget, QLabel

        deploy_page = QWidget()
        deploy_layout = QVBoxLayout(deploy_page)
        deploy_layout.setAlignment(Qt.AlignCenter)  # type: ignore[arg-type]
        deploy_title = QLabel("🚀  Deploy Application")
        deploy_title.setObjectName("pageTitle")
        deploy_title.setAlignment(Qt.AlignCenter)  # type: ignore[arg-type]
        deploy_layout.addWidget(deploy_title)
        deploy_btn = QPushButton("📦  Launch Deploy Wizard")
        deploy_btn.setObjectName("btnPrimary")
        deploy_btn.setAccessibleName("Launch deploy wizard")
        deploy_btn.clicked.connect(
            lambda: DeployWizard(parent=window).exec_()  # type: ignore[arg-type]
        )
        deploy_layout.addWidget(deploy_btn, alignment=Qt.AlignCenter)  # type: ignore[arg-type]
        window.replace_page(PAGE_DEPLOYMENT_WIZARD, deploy_page)

        # ── Monitoring page (tabs: Metrics, Logs, Events) ────────────────────
        from PyQt5.QtWidgets import QTabWidget
        from kuber.views.monitoring.metrics_view import MetricsView
        from kuber.views.monitoring.logs_view import LogsView
        from kuber.views.monitoring.events_view import EventsView

        monitoring_tabs = QTabWidget()
        monitoring_tabs.setObjectName("monitoringTabs")
        monitoring_tabs.setAccessibleName("Monitoring tabs")
        monitoring_tabs.addTab(MetricsView(view_model=monitoring_vm), "📊 Metrics")
        logs_view = LogsView(view_model=monitoring_vm)
        monitoring_tabs.addTab(logs_view, "📝 Logs")
        monitoring_tabs.addTab(EventsView(view_model=monitoring_vm), "⚡ Events")
        window.replace_page(PAGE_MONITORING, monitoring_tabs)

        # Connect Pods → Monitoring navigation
        _LOGS_TAB_INDEX = 1

        def _open_pod_in_monitoring(pod_name: str, namespace: str) -> None:
            window._navigate_to(PAGE_MONITORING)
            monitoring_tabs.setCurrentIndex(_LOGS_TAB_INDEX)
            logs_view.set_pod(pod_name, namespace)

        pods_view.open_monitoring_requested.connect(_open_pod_in_monitoring)

        # ── Users page ────────────────────────────────────────────────────────
        from kuber.views.users.users_view import UsersView

        window.replace_page(PAGE_USERS, UsersView())

        # ── Backup page ──────────────────────────────────────────────────────
        from kuber.views.backup.backup_view import BackupView

        window.replace_page(PAGE_BACKUP, BackupView())

        # ── Settings page ────────────────────────────────────────────────────
        from kuber.views.settings.settings_view import SettingsView

        window.replace_page(PAGE_SETTINGS, SettingsView())

        # Ensure the first visible page is Clusters with its sidebar button highlighted
        window._navigate_to(PAGE_CLUSTERS)

        logger.info("All views initialised and wired to MainWindow.")

    # ── Private setup ───────────────────────────────────────────────────────

    def _setup_app_metadata(self) -> None:
        self._app.setApplicationName(APP_NAME)
        self._app.setOrganizationName(APP_ORGANIZATION)
        self._app.setOrganizationDomain(APP_DOMAIN)
        self._app.setApplicationVersion("0.1.0")

    def _setup_logging(self) -> None:
        setup_logging(log_dir=LOGS_DIR)
        logger.info(f"{APP_NAME} starting up…")

    def _install_exception_handler(self) -> None:
        """Replace default excepthook with a user-friendly dialog."""

        def _handler(exc_type: type, exc_value: BaseException, exc_tb: object) -> None:
            if issubclass(exc_type, KeyboardInterrupt):
                sys.__excepthook__(exc_type, exc_value, exc_tb)
                return
            tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_tb))
            logger.critical(f"Unhandled exception:\n{tb_str}")
            QMessageBox.critical(
                None,
                "Unexpected Error",
                f"An unexpected error occurred:\n\n{exc_value}\n\n"
                "The application will attempt to continue. Check the log file for details.",
            )

        sys.excepthook = _handler

    def _setup_theme(self) -> None:
        theme = self._settings.theme
        try:
            ThemeManager.apply(self._app, theme=theme)
        except (ValueError, OSError) as exc:
            logger.warning(f"Could not apply theme '{theme}': {exc}. Falling back to 'dark'.")
            ThemeManager.apply(self._app, theme="dark")

    def _setup_i18n(self) -> None:
        locale = QLocale(self._settings.language)
        QLocale.setDefault(locale)

        # Qt built-in translations
        qt_translator = QTranslator(self._app)
        translations_path = QLibraryInfo.location(QLibraryInfo.TranslationsPath)
        if qt_translator.load(locale, "qt", "_", translations_path):
            self._app.installTranslator(qt_translator)

        # App-specific translations
        from kuber.constants import I18N_DIR
        app_translator = QTranslator(self._app)
        if app_translator.load(locale, "kuber", "_", str(I18N_DIR)):
            self._app.installTranslator(app_translator)

        logger.info(f"i18n locale: {locale.name()}")

