"""Tests for backend/config.py dotenv loading logic."""
import os
import tempfile
from pathlib import Path

import pytest


def _clean_test_env():
    """Remove all TEST_* keys from os.environ."""
    for k in list(os.environ.keys()):
        if k.startswith("TEST_"):
            os.environ.pop(k, None)


class TestDotenvLoading:
    """Tests for the .env loading behavior in config.py."""

    def setup_method(self):
        _clean_test_env()

    def teardown_method(self):
        _clean_test_env()

    def test_utf8_normal(self):
        """Plain UTF-8 .env should load all variables."""
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("TEST_KEY_A=value_a\nTEST_KEY_B=value_b\n", encoding="utf-8")
            self._apply_env_file(env_file)

            assert os.environ.get("TEST_KEY_A") == "value_a"
            assert os.environ.get("TEST_KEY_B") == "value_b"

    def test_utf8_bom(self):
        """UTF-8 with BOM .env should load all variables (BOM on first line)."""
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("TEST_BOM_A=first_value\nTEST_BOM_B=second_value\n", encoding="utf-8-sig")

            self._apply_env_file(env_file)

            assert os.environ.get("TEST_BOM_A") == "first_value"
            assert os.environ.get("TEST_BOM_B") == "second_value"

    def test_empty_system_env_filled_by_dotenv(self):
        """Empty system env var should be filled by .env value."""
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("TEST_FILL_ME=from_dotenv\n", encoding="utf-8")

            os.environ["TEST_FILL_ME"] = ""
            self._apply_env_file(env_file)
            assert os.environ.get("TEST_FILL_ME") == "from_dotenv"

    def test_nonempty_system_env_not_overridden(self):
        """Non-empty system env var should NOT be overridden by .env."""
        with tempfile.TemporaryDirectory() as tmp:
            env_file = Path(tmp) / ".env"
            env_file.write_text("TEST_NO_OVERRIDE=dotenv_value\n", encoding="utf-8")

            os.environ["TEST_NO_OVERRIDE"] = "system_value"
            self._apply_env_file(env_file)
            assert os.environ.get("TEST_NO_OVERRIDE") == "system_value"

    def test_skip_dotenv_flag(self):
        """Test the _apply_env_values function respects logic (tested via direct call)."""
        values = {"TEST_SKIP": "should_not_load_when_skip_set"}
        # With SKIP_DOTENV set, the module won't call _apply_env_values,
        # but calling it directly should still work. The skip logic is in
        # config.py's module-level if-statement, not inside _apply_env_values.
        # This test validates that _apply_env_values functions correctly.
        os.environ["TEST_SKIP_EXISTING"] = "keep_me"
        values["TEST_SKIP_EXISTING"] = "override_attempt"

        from backend.config import _apply_env_values
        _apply_env_values(values)
        assert os.environ.get("TEST_SKIP_EXISTING") == "keep_me"
        # Clean up
        os.environ.pop("TEST_SKIP_EXISTING", None)

    def test_missing_env_file_does_not_raise(self):
        """Missing .env returns empty dict."""
        from backend.config import _load_dotenv_values
        result = _load_dotenv_values(Path("/nonexistent/.env"))
        assert result == {}

    # ── helpers ──────────────────────────────────────────────────────────

    @staticmethod
    def _apply_env_file(env_path):
        """Simulate config.py's env loading for a specific file."""
        from backend.config import _load_dotenv_values, _apply_env_values
        values = _load_dotenv_values(env_path)
        _apply_env_values(values)
