"""
kuber/views/main_window.py
Main application window with sidebar navigation and central stacked widget.
"""
from __future__ import annotations

import logging

from PyQt5.QtCore import Qt, QSize
from PyQt5.QtWidgets import (
    QAction,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QStackedWidget,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from kuber.config.settings import AppSettings
from kuber.constants import (
    APP_NAME,
    MAIN_WINDOW_MIN_HEIGHT,
    MAIN_WINDOW_MIN_WIDTH,
    SIDEBAR_WIDTH,
    SUPPORTED_THEMES,
)

logger = logging.getLogger(__name__)

# ── Navigation page indices ──────────────────────────────────────────────────
PAGE_CLUSTERS = 0
PAGE_PODS = 1
PAGE_DEPLOYMENTS = 2
PAGE_SERVICES = 3
PAGE_CONFIGMAPS = 4
PAGE_DEPLOYMENT_WIZARD = 5
PAGE_MONITORING = 6
PAGE_USERS = 7
PAGE_BACKUP = 8
PAGE_SETTINGS = 9


class MainWindow(QMainWindow):
    """
    Main application window.

    Layout:
    ┌────────────────────────────────────────┐
    │  Toolbar (cluster switcher + actions)  │
    ├──────────┬─────────────────────────────┤
    │ Sidebar  │  Central stacked widget     │
    │ (nav)    │  (one page per feature)     │
    ├──────────┴─────────────────────────────┤
    │  Status bar                            │
    └────────────────────────────────────────┘
    """

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._settings = settings
        self._nav_buttons: list[QPushButton] = []
        self._setup_window()
        self._setup_toolbar()
        self._setup_central()
        self._setup_status_bar()
        self._setup_shortcuts()
        self._restore_geometry()
        logger.info("MainWindow initialised.")

    # ── Window setup ─────────────────────────────────────────────────────────

    def _setup_window(self) -> None:
        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(MAIN_WINDOW_MIN_WIDTH, MAIN_WINDOW_MIN_HEIGHT)
        self.setObjectName("mainWindow")
        self.setAccessibleName(self.tr("Kuber main window"))

    # ── Toolbar ───────────────────────────────────────────────────────────────

    def _setup_toolbar(self) -> None:
        toolbar = QToolBar(self.tr("Main Toolbar"))
        toolbar.setObjectName("mainToolbar")
        toolbar.setMovable(False)
        toolbar.setAccessibleName(self.tr("Main application toolbar"))
        self.addToolBar(toolbar)

        # App brand label
        brand = QLabel(f" ☸ {APP_NAME} ")
        brand.setObjectName("toolbarBrand")
        brand.setAccessibleName(self.tr("Application name"))
        toolbar.addWidget(brand)

        toolbar.addSeparator()

        # Cluster context label (populated by ViewModel later)
        self._cluster_label = QLabel(self.tr("No cluster connected"))
        self._cluster_label.setObjectName("toolbarClusterLabel")
        self._cluster_label.setAccessibleName(self.tr("Active cluster context"))
        toolbar.addWidget(self._cluster_label)

        # Spacer to push right-side actions to the right
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        toolbar.addWidget(spacer)

        # Theme toggle action
        self._theme_action = QAction(self.tr("🌗 Theme"), self)
        self._theme_action.setToolTip(self.tr("Switch application theme"))
        self._theme_action.triggered.connect(self._on_cycle_theme)
        toolbar.addAction(self._theme_action)

    # ── Central layout (sidebar + stacked) ────────────────────────────────────

    def _setup_central(self) -> None:
        central = QWidget()
        central.setObjectName("centralWidget")
        self.setCentralWidget(central)

        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        sidebar = self._build_sidebar()
        main_layout.addWidget(sidebar)

        # Stacked pages
        self._stack = QStackedWidget()
        self._stack.setObjectName("contentStack")
        self._stack.setAccessibleName(self.tr("Content area"))
        self._populate_pages()
        main_layout.addWidget(self._stack, stretch=1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QWidget()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(SIDEBAR_WIDTH)
        sidebar.setAccessibleName(self.tr("Navigation sidebar"))

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(2)

        nav_items = [
            ("☸", self.tr("Clusters"),     PAGE_CLUSTERS,          "Ctrl+1"),
            ("🐳", self.tr("Pods"),         PAGE_PODS,              "Ctrl+2"),
            ("🚀", self.tr("Deployments"),  PAGE_DEPLOYMENTS,       "Ctrl+3"),
            ("🔗", self.tr("Services"),     PAGE_SERVICES,          "Ctrl+4"),
            ("📄", self.tr("ConfigMaps"),   PAGE_CONFIGMAPS,        "Ctrl+5"),
            ("📦", self.tr("Deploy"),       PAGE_DEPLOYMENT_WIZARD, "Ctrl+6"),
            ("📊", self.tr("Monitoring"),   PAGE_MONITORING,        "Ctrl+7"),
            ("👤", self.tr("Users"),        PAGE_USERS,             "Ctrl+8"),
            ("💾", self.tr("Backup"),       PAGE_BACKUP,            "Ctrl+9"),
        ]

        for icon, label, page_idx, shortcut in nav_items:
            btn = QPushButton(f"  {icon}  {label}")
            btn.setObjectName("sidebarItem")
            btn.setCheckable(True)
            btn.setShortcut(shortcut)
            btn.setAccessibleName(self.tr("{0} navigation button").format(label))
            btn.setAccessibleDescription(
                self.tr("Navigate to the {0} section. Shortcut: {1}").format(label, shortcut)
            )
            btn.clicked.connect(lambda checked, idx=page_idx: self._navigate_to(idx))
            layout.addWidget(btn)
            self._nav_buttons.append(btn)

        layout.addStretch()

        # Settings at the bottom
        settings_btn = QPushButton(f"  ⚙️  {self.tr('Settings')}")
        settings_btn.setObjectName("sidebarItem")
        settings_btn.setCheckable(True)
        settings_btn.setShortcut("Ctrl+,")
        settings_btn.setAccessibleName(self.tr("Settings navigation button"))
        settings_btn.clicked.connect(lambda: self._navigate_to(PAGE_SETTINGS))
        layout.addWidget(settings_btn)
        self._nav_buttons.append(settings_btn)

        return sidebar

    def _populate_pages(self) -> None:
        """Insert placeholder pages; real views will be swapped in by ViewModels."""
        page_names = [
            self.tr("Clusters"),
            self.tr("Pods"),
            self.tr("Deployments"),
            self.tr("Services"),
            self.tr("ConfigMaps"),
            self.tr("Deploy Application"),
            self.tr("Monitoring"),
            self.tr("Users"),
            self.tr("Backup & Restore"),
            self.tr("Settings"),
        ]
        for name in page_names:
            placeholder = QLabel(name)
            placeholder.setAlignment(Qt.AlignCenter)
            placeholder.setObjectName("pagePlaceholder")
            self._stack.addWidget(placeholder)

        # Navigate to clusters by default
        self._navigate_to(PAGE_CLUSTERS)

    # ── Status bar ─────────────────────────────────────────────────────────────

    def _setup_status_bar(self) -> None:
        status_bar = QStatusBar()
        status_bar.setObjectName("mainStatusBar")
        status_bar.setAccessibleName(self.tr("Application status bar"))
        self.setStatusBar(status_bar)
        self._status_msg = QLabel(self.tr("Ready"))
        self._status_msg.setAccessibleName(self.tr("Status message"))
        status_bar.addWidget(self._status_msg)

    # ── Keyboard shortcuts ─────────────────────────────────────────────────────

    def _setup_shortcuts(self) -> None:
        """Define additional application-wide shortcuts."""
        from PyQt5.QtWidgets import QShortcut
        from PyQt5.QtGui import QKeySequence

        # Ctrl+Tab / Ctrl+Shift+Tab — cycle through pages
        next_shortcut = QShortcut(QKeySequence("Ctrl+Tab"), self)
        next_shortcut.activated.connect(self._navigate_next)
        prev_shortcut = QShortcut(QKeySequence("Ctrl+Shift+Tab"), self)
        prev_shortcut.activated.connect(self._navigate_prev)

        # Set explicit tab order for sidebar buttons
        for i in range(len(self._nav_buttons) - 1):
            QWidget.setTabOrder(self._nav_buttons[i], self._nav_buttons[i + 1])

    # ── Navigation ─────────────────────────────────────────────────────────────

    def _navigate_to(self, page_idx: int) -> None:
        """Switch the stacked widget to the given page index."""
        self._stack.setCurrentIndex(page_idx)
        for i, btn in enumerate(self._nav_buttons):
            # Map nav button index to page index (last button = settings)
            nav_page = i if i < PAGE_SETTINGS else PAGE_SETTINGS
            btn.setChecked(nav_page == page_idx)
        logger.debug(f"Navigated to page {page_idx}.")

    def _navigate_next(self) -> None:
        total = self._stack.count()
        self._navigate_to((self._stack.currentIndex() + 1) % total)

    def _navigate_prev(self) -> None:
        total = self._stack.count()
        self._navigate_to((self._stack.currentIndex() - 1) % total)

    # ── Public API ─────────────────────────────────────────────────────────────

    def set_cluster_label(self, context_name: str) -> None:
        """Update the toolbar cluster label."""
        self._cluster_label.setText(f"☸  {context_name}")

    def set_status(self, message: str) -> None:
        """Update the status bar message."""
        self._status_msg.setText(message)

    def replace_page(self, page_idx: int, widget: QWidget) -> None:
        """Replace a placeholder page with a real view widget."""
        old = self._stack.widget(page_idx)
        if old:
            self._stack.removeWidget(old)
            old.deleteLater()
        self._stack.insertWidget(page_idx, widget)

    # ── Theme cycling ──────────────────────────────────────────────────────────

    def _on_cycle_theme(self) -> None:
        from PyQt5.QtWidgets import QApplication
        from kuber.views.common.theme_manager import ThemeManager

        current = ThemeManager.current_theme() or self._settings.theme
        idx = SUPPORTED_THEMES.index(current) if current in SUPPORTED_THEMES else 0
        next_theme = SUPPORTED_THEMES[(idx + 1) % len(SUPPORTED_THEMES)]
        ThemeManager.apply(QApplication.instance(), theme=next_theme)
        self._settings.theme = next_theme
        self._settings.save()
        self.set_status(self.tr("Theme: {0}").format(next_theme))

    # ── Geometry persistence ───────────────────────────────────────────────────

    def _restore_geometry(self) -> None:
        geo = self._settings.window_geometry
        state = self._settings.window_state
        if geo:
            self.restoreGeometry(geo)
        if state:
            self.restoreState(state)

    def closeEvent(self, event) -> None:  # type: ignore[override]
        self._settings.window_geometry = bytes(self.saveGeometry())
        self._settings.window_state = bytes(self.saveState())
        self._settings.save()
        logger.info("MainWindow closed — geometry saved.")
        super().closeEvent(event)

