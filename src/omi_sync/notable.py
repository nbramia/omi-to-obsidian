"""Notable conversation classification."""
import json
from pathlib import Path
from typing import Dict, Optional
from omi_sync.models import Conversation
from omi_sync.config import Config


def load_overrides(path: Path) -> Dict[str, bool]:
    """Load notable overrides from JSON file."""
    if not path.exists():
        return {}
    try:
        with open(path) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return {}


def is_notable(
    conv: Conversation,
    config: Config,
    overrides: Optional[Dict[str, bool]] = None,
) -> bool:
    """
    Determine if a conversation is notable.

    PRD rules (ordered):
    1. Duration >= NOTABLE_DURATION_MINUTES
    2. Action items count >= NOTABLE_ACTION_ITEMS_MIN
    3. Keyword match in title or overview
    4. Manual overrides (applied last)
    """
    # Check override first (applied last means it takes precedence)
    if overrides and conv.id in overrides:
        return overrides[conv.id]

    # Rule 1: Duration
    if conv.duration_minutes >= config.notable_duration_minutes:
        return True

    # Rule 2: Action items count
    if len(conv.action_items) >= config.notable_action_items_min:
        return True

    # Rule 3: Keyword match (case-insensitive)
    text_to_search = f"{conv.title} {conv.overview}".lower()
    for keyword in config.notable_keywords:
        if keyword.lower() in text_to_search:
            return True

    return False
