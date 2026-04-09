"""
kuber/constants.py
Global application constants for Kuber.
"""
from __future__ import annotations

from pathlib import Path

# ──────────────────────────────────────────────
# Application metadata
# ──────────────────────────────────────────────
APP_NAME = "Kuber"
APP_VERSION = "0.1.0"
APP_ORGANIZATION = "Kuber"
APP_DOMAIN = "kuber.io"

# ──────────────────────────────────────────────
# File system paths
# ──────────────────────────────────────────────
PACKAGE_DIR: Path = Path(__file__).parent
RESOURCES_DIR: Path = PACKAGE_DIR / "resources"
THEMES_DIR: Path = RESOURCES_DIR / "themes"
ICONS_DIR: Path = RESOURCES_DIR / "icons"
I18N_DIR: Path = PACKAGE_DIR / "i18n"

KUBE_CONFIG_DEFAULT: Path = Path.home() / ".kube" / "config"
BACKUPS_DIR: Path = Path.home() / ".kuber" / "backups"
LOGS_DIR: Path = Path.home() / ".kuber" / "logs"

# ──────────────────────────────────────────────
# Minimum required versions
# ──────────────────────────────────────────────
MIN_KUBERNETES_VERSION = (1, 27, 0)
MIN_DOCKER_VERSION = (20, 10, 0)
MIN_GIT_VERSION = (2, 39, 0)

# ──────────────────────────────────────────────
# UI / UX constants
# ──────────────────────────────────────────────
SUPPORTED_THEMES: list[str] = ["dark", "light", "high_contrast"]
DEFAULT_THEME = "dark"
SUPPORTED_LANGUAGES: list[str] = ["en", "pt_BR"]
DEFAULT_LANGUAGE = "en"

MAIN_WINDOW_MIN_WIDTH = 1024
MAIN_WINDOW_MIN_HEIGHT = 720
SIDEBAR_WIDTH = 220

# ──────────────────────────────────────────────
# Networking / API constants
# ──────────────────────────────────────────────
HTTP_TIMEOUT_SECONDS = 10
K8S_API_TIMEOUT_SECONDS = 30
K8S_WATCH_TIMEOUT_SECONDS = 60
CONNECTIVITY_CHECK_URL = "https://8.8.8.8"
CONNECTIVITY_CHECK_TIMEOUT = 5

# ──────────────────────────────────────────────
# Retry policy
# ──────────────────────────────────────────────
RETRY_MAX_ATTEMPTS = 3
RETRY_BASE_DELAY_SECONDS = 1.0
RETRY_BACKOFF_MULTIPLIER = 2.0

# ──────────────────────────────────────────────
# Polling intervals (milliseconds)
# ──────────────────────────────────────────────
CLUSTER_STATUS_POLL_INTERVAL_MS = 15_000
METRICS_POLL_INTERVAL_MS = 5_000
EVENTS_POLL_INTERVAL_MS = 10_000

