"""Tests for config.py SECRET_KEY enforcement."""
import importlib
import os
from unittest.mock import patch

import pytest

import backend.config


# Keep a reference to the original config values so we can restore them.
_DEFAULT_SECRET = backend.config._DEFAULT_SECRET


@pytest.fixture(autouse=True)
def _restore_config():
    """Restore the config module to its original state after each test."""
    yield
    # Reload to undo any monkeypatch-induced state.
    importlib.reload(backend.config)


class TestSecretKeyDevelopment:
    """Development environment SECRET_KEY behavior."""

    def test_development_default_secret_ok(self, monkeypatch):
        """
        Development + default SECRET_KEY → no error, _IS_DEFAULT_SECRET=True.
        This is the typical out-of-the-box experience.
        """
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("SECRET_KEY", _DEFAULT_SECRET)
        importlib.reload(backend.config)

        assert backend.config.APP_ENV == "development"
        assert backend.config.IS_PRODUCTION is False
        assert backend.config._IS_DEFAULT_SECRET is True
        assert backend.config.SECRET_KEY == _DEFAULT_SECRET

    def test_development_custom_secret_ok(self, monkeypatch):
        """Development + custom SECRET_KEY should work fine."""
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.setenv("SECRET_KEY", "dev-custom-key-xyz")
        importlib.reload(backend.config)

        assert backend.config.APP_ENV == "development"
        assert backend.config.IS_PRODUCTION is False
        assert backend.config._IS_DEFAULT_SECRET is False
        assert backend.config.SECRET_KEY == "dev-custom-key-xyz"

    def test_development_missing_secret_uses_default(self, monkeypatch):
        """Development + no SECRET_KEY → uses default, warns, no crash."""
        monkeypatch.setenv("APP_ENV", "development")
        monkeypatch.delenv("SECRET_KEY", raising=False)
        importlib.reload(backend.config)

        assert backend.config.APP_ENV == "development"
        assert backend.config.IS_PRODUCTION is False
        assert backend.config._IS_DEFAULT_SECRET is True
        assert backend.config.SECRET_KEY == _DEFAULT_SECRET


class TestSecretKeyProduction:
    """Production environment SECRET_KEY enforcement."""

    def test_production_default_secret_raises(self, monkeypatch):
        """Production + default SECRET_KEY → RuntimeError at import time."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", _DEFAULT_SECRET)

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            importlib.reload(backend.config)

    def test_production_missing_secret_raises(self, monkeypatch):
        """Production + no SECRET_KEY → RuntimeError at import time."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.delenv("SECRET_KEY", raising=False)

        with pytest.raises(RuntimeError, match="SECRET_KEY"):
            importlib.reload(backend.config)

    def test_production_custom_secret_ok(self, monkeypatch):
        """Production + custom SECRET_KEY → startup OK, no default flag."""
        monkeypatch.setenv("APP_ENV", "production")
        monkeypatch.setenv("SECRET_KEY", "prod-secret-9876543210-abcdef")
        importlib.reload(backend.config)

        assert backend.config.APP_ENV == "production"
        assert backend.config.IS_PRODUCTION is True
        assert backend.config._IS_DEFAULT_SECRET is False
        assert backend.config.SECRET_KEY == "prod-secret-9876543210-abcdef"

    def test_env_fallback_var_works(self, monkeypatch):
        """ENV=production (fallback) should also trigger production mode."""
        monkeypatch.setenv("APP_ENV", "")  # explicitly empty
        monkeypatch.setenv("ENV", "production")
        monkeypatch.setenv("SECRET_KEY", "some-prod-key")

        importlib.reload(backend.config)
        assert backend.config.APP_ENV == "production"
        assert backend.config.IS_PRODUCTION is True
