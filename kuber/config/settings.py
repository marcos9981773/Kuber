"""
kuber/config/settings.py
Application settings backed by QSettings.
"""
from __future__ import annotations

from typing import Any

from PyQt5.QtCore import QSettings

from kuber.constants import (
    APP_DOMAIN,
    APP_NAME,
    APP_ORGANIZATION,
    DEFAULT_LANGUAGE,
    DEFAULT_THEME,
)


class AppSettings:
    """
    Persistent application settings stored via QSettings.

    Uses the INI format on all platforms for portability.

    Example::

        settings = AppSettings()
        settings.theme = "dark"
        settings.save()
    """

    _THEME_KEY = "ui/theme"
    _LANGUAGE_KEY = "ui/language"
    _LAST_CONTEXT_KEY = "kubernetes/last_context"
    _WINDOW_GEOMETRY_KEY = "ui/window_geometry"
    _WINDOW_STATE_KEY = "ui/window_state"
    _BACKUP_SCHEDULE_KEY = "backup/schedule_hours"

    def __init__(self) -> None:
        self._qs = QSettings(APP_ORGANIZATION, APP_NAME)

    # ── Theme ────────────────────────────────────────────────
    @property
    def theme(self) -> str:
        return str(self._qs.value(self._THEME_KEY, DEFAULT_THEME))

    @theme.setter
    def theme(self, value: str) -> None:
        self._qs.setValue(self._THEME_KEY, value)

    # ── Language ─────────────────────────────────────────────
    @property
    def language(self) -> str:
        return str(self._qs.value(self._LANGUAGE_KEY, DEFAULT_LANGUAGE))

    @language.setter
    def language(self, value: str) -> None:
        self._qs.setValue(self._LANGUAGE_KEY, value)

    # ── Last active Kubernetes context ───────────────────────
    @property
    def last_kube_context(self) -> str:
        return str(self._qs.value(self._LAST_CONTEXT_KEY, ""))

    @last_kube_context.setter
    def last_kube_context(self, value: str) -> None:
        self._qs.setValue(self._LAST_CONTEXT_KEY, value)

    # ── Window geometry / state ──────────────────────────────
    @property
    def window_geometry(self) -> bytes | None:
        raw = self._qs.value(self._WINDOW_GEOMETRY_KEY)
        return bytes(raw) if raw else None

    @window_geometry.setter
    def window_geometry(self, value: bytes) -> None:
        self._qs.setValue(self._WINDOW_GEOMETRY_KEY, value)

    @property
    def window_state(self) -> bytes | None:
        raw = self._qs.value(self._WINDOW_STATE_KEY)
        return bytes(raw) if raw else None

    @window_state.setter
    def window_state(self, value: bytes) -> None:
        self._qs.setValue(self._WINDOW_STATE_KEY, value)

    # ── Backup schedule ──────────────────────────────────────
    @property
    def backup_schedule_hours(self) -> int:
        return int(self._qs.value(self._BACKUP_SCHEDULE_KEY, 0))

    @backup_schedule_hours.setter
    def backup_schedule_hours(self, value: int) -> None:
        self._qs.setValue(self._BACKUP_SCHEDULE_KEY, value)

    # ── Generic helpers ──────────────────────────────────────
    def get(self, key: str, default: Any = None) -> Any:
        """Return an arbitrary setting value."""
        return self._qs.value(key, default)

    def set(self, key: str, value: Any) -> None:
        """Store an arbitrary setting value."""
        self._qs.setValue(key, value)

    def save(self) -> None:
        """Flush all pending writes to disk."""
        self._qs.sync()

    def reset(self) -> None:
        """Clear all settings and restore defaults."""
        self._qs.clear()
        self._qs.sync()

