"""Highlights daily file generator."""
from datetime import datetime, timezone as tz
from typing import List, Set
from omi_sync.models import Conversation
from omi_sync.config import Config
from omi_sync.frontmatter_writer import write_frontmatter
from omi_sync.timezone_utils import format_time_local, format_datetime_local
from omi_sync.generators.event import get_event_filename
from omi_sync.people import extract_people


def generate_highlights(
    conversations: List[Conversation],
    date: str,
    notable_ids: Set[str],
    config: Config,
) -> str:
    """
    Generate highlights daily markdown file content.

    PRD: Daily Highlights format (Section C).
    """
    # Sort by started_at ascending
    sorted_convs = sorted(conversations, key=lambda c: c.started_at)

    # Extract all people
    all_people = set()
    for conv in sorted_convs:
        all_people.update(extract_people(conv))

    # Build frontmatter
    frontmatter = write_frontmatter({
        "date": date,
        "generated_at": format_datetime_local(datetime.now(tz.utc), config.timezone),
        "omi_sync": True,
        "people": sorted(all_people),
        "source": "omi",
        "timezone": config.timezone,
    })

    lines = [
        frontmatter,
        f"# Omi Highlights — {date}",
        "",
        "## Notable Events",
        "",
    ]

    # Notable events section
    notable_convs = [c for c in sorted_convs if c.id in notable_ids]
    if notable_convs:
        for conv in notable_convs:
            time_str = format_time_local(conv.started_at, config.timezone)
            event_filename = get_event_filename(conv, config).replace(".md", "")
            lines.append(f"- {time_str} — [[{event_filename}]]")
    else:
        lines.append("*No notable events.*")

    lines.extend([
        "",
        "## All Conversations",
        "",
    ])

    # All conversations section
    for conv in sorted_convs:
        time_str = format_time_local(conv.started_at, config.timezone)
        line = f"- {time_str} — {conv.title} → [[{date}]]"

        if conv.id in notable_ids:
            event_filename = get_event_filename(conv, config).replace(".md", "")
            line += f" | [[{event_filename}]]"

        lines.append(line)

    lines.append("")

    return "\n".join(lines)
