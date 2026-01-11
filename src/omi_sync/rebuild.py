"""Rebuild index from vault frontmatter."""
import re
import frontmatter
from pathlib import Path
from omi_sync.config import Config
from omi_sync.state import StateManager, IndexEntry


def rebuild_index_from_vault(config: Config) -> int:
    """
    Rebuild index by scanning vault for omi_id frontmatter.

    PRD: omi-sync rebuild-index scans vault to rebuild index from frontmatter.
    """
    state = StateManager(config.vault_path)
    count = 0

    # Scan event notes
    events_dir = config.vault_path / "Omi" / "Events"
    if events_dir.exists():
        for path in events_dir.glob("*.md"):
            try:
                post = frontmatter.load(path)
                omi_id = post.get("omi_id")
                if omi_id:
                    entry = IndexEntry(
                        omi_id=omi_id,
                        raw_date=post.get("date", ""),
                        raw_heading=_extract_heading_from_link(post.get("raw_link", "")),
                        event_path=str(path.relative_to(config.vault_path)),
                    )
                    state.set_index_entry(omi_id, entry)
                    count += 1
            except Exception:
                continue

    # Scan raw files for additional entries
    raw_dir = config.vault_path / "Omi" / "Raw"
    if raw_dir.exists():
        for path in raw_dir.glob("*.md"):
            try:
                content = path.read_text()
                for match in re.finditer(r"## (\d{2}:\d{2}) — (.+?) \(omi:([^)]+)\)", content):
                    time_str, title, omi_id = match.groups()
                    if not state.get_index_entry(omi_id):
                        date = path.stem
                        entry = IndexEntry(
                            omi_id=omi_id,
                            raw_date=date,
                            raw_heading=f"{time_str} — {title} (omi:{omi_id})",
                        )
                        state.set_index_entry(omi_id, entry)
                        count += 1
            except Exception:
                continue

    state.save()
    return count


def _extract_heading_from_link(raw_link: str) -> str:
    """Extract heading from Obsidian link format."""
    match = re.search(r"#(.+?)\]\]", raw_link)
    return match.group(1) if match else ""
