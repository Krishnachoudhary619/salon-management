import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog

from app.core.config import Settings
from app.core.constants import SENSITIVE_LOG_KEYS


def _redact_value(key: str, value: Any) -> Any:
    if key.lower() in SENSITIVE_LOG_KEYS:
        return "***REDACTED***"
    if isinstance(value, dict):
        return {
            inner_key: _redact_value(str(inner_key), inner_value)
            for inner_key, inner_value in value.items()
        }
    if isinstance(value, list):
        return [_redact_value(key, item) for item in value]
    return value


def _redact_sensitive_data(
    _logger: Any,
    _method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    return {key: _redact_value(key, value) for key, value in event_dict.items()}


def configure_logging(settings: Settings) -> None:
    """Configure structured logging. Never logs passwords or tokens."""

    log_level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)
    renderer: structlog.types.Processor
    if settings.LOG_JSON or settings.is_production:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer()

    shared_processors: list[structlog.types.Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.TimeStamper(fmt="iso", utc=True),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        _redact_sensitive_data,
    ]

    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    formatter = structlog.stdlib.ProcessorFormatter(
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            renderer,
        ],
        foreign_pre_chain=shared_processors,
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    root_logger = logging.getLogger()
    root_logger.handlers.clear()
    root_logger.addHandler(handler)
    root_logger.setLevel(log_level)

    for name in ("uvicorn", "uvicorn.error", "uvicorn.access", "sqlalchemy.engine"):
        named_logger = logging.getLogger(name)
        named_logger.handlers.clear()
        named_logger.propagate = True


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    return structlog.get_logger(name)
