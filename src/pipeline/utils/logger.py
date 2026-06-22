"""
Logger estructurado compatible con Cloud Logging.
- Local: formato legible para humanos
- Producción: JSON indexable por Cloud Logging
"""
import json
import logging
import os
import sys
from datetime import datetime, timezone
from typing import Any


def get_logger(name: str) -> logging.Logger:
    """Retorna un logger configurado para el ambiente actual."""
    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    if os.getenv("ENVIRONMENT", "local") == "local":
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(
            logging.Formatter(
                fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
                datefmt="%Y-%m-%d %H:%M:%S",
            )
        )
    else:
        handler = logging.StreamHandler(sys.stdout)
        handler.setFormatter(_CloudFormatter())

    logger.addHandler(handler)
    return logger


class _CloudFormatter(logging.Formatter):
    """Formatea logs como JSON para Cloud Logging."""

    _SEVERITY: dict[int, str] = {
        logging.DEBUG: "DEBUG",
        logging.INFO: "INFO",
        logging.WARNING: "WARNING",
        logging.ERROR: "ERROR",
        logging.CRITICAL: "CRITICAL",
    }

    def format(self, record: logging.LogRecord) -> str:
        entry: dict[str, Any] = {
            "severity": self._SEVERITY.get(record.levelno, "DEFAULT"),
            "message": record.getMessage(),
            "logger": record.name,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        if record.exc_info:
            entry["stack_trace"] = self.formatException(record.exc_info)
        return json.dumps(entry, ensure_ascii=False)
