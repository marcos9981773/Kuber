"""
main.py — Kuber application entry point.
"""
from __future__ import annotations

import sys


def main() -> None:
    """Start the Kuber desktop application."""
    # Ensure kuber dirs exist before importing Qt
    from pathlib import Path
    from kuber.constants import BACKUPS_DIR, LOGS_DIR

    for directory in (BACKUPS_DIR, LOGS_DIR):
        directory.mkdir(parents=True, exist_ok=True)

    # Qt must be imported after environment is ready
    from PyQt5.QtWidgets import QApplication
    from PyQt5.QtCore import Qt
    from kuber.app import KuberApplication

    # Enable HiDPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    kuber_app = KuberApplication(app)
    sys.exit(kuber_app.run())


if __name__ == "__main__":
    main()
