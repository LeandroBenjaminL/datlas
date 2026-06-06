"""
Datlas structured logging.

Provides:
- JSON console logging via structlog
- Configurable log level via LOG_LEVEL env var
- Request ID context propagation
- Standard library integration for FastAPI/Uvicorn
"""

import logging
import sys
from contextvars import ContextVar

import structlog

from app.config import settings

# ── Context variable for request IDs ──
request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)


def add_request_id(logger, method_name, event_dict):
    """Inject the current request_id into every log event."""
    rid = request_id_ctx.get()
    if rid:
        event_dict["request_id"] = rid
    return event_dict


def setup_logging() -> structlog.stdlib.BoundLogger:
    """Configure structlog with JSON console output.

    Returns a configured logger ready for use.
    """
    # Reset structlog so it can be reconfigured
    structlog.reset_defaults()

    # Configure standard library logging bridge
    level = getattr(logging, settings.LOG_LEVEL.upper(), logging.INFO)

    # Shared processors: timestamps are ISO 8601 by default in structlog
    shared_processors: list = [
        structlog.contextvars.merge_contextvars,
        add_request_id,
        structlog.processors.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    structlog.configure(
        processors=shared_processors
        + [
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # Attach JSON renderer to the standard library handler
    formatter = structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            structlog.processors.JSONRenderer(),
        ],
    )

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)

    # Silence noisy third-party loggers
    logging.getLogger("uvicorn.access").handlers = []

    root = logging.getLogger()
    root.addHandler(handler)
    root.setLevel(level)

    # Also configure uvicorn to use our handler
    for name in ("uvicorn", "uvicorn.error", "uvicorn.access"):
        logger = logging.getLogger(name)
        logger.handlers = [handler]
        logger.propagate = False

    return structlog.get_logger("datlas")


# ── Module-level logger ──
logger = setup_logging()
