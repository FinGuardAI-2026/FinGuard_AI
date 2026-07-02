"""
backend/app/core/logging/logger.py  (production-grade structured logging)
─────────────────────────────────────────────────────────────────────────
Configures a JSON-structured logger for the entire application.
In production (DEBUG=false), all output is JSON for log aggregators.
In development (DEBUG=true), coloured human-readable output is used.
"""
import logging
import sys
import json
import os
from datetime import datetime, timezone


class JsonFormatter(logging.Formatter):
    """Formats log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Attach optional structured fields
        if hasattr(record, "request_id"):
            log_entry["request_id"] = record.request_id

        # Capture exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(log_entry)


class DevFormatter(logging.Formatter):
    """Human-readable coloured formatter for local development."""

    COLOURS = {
        "DEBUG": "\033[36m",    # cyan
        "INFO": "\033[32m",     # green
        "WARNING": "\033[33m",  # yellow
        "ERROR": "\033[31m",    # red
        "CRITICAL": "\033[35m", # magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        colour = self.COLOURS.get(record.levelname, "")
        ts = datetime.now(timezone.utc).strftime("%H:%M:%S")
        prefix = f"{colour}[{record.levelname}]{self.RESET}"
        request_id = getattr(record, "request_id", None)
        rid = f" ({request_id[:8]}…)" if request_id else ""
        return f"{ts} {prefix}{rid} {record.getMessage()}"


def _build_logger() -> logging.Logger:
    debug_mode = os.getenv("DEBUG", "false").lower() in ("1", "true", "yes")

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(DevFormatter() if debug_mode else JsonFormatter())

    log = logging.getLogger("finguard")
    log.setLevel(logging.DEBUG if debug_mode else logging.INFO)
    log.handlers.clear()
    log.addHandler(handler)
    log.propagate = False
    return log


logger = _build_logger()
