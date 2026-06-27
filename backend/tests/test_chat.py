"""Tests for chat endpoint security hardening.

All upstream AI calls are mocked — no real network requests.
"""

from unittest.mock import MagicMock

import pytest

from backend.main import app
from backend.ratelimit import MemoryRateLimiter, reset_limiter_for_tests

# ── Fixtures ────────────────────────────────────────────────────────────────


class _NoLimitLimiter:
    """A rate limiter that never blocks. Used in tests that don't test rate limiting."""

    def check(self, *, key, limit, window_s=3600):
        pass


@pytest.fixture(autouse=True)
def _override_limiter():
    """Inject a fresh MemoryRateLimiter before each test so state doesn't leak."""
    app.dependency_overrides.clear()
    # Use a fresh in-memory limiter so tests are isolated.
    limiter = MemoryRateLimiter()
    from backend.routers.chat import rate_limiter as rl_dep

    app.dependency_overrides[rl_dep] = lambda: limiter
    yield
    app.dependency_overrides.clear()
    reset_limiter_for_tests()


# ── Helpers ──────────────────────────────────────────────────────────────────


def _mock_openai_response(content: str = "这是 AI 助手的回复。") -> MagicMock:
    """Return a mock OpenAI completion with the given content."""
    choice = MagicMock()
    choice.message.content = content
    completion = MagicMock()
    completion.choices = [choice]
    return completion


def _mock_ai_client(content: str = "这是 AI 助手的回复。"):
    """Return a mock OpenAI client whose completions.create returns the given content."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _mock_openai_response(content)
    return mock_client


# ═══════════════════════════════════════════════════════════════════════════════
# Auth required
# ═══════════════════════════════════════════════════════════════════════════════


class TestChatAuthRequired:
    """Anonymous requests must be rejected."""

    def test_no_token_returns_401(self, client):
        resp = client.post("/chat/", json={"message": "你好"})
        assert resp.status_code == 401

    def test_invalid_token_returns_401(self, client):
        resp = client.post(
            "/chat/",
            json={"message": "你好"},
            headers={"Authorization": "Bearer invalid-token"},
        )
        assert resp.status_code == 401


# ═══════════════════════════════════════════════════════════════════════════════
# Message validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestChatMessageValidation:
    """Input validation for message length and content."""

    def test_empty_message_returns_400(self, client, auth_headers):
        resp = client.post("/chat/", json={"message": "   "}, headers=auth_headers)
        assert resp.status_code == 400
        assert "不能为空" in resp.json()["detail"]

    def test_message_too_long_returns_400(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.CHAT_MAX_MESSAGE_LENGTH", 10)
        resp = client.post(
            "/chat/",
            json={"message": "A" * 11},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "过长" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# History validation
# ═══════════════════════════════════════════════════════════════════════════════


class TestChatHistoryValidation:
    """Validation of history messages."""

    def test_history_role_must_be_user_or_assistant(self, client, auth_headers):
        resp = client.post(
            "/chat/",
            json={
                "message": "hello",
                "history": [{"role": "system", "content": "evil prompt"}],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 422  # Pydantic validation error

    def test_too_many_history_messages_returns_400(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.CHAT_MAX_HISTORY_MESSAGES", 2)
        history = [{"role": "user", "content": f"msg {i}"} for i in range(3)]
        resp = client.post(
            "/chat/",
            json={"message": "hello", "history": history},
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "历史消息过多" in resp.json()["detail"]

    def test_history_total_too_long_returns_400(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.CHAT_MAX_HISTORY_TOTAL_LENGTH", 10)
        resp = client.post(
            "/chat/",
            json={
                "message": "hi",
                "history": [
                    {"role": "user", "content": "A" * 6},
                    {"role": "assistant", "content": "B" * 6},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 400
        assert "总长度超过限制" in resp.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# Rate limiting
# ═══════════════════════════════════════════════════════════════════════════════


class TestChatRateLimit:
    """Per-user rate limiting enforcement."""

    def test_rate_limit_exceeded_returns_429(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.CHAT_RATE_LIMIT_PER_HOUR", 2)
        monkeypatch.setattr("backend.routers.chat.OPENAI_API_KEY", "sk-test")
        # Override rate limit to 2 for the chat key.
        monkeypatch.setattr("backend.routers.chat.OPENAI_MODEL", "gpt-4o-mini")

        # Mock the AI client singleton (must patch the name bound in chat module)
        monkeypatch.setattr(
            "backend.routers.chat.get_chat_client",
            lambda: _mock_ai_client("ok"),
        )

        # First two calls should succeed
        r1 = client.post("/chat/", json={"message": "hello"}, headers=auth_headers)
        assert r1.status_code == 200
        r2 = client.post("/chat/", json={"message": "hello again"}, headers=auth_headers)
        assert r2.status_code == 200

        # Third call should be rate-limited
        r3 = client.post("/chat/", json={"message": "hello once more"}, headers=auth_headers)
        assert r3.status_code == 429
        assert "过于频繁" in r3.json()["detail"]


# ═══════════════════════════════════════════════════════════════════════════════
# Successful call
# ═══════════════════════════════════════════════════════════════════════════════


class TestChatSuccess:
    """Happy-path chat with mocked upstream."""

    def test_successful_chat_returns_reply(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(
            "backend.routers.chat.get_chat_client",
            lambda: _mock_ai_client("这是一条测试回复。"),
        )

        resp = client.post(
            "/chat/",
            json={
                "message": "帮我复习一下线性代数",
                "history": [
                    {"role": "user", "content": "什么是行列式？"},
                    {"role": "assistant", "content": "行列式是一个方阵对应的标量值..."},
                ],
            },
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "reply" in data
        assert data["reply"] == "这是一条测试回复。"

    def test_chat_without_history_succeeds(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.OPENAI_API_KEY", "sk-test")
        monkeypatch.setattr(
            "backend.routers.chat.get_chat_client",
            lambda: _mock_ai_client("好的。"),
        )

        resp = client.post("/chat/", json={"message": "什么是微积分？"}, headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["reply"] == "好的。"


# ═══════════════════════════════════════════════════════════════════════════════
# Upstream error safety
# ═══════════════════════════════════════════════════════════════════════════════


class TestChatUpstreamErrors:
    """Upstream failures must not leak API key or internal details."""

    def test_upstream_error_returns_safe_502(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.OPENAI_API_KEY", "sk-test")

        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("Connection refused by upstream")
        monkeypatch.setattr(
            "backend.routers.chat.get_chat_client",
            lambda: mock_client,
        )

        resp = client.post("/chat/", json={"message": "你好"}, headers=auth_headers)
        assert resp.status_code == 502
        detail = resp.json()["detail"]
        # Must NOT leak the real exception
        assert "暂时不可用" in detail
        assert "Connection refused" not in detail

    def test_missing_api_key_returns_503(self, client, auth_headers, monkeypatch):
        monkeypatch.setattr("backend.routers.chat.OPENAI_API_KEY", "")
        resp = client.post("/chat/", json={"message": "你好"}, headers=auth_headers)
        assert resp.status_code == 503
        assert "未配置" in resp.json()["detail"]
