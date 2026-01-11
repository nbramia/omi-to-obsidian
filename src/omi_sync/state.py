"""State and index management."""
import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional


@dataclass
class IndexEntry:
    """Index entry for a conversation."""
    omi_id: str
    raw_date: str
    raw_heading: str
    event_path: Optional[str] = None
    last_seen_finished_at: Optional[str] = None
    last_content_hash: Optional[str] = None


class StateManager:
    """
    Manage sync state and index.

    PRD: Maintain state.json and index.json in Omi/.omi-sync/
    """

    def __init__(self, vault_path: Path):
        self.vault_path = vault_path
        self.sync_dir = vault_path / "Omi" / ".omi-sync"
        self.state_file = self.sync_dir / "state.json"
        self.index_file = self.sync_dir / "index.json"
        self.overrides_dir = self.sync_dir / "overrides"

        # Ensure directories exist
        self.sync_dir.mkdir(parents=True, exist_ok=True)
        self.overrides_dir.mkdir(exist_ok=True)

        # Load existing state
        self.state = self._load_json(self.state_file, {
            "last_cursor": None,
            "last_run_at": None,
        })
        self._index: Dict[str, IndexEntry] = {}
        self._load_index()

    def _load_json(self, path: Path, default: dict) -> dict:
        """Load JSON file or return default."""
        if path.exists():
            try:
                with open(path) as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return default.copy()

    def _load_index(self):
        """Load index from file."""
        data = self._load_json(self.index_file, {})
        for omi_id, entry_data in data.items():
            self._index[omi_id] = IndexEntry(**entry_data)

    def save(self):
        """Save state and index to disk."""
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, sort_keys=True)

        index_data = {k: asdict(v) for k, v in self._index.items()}
        with open(self.index_file, "w") as f:
            json.dump(index_data, f, indent=2, sort_keys=True)

    def update_cursor(self, cursor: str):
        """Update the sync cursor."""
        self.state["last_cursor"] = cursor

    def update_last_run(self, timestamp: str):
        """Update last run timestamp."""
        self.state["last_run_at"] = timestamp

    def get_index_entry(self, omi_id: str) -> Optional[IndexEntry]:
        """Get index entry by omi_id."""
        return self._index.get(omi_id)

    def set_index_entry(self, omi_id: str, entry: IndexEntry):
        """Set index entry."""
        self._index[omi_id] = entry

    def get_entries_for_date(self, date: str) -> List[IndexEntry]:
        """Get all index entries for a specific date."""
        return [e for e in self._index.values() if e.raw_date == date]

    def get_all_entries(self) -> List[IndexEntry]:
        """Get all index entries."""
        return list(self._index.values())

    def get_notable_overrides_path(self) -> Path:
        """Get path to notable overrides file."""
        return self.overrides_dir / "notable.json"
