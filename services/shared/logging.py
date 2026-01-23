from __future__ import annotations

import logging
import logging.config
import os
from contextvars import ContextVar
from typing import Any

request_id_var: ContextVar[str] = ContextVar("request_id", default="-")

class RequestIdFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True

def configure_logging(*, service_name: str, level: str | None = None) -> None:
    """
    Configure logging for a service.

    - Output to stdout.
    - Single consistent format.
    - request_id is injected via ContextVar (for future HTTP/Kafka correlation).
    """
    lvl = (level or os.getenv("LOG_LEVEL", "INFO")).upper()

    log_format = (
        "%(asctime)s | %(levelname)s | %(service)s | %(name)s | rid=%(request_id)s | %(message)s"
    )

    config: dict[str, Any] = {
        "version": 1,
        "disable_existing_loggers": False,
        "filters": {
            "request_id": {"()": RequestIdFilter},
        },
        "formatters": {
            "default": {"format": log_format}
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "default",
                "filters": ["request_id"],
                "level": lvl,
            }
        },
        "root": {
            "handlers": ["console"],
            "level": lvl,
        },
        "loggers": {
            "uvicorn.access": {"level": os.getenv("UVICORN_ACCESS_LOG_LEVEL", "INFO")},
            "uvicorn.error": {"level": os.getenv("UVICORN_ERROR_LOG_LEVEL", lvl)},
        },
    }

    old_factory = logging.getLogRecordFactory()

    def record_factory(*args: Any, **kwargs: Any) -> logging.LogRecord:
        record = old_factory(*args, **kwargs)
        record.service = service_name
        return record

    logging.setLogRecordFactory(record_factory)
    logging.config.dictConfig(config)
