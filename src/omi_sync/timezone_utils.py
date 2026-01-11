"""Timezone utilities for date grouping."""
from datetime import datetime
import pytz


def get_local_date(dt: datetime, timezone_name: str) -> str:
    """
    Convert datetime to local date string (YYYY-MM-DD).

    PRD: Group by finished_at in TIMEZONE.
    """
    tz = pytz.timezone(timezone_name)

    # Ensure datetime is timezone-aware
    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    local_dt = dt.astimezone(tz)
    return local_dt.strftime("%Y-%m-%d")


def format_time_local(dt: datetime, timezone_name: str) -> str:
    """Format datetime as HH:MM in local timezone."""
    tz = pytz.timezone(timezone_name)

    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    local_dt = dt.astimezone(tz)
    return local_dt.strftime("%H:%M")


def format_datetime_local(dt: datetime, timezone_name: str) -> str:
    """Format datetime as ISO8601 in local timezone."""
    tz = pytz.timezone(timezone_name)

    if dt.tzinfo is None:
        dt = pytz.utc.localize(dt)

    local_dt = dt.astimezone(tz)
    return local_dt.isoformat()
