"""
kuber/utils/logger.py
Structured JSON logging with file rotation for Kuber.
"""
from __future__ import annotations

import json
import logging
import logging.handlers
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class _JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "line": record.lineno,
        }
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, ensure_ascii=False)


def setup_logging(
    log_dir: Path,
    level: int = logging.INFO,
    max_bytes: int = 5 * 1024 * 1024,  # 5 MB
    backup_count: int = 5,
) -> None:
    """
    Configure application-wide logging.

    Sets up two handlers:
    - Rotating JSON file handler in ``log_dir``
    - Console (stderr) handler with a human-readable format

    Args:
        log_dir:      Directory where log files are written.
        level:        Root logging level (default: INFO).
        max_bytes:    Max size per log file before rotation.
        backup_count: Number of rotated files to keep.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "kuber.log"

    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    # Remove existing handlers to avoid duplication on re-init
    root_logger.handlers.clear()

    # ── File handler (JSON) ─────────────────────────────────
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setFormatter(_JsonFormatter())
    root_logger.addHandler(file_handler)

    # ── Console handler (human readable) ───────────────────
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setFormatter(
        logging.Formatter(
            fmt="%(asctime)s [%(levelname)-8s] %(name)s — %(message)s",
            datefmt="%H:%M:%S",
        )
    )
    root_logger.addHandler(console_handler)

    logging.getLogger("kubernetes").setLevel(logging.WARNING)
    logging.getLogger("docker").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger. Convenience wrapper around logging.getLogger."""
    return logging.getLogger(name)

