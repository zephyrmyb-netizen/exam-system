"""Tests for config.py production-safety enforcement.

Covers SECRET_KEY, INVITE_CODE, and CORS_ORIGINS validation in both
development and production modes.
"""
import importlib

import pytest

import backend.config


# Keep a reference to the original config values so we can restore them.
_DEFAULT_SECRET = backend.config._DEFAULT_SECRET

# A valid production config used as a base for tests that need everything to
# pass except the value under test.
_VALID_PROD_ENV = {
    "APP_ENV": "production",
    "SECRET_KEY": "prod-random-secret-abc123",
    "INVITE_CODE": "prod-private-code-xyz",
    "CORS_ORIGINS": "https://example.com",
}


@pytest.fixture(autouse=True)
def _restore_config():
    """Restore the config module to its original state after each test."""
    yield
    importlib.reload(backend.config)


# ── Helpers ─────────────────────────────────────────────────────────────────

def _prod_env(**overrides):
    """Build a production env dict from the valid base, applying overrides."""
    env = dict(_VALID_PROD_ENV)
    env.update(overrides)
    return env


def _set_env(monkeypatch, **kwargs):
    """Clear all config-related env vars then set what's given."""
    for key in ("APP_ENV", "ENV", "SECRET_KEY", "INVITE_CODE", "CORS_ORIGINS"):
        monkeypatch.delenv(key, raising=False)
    for key, val in kwargs.items():
        monkeypatch.setenv(key, val)


def _assert_raises(monkeypatch, match, **overrides):
    """Reload config with a prod env + overrides; assert RuntimeError matching `match`."""
    env = _prod_env(**overrides)
    _set_env(monkeypatch, **env)
    with pytest.raises(RuntimeError, match=match):
        importlib.reload(backend.config)


# ═══════════════════════════════════════════════════════════════════════════════
# Development — everything should work
# ═══════════════════════════════════════════════════════════════════════════════

class TestDevelopment:
    """Development mode: all defaults are accepted, _IS_DEFAULT flags are set."""

    def test_all_defaults_ok(self, monkeypatch):
        """Development with no custom env vars should start cleanly."""
        _set_env(monkeypatch, APP_ENV="development")
        importlib.reload(backend.config)

        assert backend.config.APP_ENV == "development"
        assert backend.config.IS_PRODUCTION is False
        assert backend.config._IS_DEFAULT_SECRET is True
        assert backend.config._IS_DEFAULT_INVITE is True
        assert backend.config.CORS_ORIGINS == ["*"]

    def test_custom_values_ok(self, monkeypatch):
        """Development with custom values should work fine."""
        _set_env(
            monkeypatch,
            APP_ENV="development",
            SECRET_KEY="dev-key",
            INVITE_CODE="dev-code",
            CORS_ORIGINS="http://localhost:5173",
        )
        importlib.reload(backend.config)

        assert backend.config.IS_PRODUCTION is False
        assert backend.config._IS_DEFAULT_SECRET is False
        assert backend.config._IS_DEFAULT_INVITE is False
        assert backend.config.SECRET_KEY == "dev-key"
        assert backend.config.INVITE_CODE == "dev-code"


# ═══════════════════════════════════════════════════════════════════════════════
# Production — SECRET_KEY
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductionSecretKey:
    """Production SECRET_KEY enforcement."""

    def test_default_secret_raises(self, monkeypatch):
        _assert_raises(monkeypatch, match="SECRET_KEY", SECRET_KEY=_DEFAULT_SECRET)

    def test_empty_secret_raises(self, monkeypatch):
        _assert_raises(monkeypatch, match="SECRET_KEY", SECRET_KEY="")

    def test_unset_secret_raises(self, monkeypatch):
        env = _prod_env()
        del env["SECRET_KEY"]
        _set_env(monkeypatch, **env)
        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            importlib.reload(backend.config)


# ═══════════════════════════════════════════════════════════════════════════════
# Production — INVITE_CODE
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductionInviteCode:
    """Production INVITE_CODE enforcement."""

    def test_default_invite_code_raises(self, monkeypatch):
        _assert_raises(monkeypatch, match="INVITE_CODE", INVITE_CODE="dev-invite")

    def test_empty_invite_code_raises(self, monkeypatch):
        _assert_raises(monkeypatch, match="INVITE_CODE", INVITE_CODE="")

    def test_unset_invite_code_raises(self, monkeypatch):
        env = _prod_env()
        del env["INVITE_CODE"]
        _set_env(monkeypatch, **env)
        with pytest.raises(RuntimeError, match="INVITE_CODE"):
            importlib.reload(backend.config)

    def test_custom_invite_code_ok(self, monkeypatch):
        env = _prod_env(INVITE_CODE="my-private-code")
        _set_env(monkeypatch, **env)
        importlib.reload(backend.config)

        assert backend.config._IS_DEFAULT_INVITE is False
        assert backend.config.INVITE_CODE == "my-private-code"


