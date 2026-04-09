"""
kuber/views/common/theme_manager.py
Runtime theme switching via QSS files.
"""
from __future__ import annotations

import logging
from pathlib import Path

from PyQt5.QtWidgets import QApplication

from kuber.constants import DEFAULT_THEME, SUPPORTED_THEMES, THEMES_DIR

logger = logging.getLogger(__name__)


class ThemeManager:
    """
    Manages application-wide QSS theme loading and switching.

    Themes are QSS files in ``kuber/resources/themes/``.
    Supported values: ``"dark"``, ``"light"``, ``"high_contrast"``.

    Usage::

        # Apply at startup:
        ThemeManager.apply(app, theme="dark")

        # Switch at runtime (no restart required):
        ThemeManager.apply(app, theme="light")
    """

    _current_theme: str = ""

    @classmethod
    def apply(cls, app: QApplication, theme: str = DEFAULT_THEME) -> None:
        """
        Load and apply a QSS theme to the running application.

        Args:
            app:   The running QApplication instance.
            theme: Theme name. One of ``"dark"``, ``"light"``, ``"high_contrast"``.

        Raises:
            ValueError: If ``theme`` is not a recognised theme name.
        """
        if theme not in SUPPORTED_THEMES:
            raise ValueError(
                f"Unknown theme '{theme}'. Supported themes: {SUPPORTED_THEMES}"
            )

        qss = cls._load_qss(theme)
        app.setStyleSheet(qss)
        cls._current_theme = theme
        logger.info(f"Theme applied: '{theme}'")

    @classmethod
    def current_theme(cls) -> str:
        """Return the name of the currently active theme."""
        return cls._current_theme

    @classmethod
    def _load_qss(cls, theme: str) -> str:
        """Read the QSS file for the given theme name."""
        qss_path: Path = THEMES_DIR / f"{theme}.qss"
        if not qss_path.exists():
            logger.warning(f"QSS file not found for theme '{theme}': {qss_path}")
            return ""
        try:
            return qss_path.read_text(encoding="utf-8")
        except OSError as exc:
            logger.error(f"Failed to read QSS file '{qss_path}': {exc}")
            return ""

