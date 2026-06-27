"""Tests for request id middleware."""

import re


def test_response_includes_generated_request_id(client):
    response = client.get("/health")

    assert response.status_code == 200
    request_id = response.headers.get("X-Request-ID")
    assert request_id
    assert re.fullmatch(r"[0-9a-f-]{36}", request_id)


def test_response_reuses_valid_request_id(client):
    response = client.get("/health", headers={"X-Request-ID": "req-local-123"})

    assert response.status_code == 200
    assert response.headers["X-Request-ID"] == "req-local-123"
