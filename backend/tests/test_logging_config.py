"""Tests for structured logging helpers."""

from backend.logging_config import add_request_id
from backend.middleware import request_id_ctx


def test_log_processor_adds_request_id_when_available():
    token = request_id_ctx.set("req-test-1")
    try:
        event = add_request_id(None, "info", {"event": "hello"})
    finally:
        request_id_ctx.reset(token)

    assert event["request_id"] == "req-test-1"


def test_log_processor_leaves_event_unchanged_without_request_id():
    event = add_request_id(None, "info", {"event": "hello"})

    assert event == {"event": "hello"}
