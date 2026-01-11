"""Tests for configuration loading and validation."""
import pytest
from pathlib import Path
from omi_sync.config import load_config, ConfigError, Config


class TestConfigValidation:
    """PRD: Config tests 1-2."""

    def test_missing_api_key_fails_fast(self, temp_vault, monkeypatch):
        """PRD Test 1: Missing API key fails fast and writes nothing."""
        monkeypatch.delenv("OMI_API_KEY", raising=False)
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        with pytest.raises(ConfigError, match="OMI_API_KEY"):
            load_config()

    def test_missing_vault_path_fails_fast(self, monkeypatch):
        """PRD Test 2: Vault path missing fails fast."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.delenv("OMI_VAULT_PATH", raising=False)

        with pytest.raises(ConfigError, match="OMI_VAULT_PATH"):
            load_config()

    def test_nonexistent_vault_path_fails(self, monkeypatch):
        """Vault path must exist."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", "/nonexistent/path")

        with pytest.raises(ConfigError, match="does not exist"):
            load_config()

    def test_valid_config_loads(self, temp_vault, monkeypatch):
        """Valid config loads successfully."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        config = load_config()

        assert config.api_key == "test-key"
        assert config.vault_path == temp_vault
        assert config.finalization_lag_minutes == 10
        assert config.timezone == "America/New_York"

    def test_custom_config_values(self, temp_vault, monkeypatch):
        """Custom environment values are respected."""
        monkeypatch.setenv("OMI_API_KEY", "custom-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))
        monkeypatch.setenv("OMI_TIMEZONE", "America/Los_Angeles")
        monkeypatch.setenv("OMI_FINALIZATION_LAG_MINUTES", "15")
        monkeypatch.setenv("OMI_NOTABLE_DURATION_MINUTES", "30")

        config = load_config()

        assert config.timezone == "America/Los_Angeles"
        assert config.finalization_lag_minutes == 15
        assert config.notable_duration_minutes == 30