# ═══════════════════════════════════════════════════════════════════════════════
# Production — CORS_ORIGINS
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductionCORS:
    """Production CORS_ORIGINS enforcement."""

    def test_empty_cors_raises(self, monkeypatch):
        _assert_raises(monkeypatch, match="CORS_ORIGINS is empty", CORS_ORIGINS="")

    def test_unset_cors_raises(self, monkeypatch):
        env = _prod_env()
        del env["CORS_ORIGINS"]
        _set_env(monkeypatch, **env)
        with pytest.raises(RuntimeError, match="CORS_ORIGINS is empty"):
            importlib.reload(backend.config)

    def test_wildcard_cors_raises(self, monkeypatch):
        _assert_raises(monkeypatch, match="CORS_ORIGINS is set to '*'", CORS_ORIGINS="*")

    def test_localhost_cors_raises(self, monkeypatch):
        _assert_raises(
            monkeypatch, match="contains localhost", CORS_ORIGINS="http://localhost:5173"
        )

    def test_loopback_ip_cors_raises(self, monkeypatch):
        _assert_raises(
            monkeypatch,
            match="contains localhost or 127.0.0.1",
            CORS_ORIGINS="http://127.0.0.1:5173",
        )

    def test_real_domain_cors_ok(self, monkeypatch):
        env = _prod_env(CORS_ORIGINS="https://exam.example.com")
        _set_env(monkeypatch, **env)
        importlib.reload(backend.config)
        assert backend.config.CORS_ORIGINS == ["https://exam.example.com"]

    def test_multiple_real_domains_ok(self, monkeypatch):
        env = _prod_env(CORS_ORIGINS="https://a.example.com,https://b.example.com")
        _set_env(monkeypatch, **env)
        importlib.reload(backend.config)
        assert backend.config.CORS_ORIGINS == [
            "https://a.example.com",
            "https://b.example.com",
        ]

    def test_localhost_among_real_domains_raises(self, monkeypatch):
        _assert_raises(
            monkeypatch,
            match="contains localhost",
            CORS_ORIGINS="https://example.com,http://localhost:5173",
        )


# ═══════════════════════════════════════════════════════════════════════════════
# Production — all good
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductionAllGood:
    """Full production config with all values valid."""

    def test_all_valid_production_ok(self, monkeypatch):
        _set_env(monkeypatch, **_VALID_PROD_ENV)
        importlib.reload(backend.config)

        assert backend.config.IS_PRODUCTION is True
        assert backend.config._IS_DEFAULT_SECRET is False
        assert backend.config._IS_DEFAULT_INVITE is False
        assert backend.config.SECRET_KEY == "prod-random-secret-abc123"
        assert backend.config.INVITE_CODE == "prod-private-code-xyz"
        assert backend.config.CORS_ORIGINS == ["https://example.com"]


# ═══════════════════════════════════════════════════════════════════════════════
# Multiple errors collected
# ═══════════════════════════════════════════════════════════════════════════════

class TestProductionMultipleErrors:
    """When multiple values are wrong, all errors are reported at once."""

    def test_multiple_errors_reported(self, monkeypatch):
        """All three bad at once → error lists all three issues."""
        _set_env(
            monkeypatch,
            APP_ENV="production",
            SECRET_KEY=_DEFAULT_SECRET,
            INVITE_CODE="dev-invite",
            CORS_ORIGINS="*",
        )
        with pytest.raises(RuntimeError) as exc_info:
            importlib.reload(backend.config)

        msg = str(exc_info.value)
        assert "SECRET_KEY" in msg
        assert "INVITE_CODE" in msg
        assert "CORS_ORIGINS" in msg


# ═══════════════════════════════════════════════════════════════════════════════
# ENV fallback
# ═══════════════════════════════════════════════════════════════════════════════

class TestEnvFallback:
    """ENV=production is accepted as a fallback for APP_ENV."""

    def test_env_fallback_triggers_production(self, monkeypatch):
        _set_env(
            monkeypatch,
            APP_ENV="",
            ENV="production",
            SECRET_KEY=_VALID_PROD_ENV["SECRET_KEY"],
            INVITE_CODE=_VALID_PROD_ENV["INVITE_CODE"],
            CORS_ORIGINS=_VALID_PROD_ENV["CORS_ORIGINS"],
        )
        importlib.reload(backend.config)

        assert backend.config.APP_ENV == "production"
        assert backend.config.IS_PRODUCTION is True
