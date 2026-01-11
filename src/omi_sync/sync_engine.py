"""Main sync orchestration engine."""
from datetime import datetime, timezone
from typing import Dict, List, Any, Set
from collections import defaultdict
from pathlib import Path

from omi_sync.config import Config
from omi_sync.models import Conversation, parse_conversation
from omi_sync.finalization import is_finalized
from omi_sync.notable import is_notable, load_overrides
from omi_sync.timezone_utils import get_local_date, format_time_local, format_datetime_local
from omi_sync.state import StateManager, IndexEntry
from omi_sync.file_writer import write_file_atomic
from omi_sync.generators.raw import generate_raw_daily
from omi_sync.generators.event import generate_event_note, get_event_filename
from omi_sync.generators.highlights import generate_highlights


class SyncEngine:
    """
    Main sync orchestration.

    PRD: Idempotent sync with deterministic outputs.
    """

    def __init__(self, config: Config):
        self.config = config
        self.state = StateManager(config.vault_path)
        self.overrides = load_overrides(self.state.get_notable_overrides_path())

    def sync(self, api_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run sync with provided API data.

        Returns dict with status and stats.
        """
        # Parse and filter conversations
        conversations = []
        for data in api_data:
            conv = parse_conversation(data)
            if is_finalized(conv, self.config.finalization_lag_minutes):
                conversations.append(conv)

        # Deduplicate by omi_id (keep latest finished_at)
        conv_by_id: Dict[str, Conversation] = {}
        for conv in conversations:
            existing = conv_by_id.get(conv.id)
            if existing is None or (conv.finished_at and existing.finished_at and conv.finished_at > existing.finished_at):
                conv_by_id[conv.id] = conv

        conversations = list(conv_by_id.values())

        # Classify notable
        notable_ids: Set[str] = set()
        for conv in conversations:
            if is_notable(conv, self.config, self.overrides):
                notable_ids.add(conv.id)

        # Group by local date (based on finished_at)
        by_date: Dict[str, List[Conversation]] = defaultdict(list)
        for conv in conversations:
            if conv.finished_at:
                local_date = get_local_date(conv.finished_at, self.config.timezone)
                by_date[local_date].append(conv)

        # Update index entries
        for conv in conversations:
            if not conv.finished_at:
                continue
            local_date = get_local_date(conv.finished_at, self.config.timezone)
            time_str = format_time_local(conv.started_at, self.config.timezone)
            raw_heading = f"{time_str} — {conv.title} (omi:{conv.id})"

            event_path = None
            if conv.id in notable_ids:
                event_path = f"Omi/Events/{get_event_filename(conv, self.config)}"

            entry = IndexEntry(
                omi_id=conv.id,
                raw_date=local_date,
                raw_heading=raw_heading,
                event_path=event_path,
                last_seen_finished_at=conv.finished_at.isoformat(),
            )
            self.state.set_index_entry(conv.id, entry)

        # Generate and write files for each affected date
        stats = {"dates": 0, "raw_files": 0, "event_files": 0, "highlights_files": 0}

        for date, date_convs in by_date.items():
            stats["dates"] += 1

            # Raw daily file
            raw_content = generate_raw_daily(date_convs, date, self.config)
            raw_path = self.config.vault_path / "Omi" / "Raw" / f"{date}.md"
            write_file_atomic(raw_path, raw_content)
            stats["raw_files"] += 1

            # Event notes for notable conversations
            date_notable_ids = {c.id for c in date_convs if c.id in notable_ids}
            for conv in date_convs:
                if conv.id in notable_ids:
                    event_content = generate_event_note(conv, self.config)
                    event_path = self.config.vault_path / "Omi" / "Events" / get_event_filename(conv, self.config)
                    write_file_atomic(event_path, event_content)
                    stats["event_files"] += 1

            # Highlights file
            highlights_content = generate_highlights(date_convs, date, date_notable_ids, self.config)
            highlights_path = self.config.vault_path / "Omi" / "Highlights" / f"{date} Highlights.md"
            write_file_atomic(highlights_path, highlights_content)
            stats["highlights_files"] += 1

        # Save state
        self.state.update_last_run(format_datetime_local(datetime.now(timezone.utc), self.config.timezone))
        self.state.save()

        return {"status": "DONE", "stats": stats}
