"""Tests for state management."""
import pytest
import json
from pathlib import Path
from omi_sync.state import StateManager, IndexEntry


class TestStateManager:
    def test_creates_sync_directory(self, tmp_path):
        """Creates .omi-sync directory if missing."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)

        assert (vault_path / "Omi" / ".omi-sync").exists()

    def test_save_and_load_state(self, tmp_path):
        """State persists across instances."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager1 = StateManager(vault_path)
        manager1.update_cursor("2026-01-10T10:00:00Z")
        manager1.save()

        manager2 = StateManager(vault_path)
        assert manager2.state["last_cursor"] == "2026-01-10T10:00:00Z"

    def test_index_entry_operations(self, tmp_path):
        """Index entries can be added and retrieved."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)
        entry = IndexEntry(
            omi_id="conv_001",
            raw_date="2026-01-10",
            raw_heading="10:00 — Meeting (omi:conv_001)",
            event_path="Omi/Events/2026-01-10T100000 - meeting - conv_001.md",
            last_seen_finished_at="2026-01-10T10:30:00Z",
            last_content_hash="abc123",
        )

        manager.set_index_entry("conv_001", entry)
        manager.save()

        manager2 = StateManager(vault_path)
        retrieved = manager2.get_index_entry("conv_001")

        assert retrieved is not None
        assert retrieved.omi_id == "conv_001"
        assert retrieved.raw_date == "2026-01-10"

    def test_get_all_entries_for_date(self, tmp_path):
        """Can retrieve all entries for a specific date."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)
        manager.set_index_entry("conv_001", IndexEntry(
            omi_id="conv_001",
            raw_date="2026-01-10",
            raw_heading="heading1",
        ))
        manager.set_index_entry("conv_002", IndexEntry(
            omi_id="conv_002",
            raw_date="2026-01-10",
            raw_heading="heading2",
        ))
        manager.set_index_entry("conv_003", IndexEntry(
            omi_id="conv_003",
            raw_date="2026-01-09",
            raw_heading="heading3",
        ))

        entries = manager.get_entries_for_date("2026-01-10")

        assert len(entries) == 2
        assert all(e.raw_date == "2026-01-10" for e in entries)

    def test_creates_overrides_directory(self, tmp_path):
        """Creates overrides directory."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)

        assert (vault_path / "Omi" / ".omi-sync" / "overrides").exists()

    def test_get_notable_overrides_path(self, tmp_path):
        """Returns correct path to notable overrides file."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)
        path = manager.get_notable_overrides_path()

        assert path == vault_path / "Omi" / ".omi-sync" / "overrides" / "notable.json"

    def test_update_last_run(self, tmp_path):
        """Can update last run timestamp."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)
        manager.update_last_run("2026-01-10T22:00:00-05:00")
        manager.save()

        manager2 = StateManager(vault_path)
        assert manager2.state["last_run_at"] == "2026-01-10T22:00:00-05:00"
