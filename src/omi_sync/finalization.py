"""Finalization logic for avoiding mid-conversation partials."""
from datetime import datetime, timezone, timedelta
from omi_sync.models import Conversation


def is_finalized(conv: Conversation, lag_minutes: int = 10) -> bool:
    """
    Check if a conversation is finalized and eligible for sync.

    PRD: Only sync finalized conversations where:
    - finished_at is present
    - finished_at <= now - FINALIZATION_LAG_MINUTES
    """
    if conv.finished_at is None:
        return False

    now = datetime.now(timezone.utc)
    cutoff = now - timedelta(minutes=lag_minutes)

    # Ensure finished_at is timezone-aware
    finished = conv.finished_at
    if finished.tzinfo is None:
        finished = finished.replace(tzinfo=timezone.utc)

    return finished <= cutoff
