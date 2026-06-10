"""
Tests for Datlas structured logging module.
"""

import io
import json
import logging

import structlog
from starlette.testclient import TestClient

from app.logging import add_request_id, request_id_ctx, setup_logging
from app.main import app

client = TestClient(app)


# ── Unit: request_id context ──


def test_request_id_ctx_defaults_to_none():
    """request_id_ctx starts as None."""
    assert request_id_ctx.get() is None


def test_request_id_ctx_set_and_reset():
    """request_id_ctx can be set and cleared."""
    token = request_id_ctx.set("test-id-12345")
    assert request_id_ctx.get() == "test-id-12345"
    request_id_ctx.reset(token)
    assert request_id_ctx.get() is None


def test_add_request_id_injects_when_set():
    """add_request_id adds request_id to event dict when context is set."""
    request_id_ctx.set("ctx-42")
    event = add_request_id(None, None, {"event": "test"})
    assert event["request_id"] == "ctx-42"
    assert event["event"] == "test"
    request_id_ctx.set(None)


def test_add_request_id_noop_when_context_none():
    """add_request_id does not add request_id when context is None."""
    event = add_request_id(None, None, {"event": "test"})
    assert "request_id" not in event


# ── Integration: request ID in response headers ──


def test_request_id_in_response():
    """Every response includes an X-Request-ID header."""
    response = client.get("/health")
    assert response.status_code == 200
    assert "X-Request-ID" in response.headers
    # Should be a valid UUID
    rid = response.headers["X-Request-ID"]
    import uuid

    uuid.UUID(rid)  # does not raise


def test_request_id_forwarded_when_provided():
    """When client sends X-Request-ID, the server echoes it back."""
    response = client.get("/health", headers={"X-Request-ID": "custom-req-999"})
    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "custom-req-999"


# ── Unit: logger creation ──


def test_setup_logging_returns_logger():
    """setup_logging() returns a configured logger."""
    logger = setup_logging()
    assert logger is not None
    assert hasattr(logger, "info")
    assert hasattr(logger, "warning")
    assert hasattr(logger, "error")
    assert hasattr(logger, "debug")


def test_logger_emits_json():
    """Logger output is valid JSON with expected fields."""
    structlog.reset_defaults()
    file = io.StringIO()
    structlog.configure(
        processors=[
            add_request_id,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=file),
        cache_logger_on_first_use=False,
    )
    logger = structlog.get_logger()
    logger.info("hello world", extra_field="value")

    output = file.getvalue().strip()
    setup_logging()

    parsed = json.loads(output)
    assert parsed["event"] == "hello world"
    assert parsed["extra_field"] == "value"
    assert parsed["level"] == "info"
    assert "timestamp" in parsed


# ── Unit: JSON format validation ──


def test_setup_logging_produces_valid_json_output():
    """After setup_logging(), the logger produces valid JSON to stdout."""
    import sys

    structlog.reset_defaults()
    # Redirect stdout to capture log output
    buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = buffer

    try:
        logger = setup_logging()
        logger.info("ping")
        # Force flush
        for h in logging.getLogger().handlers:
            h.flush()
    finally:
        sys.stdout = old_stdout

    output = buffer.getvalue().strip()
    # Should be valid JSON
    parsed = json.loads(output)
    assert parsed["event"] == "ping"
    assert parsed["level"] == "info"
    assert "timestamp" in parsed


# ── Edge case: no crash with unicode ──


def test_logger_handles_unicode():
    """Logger handles unicode characters (UTF-8)."""
    structlog.reset_defaults()
    file = io.StringIO()
    structlog.configure(
        processors=[
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        logger_factory=structlog.PrintLoggerFactory(file=file),
        cache_logger_on_first_use=False,
    )
    logger = structlog.get_logger()
    logger.info("datos 🚀 análisis", mensaje="olá, mundo 🌎")

    output = file.getvalue().strip()
    setup_logging()

    parsed = json.loads(output)
    assert "🚀" in parsed["event"]
    assert "🌎" in parsed["mensaje"]


# ── Edge case: log level filtering ──


def test_module_logger_exists():
    """The module-level logger from app.logging is usable."""
    from app.logging import logger as app_logger

    assert app_logger is not None
    # Just verify it doesn't crash when called
    app_logger.info("module logger test")
