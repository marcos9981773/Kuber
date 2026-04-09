"""
kuber/views/settings/settings_view.py
Application settings panel — theme, language, clusters, backup schedule.
"""
from __future__ import annotations

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from kuber.constants import DEFAULT_LANGUAGE, DEFAULT_THEME, SUPPORTED_LANGUAGES, SUPPORTED_THEMES


class SettingsView(QWidget):
    """
    Application-wide settings panel.

    Sections:
        - Appearance (theme selection)
        - Language
        - Backup schedule
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._setup_ui()
        self._setup_accessibility()
        self._setup_tab_order()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        title = QLabel(self.tr("Settings"))
        title.setObjectName("pageTitle")
        layout.addWidget(title)

        # ── Appearance ───────────────────────────────────────────────────────
        appearance = QGroupBox(self.tr("Appearance"))
        app_form = QFormLayout(appearance)

        self._theme_combo = QComboBox()
        for theme in SUPPORTED_THEMES:
            self._theme_combo.addItem(theme.replace("_", " ").title(), theme)
        app_form.addRow(self.tr("Theme:"), self._theme_combo)

        layout.addWidget(appearance)

        # ── Language ─────────────────────────────────────────────────────────
        lang_group = QGroupBox(self.tr("Language"))
        lang_form = QFormLayout(lang_group)

        self._lang_combo = QComboBox()
        lang_labels = {"en": "English", "pt_BR": "Português (Brasil)"}
        for lang in SUPPORTED_LANGUAGES:
            self._lang_combo.addItem(lang_labels.get(lang, lang), lang)
        lang_form.addRow(self.tr("Language:"), self._lang_combo)

        layout.addWidget(lang_group)

        # ── Backup Schedule ──────────────────────────────────────────────────
        backup_group = QGroupBox(self.tr("Backup Schedule"))
        backup_form = QFormLayout(backup_group)

        self._auto_backup_check = QCheckBox(self.tr("Enable automatic backups"))
        backup_form.addRow(self._auto_backup_check)

        self._backup_interval = QSpinBox()
        self._backup_interval.setMinimum(1)
        self._backup_interval.setMaximum(720)
        self._backup_interval.setValue(24)
        self._backup_interval.setSuffix(self.tr(" hours"))
        backup_form.addRow(self.tr("Interval:"), self._backup_interval)

        layout.addWidget(backup_group)

        # ── Actions ──────────────────────────────────────────────────────────
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        self._btn_save = QPushButton(self.tr("💾 Save Settings"))
        self._btn_save.setObjectName("btnPrimary")
        btn_row.addWidget(self._btn_save)

        self._btn_reset = QPushButton(self.tr("↺ Reset to Defaults"))
        btn_row.addWidget(self._btn_reset)
        self._btn_reset.clicked.connect(self._on_reset)

        layout.addLayout(btn_row)

        self._status = QLabel("")
        self._status.setObjectName("resourceStatus")
        layout.addWidget(self._status)

        layout.addStretch()

    def _setup_accessibility(self) -> None:
        self._theme_combo.setAccessibleName(self.tr("Theme selector"))
        self._theme_combo.setAccessibleDescription(
            self.tr("Choose a visual theme for the application.")
        )
        self._lang_combo.setAccessibleName(self.tr("Language selector"))
        self._auto_backup_check.setAccessibleName(self.tr("Enable automatic backups"))
        self._backup_interval.setAccessibleName(self.tr("Backup interval in hours"))
        self._btn_save.setAccessibleName(self.tr("Save settings"))
        self._btn_reset.setAccessibleName(self.tr("Reset settings to defaults"))

    def _setup_tab_order(self) -> None:
        QWidget.setTabOrder(self._theme_combo, self._lang_combo)
        QWidget.setTabOrder(self._lang_combo, self._auto_backup_check)
        QWidget.setTabOrder(self._auto_backup_check, self._backup_interval)
        QWidget.setTabOrder(self._backup_interval, self._btn_save)
        QWidget.setTabOrder(self._btn_save, self._btn_reset)

    # ── Public API ───────────────────────────────────────────────────────────

    def get_theme(self) -> str:
        """Return the currently selected theme name."""
        return self._theme_combo.currentData() or DEFAULT_THEME

    def set_theme(self, theme: str) -> None:
        """Set the theme combo to a given value."""
        idx = self._theme_combo.findData(theme)
        if idx >= 0:
            self._theme_combo.setCurrentIndex(idx)

    def get_language(self) -> str:
        """Return the currently selected language code."""
        return self._lang_combo.currentData() or DEFAULT_LANGUAGE

    def set_language(self, lang: str) -> None:
        """Set the language combo to a given value."""
        idx = self._lang_combo.findData(lang)
        if idx >= 0:
            self._lang_combo.setCurrentIndex(idx)

    def is_auto_backup_enabled(self) -> bool:
        """Return whether auto-backup is enabled."""
        return self._auto_backup_check.isChecked()

    def set_auto_backup_enabled(self, enabled: bool) -> None:
        """Set auto-backup checkbox."""
        self._auto_backup_check.setChecked(enabled)

    def get_backup_interval_hours(self) -> int:
        """Return the backup interval in hours."""
        return self._backup_interval.value()

    def set_backup_interval_hours(self, hours: int) -> None:
        """Set the backup interval."""
        self._backup_interval.setValue(hours)

    def set_status(self, text: str) -> None:
        """Update the status label."""
        self._status.setText(text)

    def _on_reset(self) -> None:
        """Reset all settings to defaults."""
        self.set_theme(DEFAULT_THEME)
        self.set_language(DEFAULT_LANGUAGE)
        self.set_auto_backup_enabled(False)
        self.set_backup_interval_hours(24)
        self._status.setText(self.tr("Settings reset to defaults."))

