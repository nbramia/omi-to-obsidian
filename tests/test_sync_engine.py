"""Tests for sync engine."""
import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from freezegun import freeze_time
from omi_sync.sync_engine import SyncEngine
from omi_sync.config import Config


@pytest.fixture
def config(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    return Config(api_key="test", vault_path=vault)


@pytest.fixture
def sample_api_response(fixtures_dir):
    with open(fixtures_dir / "conversations_page1.json") as f:
        return json.load(f)


class TestIdempotency:
    """PRD Tests 16-17: Idempotency."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_running_twice_yields_identical_files(self, config, sample_api_response):
        """PRD Test 16: Running twice with same fixtures yields byte-identical files."""
        engine = SyncEngine(config)

        # First run
        engine.sync(sample_api_response)
        first_run_files = {}
        for path in config.vault_path.rglob("*.md"):
            first_run_files[str(path.relative_to(config.vault_path))] = path.read_text()

        # Second run
        engine.sync(sample_api_response)
        second_run_files = {}
        for path in config.vault_path.rglob("*.md"):
            second_run_files[str(path.relative_to(config.vault_path))] = path.read_text()

        # Same files
        assert set(first_run_files.keys()) == set(second_run_files.keys())

        # Identical content
        for path in first_run_files:
            assert first_run_files[path] == second_run_files[path], f"Mismatch in {path}"

    @freeze_time("2026-01-10T22:00:00Z")
    def test_update_changes_files_in_place(self, config):
        """PRD Test 17: Update case changes summary and updates files in place."""
        engine = SyncEngine(config)

        # Initial data
        initial_data = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:20:00Z",
            "language": "en",
            "source": "omi",
            "structured": {
                "title": "Meeting",
                "overview": "Original summary",
                "action_items": [],
            },
            "transcript_segments": [],
        }]

        engine.sync(initial_data)
        raw_file = config.vault_path / "Omi" / "Raw" / "2026-01-10.md"
        assert raw_file.exists()

        # Updated data with new title
        updated_data = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:20:00Z",
            "language": "en",
            "source": "omi",
            "structured": {
                "title": "Updated Meeting Title",
                "overview": "Updated summary",
                "action_items": [],
            },
            "transcript_segments": [],
        }]

        engine.sync(updated_data)
        content = raw_file.read_text()
        assert "Updated Meeting Title" in content


class TestStopToken:
    """PRD Test 18: Ralph stop token."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_successful_run_returns_done(self, config, sample_api_response):
        """PRD Test 18: Successful run returns DONE status."""
        engine = SyncEngine(config)
        result = engine.sync(sample_api_response)

        assert result["status"] == "DONE"


class TestDeduplication:
    """PRD Test 5: No duplicates on update."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_same_omi_id_with_later_finished_at_updates(self, config):
        """PRD Test 5: Same omi_id with later finished_at updates, no duplicates."""
        engine = SyncEngine(config)

        # First version
        data_v1 = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:20:00Z",
            "language": "en",
            "source": "omi",
            "structured": {"title": "Meeting v1", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]
        engine.sync(data_v1)

        # Same ID, later finished_at
        data_v2 = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:25:00Z",
            "language": "en",
            "source": "omi",
            "structured": {"title": "Meeting v2", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]
        engine.sync(data_v2)

        raw_file = config.vault_path / "Omi" / "Raw" / "2026-01-10.md"
        content = raw_file.read_text()

        assert "Meeting v2" in content
        assert content.count("(omi:conv_001)") == 1


class TestFinalizationFiltering:
    """Test that only finalized conversations are synced."""

    @freeze_time("2026-01-10T22:05:00Z")
    def test_recent_conversation_filtered_out(self, config):
        """Conversations within finalization lag are filtered out."""
        engine = SyncEngine(config)

        data = [{
            "id": "conv_recent",
            "started_at": "2026-01-10T21:50:00Z",
            "finished_at": "2026-01-10T22:00:00Z",  # 5 min ago, within lag
            "language": "en",
            "source": "omi",
            "structured": {"title": "Recent", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]

        result = engine.sync(data)

        # No files should be created
        raw_files = list((config.vault_path / "Omi" / "Raw").glob("*.md"))
        assert len(raw_files) == 0


class TestNotableClassification:
    """Test notable conversation classification in sync."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_notable_by_duration_creates_event_file(self, config):
        """Notable conversations create event files."""
        engine = SyncEngine(config)

        data = [{
            "id": "conv_long",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:30:00Z",  # 30 min - notable
            "language": "en",
            "source": "omi",
            "structured": {"title": "Long Meeting", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]

        engine.sync(data)

        event_files = list((config.vault_path / "Omi" / "Events").glob("*.md"))
        assert len(event_files) == 1

    @freeze_time("2026-01-10T22:00:00Z")
    def test_non_notable_no_event_file(self, config):
        """Non-notable conversations don't create event files."""
        engine = SyncEngine(config)

        data = [{
            "id": "conv_short",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:10:00Z",  # 10 min - not notable
            "language": "en",
            "source": "omi",
            "structured": {"title": "Short Chat", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]

        engine.sync(data)

        event_files = list((config.vault_path / "Omi" / "Events").glob("*.md"))
        assert len(event_files) == 0
