"""Tests for CLI commands."""
import pytest
from click.testing import CliRunner
from omi_sync.cli import main


class TestDoctorCommand:
    def test_doctor_fails_without_api_key(self, temp_vault, monkeypatch):
        """Doctor fails fast without API key."""
        monkeypatch.delenv("OMI_API_KEY", raising=False)
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])

        assert result.exit_code != 0
        assert "OMI_API_KEY" in result.output

    def test_doctor_passes_with_valid_config(self, temp_vault, monkeypatch):
        """Doctor passes with valid config."""
        monkeypatch.setenv("OMI_API_KEY", "test-key-1234")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])

        assert result.exit_code == 0
        assert "Configuration OK" in result.output


class TestRunCommand:
    def test_run_outputs_done(self, temp_vault, monkeypatch, httpx_mock):
        """Run command outputs DONE on success."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        httpx_mock.add_response(json=[])

        runner = CliRunner()
        result = runner.invoke(main, ["run"])

        assert result.exit_code == 0
        assert "DONE" in result.output

    def test_run_fails_without_config(self, monkeypatch):
        """Run fails without proper config."""
        monkeypatch.delenv("OMI_API_KEY", raising=False)
        monkeypatch.delenv("OMI_VAULT_PATH", raising=False)

        runner = CliRunner()
        result = runner.invoke(main, ["run"])

        assert result.exit_code != 0


class TestRebuildIndexCommand:
    def test_rebuild_index_runs(self, temp_vault, monkeypatch):
        """Rebuild index command runs successfully."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        runner = CliRunner()
        result = runner.invoke(main, ["rebuild-index"])

        assert result.exit_code == 0
        assert "Rebuilt index with" in result.output
