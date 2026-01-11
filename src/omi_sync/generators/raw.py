"""Raw daily file generator."""
from datetime import datetime, timezone as tz
from typing import List
from omi_sync.models import Conversation
from omi_sync.config import Config
from omi_sync.frontmatter_writer import write_frontmatter
from omi_sync.timezone_utils import format_time_local, format_datetime_local
from omi_sync.people import extract_people


def generate_raw_daily(
    conversations: List[Conversation],
    date: str,
    config: Config,
) -> str:
    """
    Generate raw daily markdown file content.

    PRD: Daily Raw file format (Section A).
    """
    # Sort by started_at ascending
    sorted_convs = sorted(conversations, key=lambda c: c.started_at)

    # Extract all people from all conversations
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

    # Build body
    lines = [
        frontmatter,
        f"# Omi Raw — {date}",
        "",
    ]

    for conv in sorted_convs:
        time_str = format_time_local(conv.started_at, config.timezone)
        heading = f"## {time_str} — {conv.title} (omi:{conv.id})"
        lines.append(heading)
        lines.append("")

        # Metadata bullets
        lines.append(f"- **Started**: {conv.started_at.isoformat()}")
        if conv.finished_at:
            lines.append(f"- **Finished**: {conv.finished_at.isoformat()}")
        lines.append(f"- **Duration**: {conv.duration_minutes} minutes")
        if conv.category:
            lines.append(f"- **Category**: {conv.category}")
        if conv.language:
            lines.append(f"- **Language**: {conv.language}")
        if conv.source:
            lines.append(f"- **Source**: {conv.source}")
        if conv.geolocation and conv.geolocation.address:
            lines.append(f"- **Location**: {conv.geolocation.address}")
        lines.append("")

        # Transcript in details block
        if conv.transcript_segments:
            lines.append("<details>")
            lines.append("<summary>Transcript</summary>")
            lines.append("")
            for seg in conv.transcript_segments:
                lines.append(f"- **{seg.speaker}**: {seg.text}")
            lines.append("")
            lines.append("</details>")
            lines.append("")

    return "\n".join(lines)
