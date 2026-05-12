from __future__ import annotations

import logging
import sys

from pythonjsonlogger import jsonlogger

from src.core.settings import get_settings


def configure_logging() -> None:
    """Configure structured JSON logging for the application."""
    settings = get_settings()
    level = getattr(logging, settings.log_level.upper(), logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        "%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s %(method)s %(path)s %(status_code)s %(duration_ms)s"
    )
    handler.setFormatter(formatter)

    root = logging.getLogger()
    root.handlers = []
    root.setLevel(level)
    root.addHandler(handler)


# PUBLIC_INTERFACE
def get_logger(name: str) -> logging.Logger:
    """Get a logger instance (logging must be configured at startup)."""
    return logging.getLogger(name)
