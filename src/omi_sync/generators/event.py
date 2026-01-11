"""Event note generator."""
from datetime import datetime, timezone as tz
from omi_sync.models import Conversation
from omi_sync.config import Config
from omi_sync.frontmatter_writer import write_frontmatter
from omi_sync.timezone_utils import get_local_date, format_time_local, format_datetime_local
from omi_sync.slugify import slugify
from omi_sync.people import extract_people


def get_event_filename(conv: Conversation, config: Config) -> str:
    """
    Generate deterministic event filename.

    PRD: Omi/Events/YYYY-MM-DDTHHMMSS - <slug(title)> - <omi_id>.md
    """
    local_date = get_local_date(conv.finished_at, config.timezone)
    time_str = format_time_local(conv.finished_at, config.timezone).replace(":", "")
    title_slug = slugify(conv.title)

    return f"{local_date}T{time_str}00 - {title_slug} - {conv.id}.md"


def generate_event_note(conv: Conversation, config: Config) -> str:
    """
    Generate event note markdown content.

    PRD: Event note format (Section B).
    """
    local_date = get_local_date(conv.finished_at, config.timezone)
    time_str = format_time_local(conv.started_at, config.timezone)
    raw_heading = f"{time_str} — {conv.title} (omi:{conv.id})"

    # Build frontmatter
    frontmatter = write_frontmatter({
        "category": conv.category or "",
        "date": local_date,
        "duration_minutes": conv.duration_minutes,
        "finished_at": conv.finished_at.isoformat() if conv.finished_at else "",
        "generated_at": format_datetime_local(datetime.now(tz.utc), config.timezone),
        "language": conv.language or "",
        "omi_id": conv.id,
        "omi_sync": True,
        "people": extract_people(conv),
        "raw_daily": f"[[{local_date}]]",
        "raw_link": f"[[{local_date}#{raw_heading}]]",
        "source": conv.source or "",
        "started_at": conv.started_at.isoformat(),
    })

    # Build body
    lines = [
        frontmatter,
        f"# {conv.title}",
        "",
        "## Summary",
        "",
        conv.overview or "*No summary available.*",
        "",
        "## Action Items",
        "",
    ]

    if conv.action_items:
        for item in conv.action_items:
            checkbox = "[x]" if item.completed else "[ ]"
            lines.append(f"- {checkbox} {item.description}")
    else:
        lines.append("*No action items.*")

    lines.extend([
        "",
        "## Link to Raw",
        "",
        f"[[{local_date}#{raw_heading}]]",
        "",
    ])

    return "\n".join(lines)
