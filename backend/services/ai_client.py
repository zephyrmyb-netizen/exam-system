"""Singleton OpenAI clients.

Both chat and import paths used to instantiate ``OpenAI(...)`` on every
request, which rebuilt the underlying httpx connection pool each time and
prevented keep-alive reuse. This module keeps lazily-built module-level
clients keyed by their relevant timeout (chat vs import), and exposes
``rebuild_clients()`` so that config changes can refresh them in tests.

The clients read their credentials from ``config`` at build time; if the
environment config is changed at runtime, call ``rebuild_clients()`` to
pick up the new values.
"""
from __future__ import annotations

import threading

from openai import OpenAI

from ..config import (
    CHAT_UPSTREAM_TIMEOUT,
    IMPORT_UPSTREAM_TIMEOUT,
    OPENAI_API_KEY,
    OPENAI_BASE_URL,
)

_lock = threading.Lock()
_chat_client: OpenAI | None = None
_import_client: OpenAI | None = None


def get_chat_client() -> OpenAI:
    """Return the shared chat client, building it on first use."""
    global _chat_client
    if _chat_client is None:
        with _lock:
            if _chat_client is None:
                _chat_client = OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    timeout=CHAT_UPSTREAM_TIMEOUT,
                )
    return _chat_client


def get_import_client() -> OpenAI:
    """Return the shared import client, building it on first use."""
    global _import_client
    if _import_client is None:
        with _lock:
            if _import_client is None:
                _import_client = OpenAI(
                    api_key=OPENAI_API_KEY,
                    base_url=OPENAI_BASE_URL,
                    timeout=IMPORT_UPSTREAM_TIMEOUT,
                )
    return _import_client


def rebuild_clients() -> None:
    """Discard cached clients so the next call rebuilds them from current config.

    Used when AI settings (key/base_url/timeout) change at runtime, e.g. in
    tests or after a config reload.
    """
    global _chat_client, _import_client
    with _lock:
        _chat_client = None
        _import_client = None
