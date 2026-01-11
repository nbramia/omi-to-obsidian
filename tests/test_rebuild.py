"""Tests for rebuild index functionality."""
import pytest
from pathlib import Path
from omi_sync.rebuild import rebuild_index_from_vault
from omi_sync.config import Config
from omi_sync.state import StateManager


class TestRebuildIndex:
    def test_rebuilds_from_event_frontmatter(self, tmp_path):
        """Rebuilds index from event note frontmatter."""
        vault = tmp_path / "vault"
        vault.mkdir()

        events_dir = vault / "Omi" / "Events"
        events_dir.mkdir(parents=True)

        event_note = events_dir / "2026-01-10T100000 - meeting - conv_001.md"
        event_note.write_text("""---
omi_id: conv_001
date: '2026-01-10'
raw_link: '[[2026-01-10#10:00 — Meeting (omi:conv_001)]]'
---

# Meeting
""")

        config = Config(api_key="test", vault_path=vault)
        count = rebuild_index_from_vault(config)

        assert count == 1

        state = StateManager(vault)
        entry = state.get_index_entry("conv_001")
        assert entry is not None
        assert entry.raw_date == "2026-01-10"

    def test_rebuilds_from_raw_headings(self, tmp_path):
        """Rebuilds index from raw file headings."""
        vault = tmp_path / "vault"
        vault.mkdir()

        raw_dir = vault / "Omi" / "Raw"
        raw_dir.mkdir(parents=True)

        raw_note = raw_dir / "2026-01-10.md"
        raw_note.write_text("""---
date: '2026-01-10'
---

# Omi Raw — 2026-01-10

## 10:00 — Meeting (omi:conv_001)

Some content

## 11:00 — Another Meeting (omi:conv_002)

More content
""")

        config = Config(api_key="test", vault_path=vault)
        count = rebuild_index_from_vault(config)

        assert count == 2

    def test_handles_no_files(self, tmp_path):
        """Handles empty vault gracefully."""
        vault = tmp_path / "vault"
        vault.mkdir()

        config = Config(api_key="test", vault_path=vault)
        count = rebuild_index_from_vault(config)

        assert count == 0
