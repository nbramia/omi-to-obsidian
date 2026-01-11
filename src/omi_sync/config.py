"""Configuration loading and validation."""
from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import List


class ConfigError(Exception):
    """Configuration error."""
    pass


@dataclass
class Config:
    """Sync configuration."""
    api_key: str
    vault_path: Path
    api_base_url: str = "https://api.omi.me/v1/dev"
    finalization_lag_minutes: int = 10
    timezone: str = "America/New_York"
    notable_duration_minutes: int = 25
    notable_action_items_min: int = 2
    notable_keywords: List[str] = field(default_factory=lambda: [
        "therapy", "therapist", "session",
        "1:1", "one-on-one", "standup", "retro", "planning", "interview",
        "doctor", "appointment"
    ])


def load_config() -> Config:
    """Load and validate configuration from environment."""
    api_key = os.environ.get("OMI_API_KEY")
    if not api_key:
        raise ConfigError("OMI_API_KEY environment variable is required")

    vault_path_str = os.environ.get("OMI_VAULT_PATH")
    if not vault_path_str:
        raise ConfigError("OMI_VAULT_PATH environment variable is required")

    vault_path = Path(vault_path_str).expanduser()
    if not vault_path.exists():
        raise ConfigError(f"OMI_VAULT_PATH does not exist: {vault_path}")

    return Config(
        api_key=api_key,
        vault_path=vault_path,
        api_base_url=os.environ.get("OMI_API_BASE_URL", "https://api.omi.me/v1/dev"),
        finalization_lag_minutes=int(os.environ.get("OMI_FINALIZATION_LAG_MINUTES", "10")),
        timezone=os.environ.get("OMI_TIMEZONE", "America/New_York"),
        notable_duration_minutes=int(os.environ.get("OMI_NOTABLE_DURATION_MINUTES", "25")),
        notable_action_items_min=int(os.environ.get("OMI_NOTABLE_ACTION_ITEMS_MIN", "2")),
    )
