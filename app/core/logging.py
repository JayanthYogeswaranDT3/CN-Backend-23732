from __future__ import annotations

import logging
import sys
from typing import Any

from pythonjsonlogger import jsonlogger

from app.core.config import Settings


class RequestIdFilter(logging.Filter):
    """Inject request_id into log records when available on the record."""

    def filter(self, record: logging.LogRecord) -> bool:
        if not hasattr(record, "request_id"):
            record.request_id = None
        return True


def configure_logging(settings: Settings) -> None:
    """Configure structured JSON logging for the application."""
    root = logging.getLogger()
    root.setLevel(settings.log_level.upper())

    handler = logging.StreamHandler(sys.stdout)
    formatter = jsonlogger.JsonFormatter(
        fmt="%(asctime)s %(levelname)s %(name)s %(message)s %(request_id)s",
    )
    handler.setFormatter(formatter)
    handler.addFilter(RequestIdFilter())

    # Avoid duplicate handlers in reload
    root.handlers.clear()
    root.addHandler(handler)

    # Make Uvicorn loggers consistent
    for logger_name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logging.getLogger(logger_name).handlers.clear()
        logging.getLogger(logger_name).propagate = True
"
