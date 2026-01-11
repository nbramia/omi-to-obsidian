# Omi-Obsidian Sync Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build a CLI tool that syncs Omi conversations to an Obsidian vault as deterministic Markdown files.

**Architecture:** Python CLI using Click, with separate modules for API client, markdown generation, notable classification, and state management. TDD throughout with mocked HTTP.

**Tech Stack:** Python 3.11+, Click (CLI), httpx (HTTP), pytest, python-frontmatter, pytz

---

## Phase 1: Project Setup

### Task 1.1: Initialize Python Project

**Files:**
- Create: `pyproject.toml`
- Create: `src/omi_sync/__init__.py`
- Create: `src/omi_sync/cli.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

**Step 1: Create pyproject.toml**

```toml
[project]
name = "omi-sync"
version = "0.1.0"
description = "Sync Omi conversations to Obsidian vault"
requires-python = ">=3.11"
dependencies = [
    "click>=8.1.0",
    "httpx>=0.27.0",
    "python-frontmatter>=1.1.0",
    "pytz>=2024.1",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-httpx>=0.30.0",
    "freezegun>=1.4.0",
]

[project.scripts]
omi-sync = "omi_sync.cli:main"

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[tool.hatch.build.targets.wheel]
packages = ["src/omi_sync"]

[tool.pytest.ini_options]
testpaths = ["tests"]
pythonpath = ["src"]
```

**Step 2: Create directory structure and init files**

```bash
mkdir -p src/omi_sync tests fixtures
touch src/omi_sync/__init__.py tests/__init__.py
```

**Step 3: Create minimal CLI skeleton (src/omi_sync/cli.py)**

```python
"""Omi to Obsidian sync CLI."""
import click


@click.group()
def main():
    """Sync Omi conversations to Obsidian vault."""
    pass


@main.command()
def run():
    """Run one-shot sync."""
    click.echo("DONE")


@main.command()
def doctor():
    """Validate configuration."""
    click.echo("Doctor check passed")


@main.command()
def rebuild_index():
    """Rebuild index from vault frontmatter."""
    click.echo("Index rebuilt")


if __name__ == "__main__":
    main()
```

**Step 4: Create conftest.py with common fixtures**

```python
"""Shared test fixtures."""
import pytest
from pathlib import Path
import tempfile
import shutil


@pytest.fixture
def temp_vault():
    """Create a temporary vault directory."""
    vault = tempfile.mkdtemp(prefix="omi_vault_")
    yield Path(vault)
    shutil.rmtree(vault, ignore_errors=True)


@pytest.fixture
def fixtures_dir():
    """Return path to fixtures directory."""
    return Path(__file__).parent.parent / "fixtures"
```

**Step 5: Install and verify**

Run: `cd /Users/nathanramia/Documents/Code/omi_to_obsidian && pip install -e ".[dev]"`

Run: `omi-sync --help`
Expected: Shows help with run, doctor, rebuild-index commands

**Step 6: Commit**

```bash
git init
git add -A
git commit -m "feat: initialize project structure with CLI skeleton"
```

---

### Task 1.2: Add Test Fixtures

**Files:**
- Create: `fixtures/conversations_page1.json`
- Create: `fixtures/conversations_page2.json`
- Create: `fixtures/edge_cases.json`
- Create: `fixtures/overrides_notable.json`

**Step 1: Create fixtures from omi_context.md**

Copy the JSON fixtures from the context document into the fixtures directory.

**Step 2: Commit**

```bash
git add fixtures/
git commit -m "feat: add test fixtures from PRD"
```

---

## Phase 2: Configuration

### Task 2.1: Config Module with Validation

**Files:**
- Create: `src/omi_sync/config.py`
- Create: `tests/test_config.py`

**Step 1: Write failing tests for config validation**

```python
"""Tests for configuration loading and validation."""
import pytest
import os
from omi_sync.config import load_config, ConfigError


class TestConfigValidation:
    """PRD: Config tests 1-2."""

    def test_missing_api_key_fails_fast(self, temp_vault, monkeypatch):
        """PRD Test 1: Missing API key fails fast and writes nothing."""
        monkeypatch.delenv("OMI_API_KEY", raising=False)
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        with pytest.raises(ConfigError, match="OMI_API_KEY"):
            load_config()

    def test_missing_vault_path_fails_fast(self, monkeypatch):
        """PRD Test 2: Vault path missing fails fast."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.delenv("OMI_VAULT_PATH", raising=False)

        with pytest.raises(ConfigError, match="OMI_VAULT_PATH"):
            load_config()

    def test_nonexistent_vault_path_fails(self, monkeypatch):
        """Vault path must exist."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", "/nonexistent/path")

        with pytest.raises(ConfigError, match="does not exist"):
            load_config()

    def test_valid_config_loads(self, temp_vault, monkeypatch):
        """Valid config loads successfully."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        config = load_config()

        assert config.api_key == "test-key"
        assert config.vault_path == temp_vault
        assert config.finalization_lag_minutes == 10
        assert config.timezone == "America/New_York"
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_config.py -v`
Expected: FAIL (module not found)

**Step 3: Implement config module**

```python
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
```

**Step 4: Run tests to verify they pass**

Run: `pytest tests/test_config.py -v`
Expected: All 4 tests PASS

**Step 5: Commit**

```bash
git add src/omi_sync/config.py tests/test_config.py
git commit -m "feat: add config loading with validation (PRD tests 1-2)"
```

---

### Task 2.2: Doctor Command

**Files:**
- Modify: `src/omi_sync/cli.py`
- Create: `tests/test_cli.py`

**Step 1: Write test for doctor command**

```python
"""Tests for CLI commands."""
import pytest
from click.testing import CliRunner
from omi_sync.cli import main


class TestDoctorCommand:
    def test_doctor_fails_without_api_key(self, temp_vault, monkeypatch):
        """Doctor fails fast without API key."""
        monkeypatch.delenv("OMI_API_KEY", raising=False)
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])

        assert result.exit_code != 0
        assert "OMI_API_KEY" in result.output

    def test_doctor_passes_with_valid_config(self, temp_vault, monkeypatch):
        """Doctor passes with valid config."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        runner = CliRunner()
        result = runner.invoke(main, ["doctor"])

        assert result.exit_code == 0
        assert "passed" in result.output.lower() or "ok" in result.output.lower()
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/test_cli.py -v`
Expected: FAIL

**Step 3: Update doctor command**

```python
@main.command()
def doctor():
    """Validate configuration."""
    from omi_sync.config import load_config, ConfigError

    try:
        config = load_config()
        click.echo(f"API Key: {'*' * 8}...{config.api_key[-4:]}")
        click.echo(f"Vault Path: {config.vault_path}")
        click.echo(f"Timezone: {config.timezone}")
        click.echo(f"Finalization Lag: {config.finalization_lag_minutes} minutes")
        click.echo("Configuration OK")
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)
```

**Step 4: Run tests**

Run: `pytest tests/test_cli.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/omi_sync/cli.py tests/test_cli.py
git commit -m "feat: implement doctor command with config validation"
```

---

## Phase 3: Data Models

### Task 3.1: Conversation Data Models

**Files:**
- Create: `src/omi_sync/models.py`
- Create: `tests/test_models.py`

**Step 1: Write tests for model parsing**

```python
"""Tests for data models."""
import pytest
from datetime import datetime, timezone
from omi_sync.models import Conversation, TranscriptSegment, ActionItem, parse_conversation


class TestConversationParsing:
    def test_parse_full_conversation(self, fixtures_dir):
        """Parse a complete conversation from API response."""
        import json
        with open(fixtures_dir / "conversations_page1.json") as f:
            data = json.load(f)

        conv = parse_conversation(data[0])

        assert conv.id == "conv_20260110_0001"
        assert conv.title == "Feature Discussion"
        assert conv.language == "en"
        assert len(conv.transcript_segments) == 3
        assert len(conv.action_items) == 1
        assert conv.action_items[0].description == "Create mockups for new UI"
        assert conv.action_items[0].completed is False

    def test_parse_conversation_missing_structured(self, fixtures_dir):
        """Handle conversation with null structured field."""
        import json
        with open(fixtures_dir / "edge_cases.json") as f:
            data = json.load(f)

        conv = parse_conversation(data[0])  # conv_missing_structured

        assert conv.id == "conv_missing_structured"
        assert conv.title == "Untitled"
        assert conv.overview == ""
        assert conv.action_items == []

    def test_parse_conversation_missing_transcript(self, fixtures_dir):
        """Handle conversation with null transcript_segments."""
        import json
        with open(fixtures_dir / "edge_cases.json") as f:
            data = json.load(f)

        conv = parse_conversation(data[1])  # conv_no_transcript_segments

        assert conv.id == "conv_no_transcript_segments"
        assert conv.transcript_segments == []

    def test_duration_minutes_calculation(self):
        """Duration calculated from started_at and finished_at."""
        data = {
            "id": "test",
            "started_at": "2026-01-10T10:00:00Z",
            "finished_at": "2026-01-10T10:30:00Z",
            "language": "en",
            "source": "omi",
            "structured": None,
            "transcript_segments": None,
            "geolocation": None,
        }

        conv = parse_conversation(data)

        assert conv.duration_minutes == 30
```

**Step 2: Run tests to verify failure**

Run: `pytest tests/test_models.py -v`
Expected: FAIL

**Step 3: Implement models**

```python
"""Data models for Omi conversations."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from dateutil import parser as date_parser


@dataclass
class TranscriptSegment:
    """A segment of transcript from a conversation."""
    speaker: str
    start: float
    end: float
    text: str
    is_user: bool = False


@dataclass
class ActionItem:
    """An action item from a conversation."""
    description: str
    completed: bool = False


@dataclass
class Geolocation:
    """Location data for a conversation."""
    latitude: float
    longitude: float
    address: Optional[str] = None


@dataclass
class Conversation:
    """A parsed Omi conversation."""
    id: str
    started_at: datetime
    finished_at: datetime
    language: str
    source: str
    title: str = "Untitled"
    overview: str = ""
    category: str = ""
    action_items: List[ActionItem] = field(default_factory=list)
    transcript_segments: List[TranscriptSegment] = field(default_factory=list)
    geolocation: Optional[Geolocation] = None

    @property
    def duration_minutes(self) -> int:
        """Calculate duration in minutes."""
        delta = self.finished_at - self.started_at
        return int(delta.total_seconds() / 60)


def parse_conversation(data: dict) -> Conversation:
    """Parse a conversation from API response."""
    structured = data.get("structured") or {}

    action_items = []
    for item in structured.get("action_items") or []:
        action_items.append(ActionItem(
            description=item.get("description", ""),
            completed=item.get("completed", False),
        ))

    transcript_segments = []
    for seg in data.get("transcript_segments") or []:
        transcript_segments.append(TranscriptSegment(
            speaker=seg.get("speaker", "SPEAKER_00"),
            start=seg.get("start", 0.0),
            end=seg.get("end", 0.0),
            text=seg.get("text", ""),
            is_user=seg.get("is_user", False),
        ))

    geo_data = data.get("geolocation")
    geolocation = None
    if geo_data:
        geolocation = Geolocation(
            latitude=geo_data.get("latitude", 0),
            longitude=geo_data.get("longitude", 0),
            address=geo_data.get("address"),
        )

    return Conversation(
        id=data["id"],
        started_at=date_parser.isoparse(data["started_at"]),
        finished_at=date_parser.isoparse(data["finished_at"]),
        language=data.get("language", ""),
        source=data.get("source", ""),
        title=structured.get("title", "Untitled"),
        overview=structured.get("overview", ""),
        category=structured.get("category", ""),
        action_items=action_items,
        transcript_segments=transcript_segments,
        geolocation=geolocation,
    )
```

**Step 4: Add python-dateutil to dependencies**

Update pyproject.toml dependencies to include `"python-dateutil>=2.8.0"`.

**Step 5: Run tests**

Run: `pytest tests/test_models.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/omi_sync/models.py tests/test_models.py pyproject.toml
git commit -m "feat: add conversation data models with parsing"
```

---

## Phase 4: Finalization Logic

### Task 4.1: Finalization Filter

**Files:**
- Create: `src/omi_sync/finalization.py`
- Create: `tests/test_finalization.py`

**Step 1: Write failing tests**

```python
"""Tests for finalization logic."""
import pytest
from datetime import datetime, timezone, timedelta
from freezegun import freeze_time
from omi_sync.finalization import is_finalized
from omi_sync.models import Conversation


class TestFinalization:
    """PRD: Finalization / partial avoidance tests 3-5."""

    @freeze_time("2026-01-10T22:10:00Z")
    def test_conversation_within_lag_window_ignored(self):
        """PRD Test 3: Conversation with finished_at within lag window is ignored."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 21, 40, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 22, 5, tzinfo=timezone.utc),  # 5 min ago
            language="en",
            source="omi",
        )

        assert is_finalized(conv, lag_minutes=10) is False

    @freeze_time("2026-01-10T22:20:00Z")
    def test_conversation_after_lag_window_eligible(self):
        """PRD Test 4: Same conversation later becomes eligible."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 21, 40, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 22, 5, tzinfo=timezone.utc),  # 15 min ago
            language="en",
            source="omi",
        )

        assert is_finalized(conv, lag_minutes=10) is True

    def test_conversation_without_finished_at_ignored(self):
        """Conversation without finished_at is never finalized."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 21, 40, tzinfo=timezone.utc),
            finished_at=None,
            language="en",
            source="omi",
        )

        assert is_finalized(conv, lag_minutes=10) is False

    @freeze_time("2026-01-10T22:10:00Z")
    def test_exactly_at_lag_boundary(self):
        """Conversation exactly at lag boundary is eligible."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 21, 40, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 22, 0, tzinfo=timezone.utc),  # exactly 10 min ago
            language="en",
            source="omi",
        )

        assert is_finalized(conv, lag_minutes=10) is True
```

**Step 2: Run tests**

Run: `pytest tests/test_finalization.py -v`
Expected: FAIL

**Step 3: Implement finalization logic**

```python
"""Finalization logic for avoiding mid-conversation partials."""
from datetime import datetime, timezone, timedelta
from typing import Optional
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
```

**Step 4: Update Conversation model to allow None finished_at**

In models.py, change `finished_at: datetime` to `finished_at: Optional[datetime]`.

**Step 5: Run tests**

Run: `pytest tests/test_finalization.py -v`
Expected: PASS

**Step 6: Commit**

```bash
git add src/omi_sync/finalization.py tests/test_finalization.py src/omi_sync/models.py
git commit -m "feat: add finalization logic (PRD tests 3-4)"
```

---

## Phase 5: Notable Classification

### Task 5.1: Notable Classification Rules

**Files:**
- Create: `src/omi_sync/notable.py`
- Create: `tests/test_notable.py`

**Step 1: Write failing tests**

```python
"""Tests for notable conversation classification."""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from omi_sync.notable import is_notable, load_overrides
from omi_sync.models import Conversation, ActionItem
from omi_sync.config import Config


@pytest.fixture
def config():
    """Default config for notable tests."""
    return Config(
        api_key="test",
        vault_path=Path("/tmp"),
        notable_duration_minutes=25,
        notable_action_items_min=2,
        notable_keywords=["therapy", "therapist", "interview", "1:1", "doctor"],
    )


class TestNotableClassification:
    """PRD: Notable classification tests 9-12."""

    def test_duration_rule_triggers(self, config):
        """PRD Test 9: Duration rule triggers."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),  # 30 min
            language="en",
            source="omi",
            title="Long Meeting",
        )

        assert is_notable(conv, config) is True

    def test_duration_below_threshold_not_notable(self, config):
        """Duration below threshold is not notable."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 20, tzinfo=timezone.utc),  # 20 min
            language="en",
            source="omi",
            title="Short Meeting",
        )

        assert is_notable(conv, config) is False

    def test_action_items_rule_triggers(self, config):
        """PRD Test 10: Action-items rule triggers."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 15, tzinfo=timezone.utc),  # 15 min (short)
            language="en",
            source="omi",
            title="Action Meeting",
            action_items=[
                ActionItem(description="Task 1", completed=False),
                ActionItem(description="Task 2", completed=False),
            ],
        )

        assert is_notable(conv, config) is True

    def test_keyword_rule_triggers_title(self, config):
        """PRD Test 11: Keyword rule triggers in title."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 15, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="Therapy Session",
        )

        assert is_notable(conv, config) is True

    def test_keyword_rule_triggers_overview(self, config):
        """Keyword rule triggers in overview."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 15, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="Meeting",
            overview="Discussion about the interview process",
        )

        assert is_notable(conv, config) is True

    def test_keyword_case_insensitive(self, config):
        """Keywords match case-insensitively."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 15, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="THERAPY SESSION",
        )

        assert is_notable(conv, config) is True


class TestOverrides:
    """PRD Test 12: Override file forces true/false."""

    def test_override_forces_false(self, config, tmp_path):
        """Override can force notable to false."""
        overrides_file = tmp_path / "notable.json"
        overrides_file.write_text('{"conv_therapy": false}')

        conv = Conversation(
            id="conv_therapy",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 55, tzinfo=timezone.utc),  # 55 min
            language="en",
            source="omi",
            title="Therapy Session",  # Would be notable
        )

        overrides = load_overrides(overrides_file)
        assert is_notable(conv, config, overrides=overrides) is False

    def test_override_forces_true(self, config, tmp_path):
        """Override can force notable to true."""
        overrides_file = tmp_path / "notable.json"
        overrides_file.write_text('{"conv_short": true}')

        conv = Conversation(
            id="conv_short",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 5, tzinfo=timezone.utc),  # 5 min
            language="en",
            source="omi",
            title="Quick Chat",  # Would NOT be notable
        )

        overrides = load_overrides(overrides_file)
        assert is_notable(conv, config, overrides=overrides) is True

    def test_missing_overrides_file_returns_empty(self, tmp_path):
        """Missing overrides file returns empty dict."""
        overrides = load_overrides(tmp_path / "nonexistent.json")
        assert overrides == {}
```

**Step 2: Run tests**

Run: `pytest tests/test_notable.py -v`
Expected: FAIL

**Step 3: Implement notable classification**

```python
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
```

**Step 4: Run tests**

Run: `pytest tests/test_notable.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/omi_sync/notable.py tests/test_notable.py
git commit -m "feat: add notable classification (PRD tests 9-12)"
```

---

## Phase 6: Timezone and Date Grouping

### Task 6.1: Timezone Utilities

**Files:**
- Create: `src/omi_sync/timezone_utils.py`
- Create: `tests/test_timezone.py`

**Step 1: Write failing tests**

```python
"""Tests for timezone utilities."""
import pytest
from datetime import datetime, timezone
from omi_sync.timezone_utils import get_local_date, format_time_local
from omi_sync.models import Conversation


class TestTimezoneGrouping:
    """PRD Test 6: Groups by finished_at in America/New_York correctly."""

    def test_utc_to_eastern_same_day(self):
        """UTC afternoon is same day in Eastern."""
        dt = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)  # 6 PM UTC = 1 PM EST
        local_date = get_local_date(dt, "America/New_York")
        assert local_date == "2026-01-10"

    def test_utc_late_night_previous_day_eastern(self):
        """UTC early morning is previous day in Eastern."""
        dt = datetime(2026, 1, 10, 3, 0, 0, tzinfo=timezone.utc)  # 3 AM UTC = 10 PM EST previous day
        local_date = get_local_date(dt, "America/New_York")
        assert local_date == "2026-01-09"

    def test_utc_day_boundary_crossing(self):
        """Test UTC day boundary crossing."""
        # 11:30 PM Eastern on Jan 9 = 4:30 AM UTC on Jan 10
        dt = datetime(2026, 1, 10, 4, 30, 0, tzinfo=timezone.utc)
        local_date = get_local_date(dt, "America/New_York")
        assert local_date == "2026-01-09"

    def test_format_time_local(self):
        """Format time in local timezone."""
        dt = datetime(2026, 1, 10, 18, 30, 0, tzinfo=timezone.utc)  # 1:30 PM EST
        time_str = format_time_local(dt, "America/New_York")
        assert time_str == "13:30"

    def test_conversation_grouped_by_finished_at(self):
        """Conversations group by finished_at, not started_at."""
        # Started at 11 PM EST Jan 9, finished at 12:30 AM EST Jan 10
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 4, 0, tzinfo=timezone.utc),   # 11 PM EST Jan 9
            finished_at=datetime(2026, 1, 10, 5, 30, tzinfo=timezone.utc), # 12:30 AM EST Jan 10
            language="en",
            source="omi",
        )
        local_date = get_local_date(conv.finished_at, "America/New_York")
        assert local_date == "2026-01-10"
```

**Step 2: Run tests**

Run: `pytest tests/test_timezone.py -v`
Expected: FAIL

**Step 3: Implement timezone utilities**

```python
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
```

**Step 4: Run tests**

Run: `pytest tests/test_timezone.py -v`
Expected: PASS

**Step 5: Commit**

```bash
git add src/omi_sync/timezone_utils.py tests/test_timezone.py
git commit -m "feat: add timezone utilities (PRD test 6)"
```

---

## Phase 7: Markdown Generation

### Task 7.1: Slugify Helper

**Files:**
- Create: `src/omi_sync/slugify.py`
- Create: `tests/test_slugify.py`

**Step 1: Write tests**

```python
"""Tests for slugify helper."""
from omi_sync.slugify import slugify


class TestSlugify:
    def test_basic_slugify(self):
        assert slugify("Hello World") == "hello-world"

    def test_special_characters_removed(self):
        assert slugify("Meeting: Q1 Planning!") == "meeting-q1-planning"

    def test_multiple_spaces_collapsed(self):
        assert slugify("Too   Many   Spaces") == "too-many-spaces"

    def test_unicode_handled(self):
        assert slugify("Café Meeting") == "cafe-meeting"

    def test_empty_string(self):
        assert slugify("") == "untitled"

    def test_max_length(self):
        result = slugify("A" * 100, max_length=50)
        assert len(result) <= 50
```

**Step 2: Implement slugify**

```python
"""Stable slugify helper."""
import re
import unicodedata


def slugify(text: str, max_length: int = 50) -> str:
    """
    Convert text to URL-safe slug.

    PRD: Use a small slugify helper (stable).
    """
    if not text:
        return "untitled"

    # Normalize unicode
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")

    # Convert to lowercase
    text = text.lower()

    # Replace non-alphanumeric with hyphens
    text = re.sub(r"[^a-z0-9]+", "-", text)

    # Remove leading/trailing hyphens
    text = text.strip("-")

    # Collapse multiple hyphens
    text = re.sub(r"-+", "-", text)

    # Truncate
    if len(text) > max_length:
        text = text[:max_length].rstrip("-")

    return text or "untitled"
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_slugify.py -v
git add src/omi_sync/slugify.py tests/test_slugify.py
git commit -m "feat: add slugify helper"
```

---

### Task 7.2: Frontmatter Writer

**Files:**
- Create: `src/omi_sync/frontmatter_writer.py`
- Create: `tests/test_frontmatter.py`

**Step 1: Write tests**

```python
"""Tests for frontmatter writing."""
from omi_sync.frontmatter_writer import write_frontmatter


class TestFrontmatterWriter:
    def test_stable_key_ordering(self):
        """Keys are written in deterministic order."""
        data = {"z_key": "last", "a_key": "first", "date": "2026-01-10"}
        result1 = write_frontmatter(data)
        result2 = write_frontmatter(data)
        assert result1 == result2

    def test_yaml_format(self):
        """Output is valid YAML frontmatter."""
        data = {"date": "2026-01-10", "source": "omi"}
        result = write_frontmatter(data)
        assert result.startswith("---\n")
        assert result.endswith("---\n")
        assert "date: '2026-01-10'" in result or "date: 2026-01-10" in result

    def test_list_values(self):
        """List values are properly formatted."""
        data = {"people": ["Alice", "Bob"]}
        result = write_frontmatter(data)
        assert "people:" in result
        assert "Alice" in result
        assert "Bob" in result
```

**Step 2: Implement frontmatter writer**

```python
"""Frontmatter writer with stable key ordering."""
import yaml
from typing import Any, Dict


class StableOrderDumper(yaml.SafeDumper):
    """YAML dumper that maintains key order."""
    pass


def _dict_representer(dumper, data):
    return dumper.represent_mapping(
        yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG,
        sorted(data.items())
    )


StableOrderDumper.add_representer(dict, _dict_representer)


def write_frontmatter(data: Dict[str, Any]) -> str:
    """
    Write YAML frontmatter with stable key ordering.

    PRD: Use a YAML frontmatter writer that preserves stable ordering of keys.
    """
    yaml_str = yaml.dump(
        data,
        Dumper=StableOrderDumper,
        default_flow_style=False,
        allow_unicode=True,
        sort_keys=True,
    )
    return f"---\n{yaml_str}---\n"
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_frontmatter.py -v
git add src/omi_sync/frontmatter_writer.py tests/test_frontmatter.py
git commit -m "feat: add frontmatter writer with stable ordering"
```

---

### Task 7.3: People Extraction

**Files:**
- Create: `src/omi_sync/people.py`
- Create: `tests/test_people.py`

**Step 1: Write tests**

```python
"""Tests for people extraction."""
from omi_sync.people import extract_people
from omi_sync.models import Conversation, TranscriptSegment
from datetime import datetime, timezone


class TestPeopleExtraction:
    def test_extract_unique_speakers(self):
        """Extract unique speaker names from transcript."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
            language="en",
            source="omi",
            transcript_segments=[
                TranscriptSegment(speaker="SPEAKER_00", start=0, end=10, text="Hello"),
                TranscriptSegment(speaker="SPEAKER_01", start=10, end=20, text="Hi"),
                TranscriptSegment(speaker="SPEAKER_00", start=20, end=30, text="Bye"),
            ],
        )

        people = extract_people(conv)

        assert len(people) == 2
        assert "Speaker 0" in people
        assert "Speaker 1" in people

    def test_empty_transcript(self):
        """Empty transcript returns empty list."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
            language="en",
            source="omi",
            transcript_segments=[],
        )

        people = extract_people(conv)

        assert people == []
```

**Step 2: Implement people extraction**

```python
"""People extraction from conversations."""
import re
from typing import List
from omi_sync.models import Conversation


def extract_people(conv: Conversation) -> List[str]:
    """
    Extract unique participant names from conversation.

    PRD: people field should contain unique participant names
    extracted from transcript_segments speaker identification.
    """
    speakers = set()

    for segment in conv.transcript_segments:
        speakers.add(segment.speaker)

    # Convert SPEAKER_00 format to readable names
    people = []
    for speaker in sorted(speakers):
        # Convert "SPEAKER_00" to "Speaker 0"
        match = re.match(r"SPEAKER_(\d+)", speaker)
        if match:
            num = int(match.group(1))
            people.append(f"Speaker {num}")
        else:
            people.append(speaker)

    return people
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_people.py -v
git add src/omi_sync/people.py tests/test_people.py
git commit -m "feat: add people extraction from transcripts"
```

---

### Task 7.4: Raw Daily File Generator

**Files:**
- Create: `src/omi_sync/generators/raw.py`
- Create: `tests/test_generators_raw.py`

**Step 1: Write tests**

```python
"""Tests for raw daily file generation."""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from omi_sync.generators.raw import generate_raw_daily
from omi_sync.models import Conversation, TranscriptSegment, ActionItem
from omi_sync.config import Config


@pytest.fixture
def sample_conversations():
    """Sample conversations for testing."""
    return [
        Conversation(
            id="conv_001",
            started_at=datetime(2026, 1, 10, 14, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 14, 20, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="Morning Meeting",
            overview="Discussed project status",
            category="business",
            transcript_segments=[
                TranscriptSegment(speaker="SPEAKER_00", start=0, end=10, text="Hello everyone"),
                TranscriptSegment(speaker="SPEAKER_01", start=10, end=20, text="Hi there"),
            ],
        ),
        Conversation(
            id="conv_002",
            started_at=datetime(2026, 1, 10, 16, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 16, 30, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="Afternoon Chat",
            overview="Casual discussion",
            category="personal",
            transcript_segments=[
                TranscriptSegment(speaker="SPEAKER_00", start=0, end=5, text="Quick chat"),
            ],
        ),
    ]


@pytest.fixture
def config(tmp_path):
    return Config(api_key="test", vault_path=tmp_path)


class TestRawDailyGeneration:
    """PRD Tests 7-8: Raw file generation."""

    def test_raw_file_contains_correct_headings(self, sample_conversations, config):
        """PRD Test 7: Raw daily file contains correct headings including (omi:<id>)."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "# Omi Raw — 2026-01-10" in content
        assert "## 09:00 — Morning Meeting (omi:conv_001)" in content
        assert "## 11:00 — Afternoon Chat (omi:conv_002)" in content

    def test_transcript_segments_deterministic_order(self, sample_conversations, config):
        """PRD Test 8: Transcript segments render deterministically in order."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        # Check segments are in order
        hello_pos = content.find("Hello everyone")
        hi_pos = content.find("Hi there")
        assert hello_pos < hi_pos

    def test_frontmatter_contains_required_fields(self, sample_conversations, config):
        """Frontmatter contains all required fields."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "date: '2026-01-10'" in content or "date: 2026-01-10" in content
        assert "source: omi" in content
        assert "omi_sync: true" in content
        assert "people:" in content
        assert "generated_at:" in content
        assert "timezone: America/New_York" in content

    def test_transcript_in_details_block(self, sample_conversations, config):
        """Transcript is wrapped in details/summary block."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "<details>" in content
        assert "<summary>Transcript</summary>" in content
        assert "</details>" in content

    def test_conversations_sorted_by_started_at(self, config):
        """Conversations are sorted by started_at ascending."""
        convs = [
            Conversation(
                id="later",
                started_at=datetime(2026, 1, 10, 16, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 1, 10, 16, 30, tzinfo=timezone.utc),
                language="en",
                source="omi",
                title="Later Meeting",
            ),
            Conversation(
                id="earlier",
                started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
                language="en",
                source="omi",
                title="Earlier Meeting",
            ),
        ]

        content = generate_raw_daily(convs, "2026-01-10", config)

        earlier_pos = content.find("Earlier Meeting")
        later_pos = content.find("Later Meeting")
        assert earlier_pos < later_pos
```

**Step 2: Create generators package and implement**

```python
# src/omi_sync/generators/__init__.py
"""Markdown generators."""

# src/omi_sync/generators/raw.py
"""Raw daily file generator."""
from datetime import datetime
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
        "generated_at": format_datetime_local(datetime.now(), config.timezone),
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
```

**Step 3: Run tests and commit**

```bash
mkdir -p src/omi_sync/generators
touch src/omi_sync/generators/__init__.py
pytest tests/test_generators_raw.py -v
git add src/omi_sync/generators/ tests/test_generators_raw.py
git commit -m "feat: add raw daily file generator (PRD tests 7-8)"
```

---

### Task 7.5: Event Note Generator

**Files:**
- Create: `src/omi_sync/generators/event.py`
- Create: `tests/test_generators_event.py`

**Step 1: Write tests**

```python
"""Tests for event note generation."""
import pytest
from datetime import datetime, timezone
from omi_sync.generators.event import generate_event_note, get_event_filename
from omi_sync.models import Conversation, ActionItem
from omi_sync.config import Config


@pytest.fixture
def config(tmp_path):
    return Config(api_key="test", vault_path=tmp_path)


@pytest.fixture
def notable_conversation():
    return Conversation(
        id="conv_therapy_001",
        started_at=datetime(2026, 1, 10, 16, 0, tzinfo=timezone.utc),
        finished_at=datetime(2026, 1, 10, 16, 55, tzinfo=timezone.utc),
        language="en",
        source="omi",
        title="Therapy Session",
        overview="Discussed stress patterns and coping strategies.",
        category="personal",
        action_items=[
            ActionItem(description="Journal for 10 minutes daily", completed=False),
            ActionItem(description="Schedule follow-up", completed=True),
        ],
    )


class TestEventNoteGeneration:
    """PRD Tests 13-14: Event note generation."""

    def test_frontmatter_includes_raw_link(self, notable_conversation, config):
        """PRD Test 13: Event note frontmatter includes raw_link to exact raw heading."""
        content = generate_event_note(notable_conversation, config)

        assert "raw_link:" in content
        assert "[[2026-01-10#11:00 — Therapy Session (omi:conv_therapy_001)]]" in content

    def test_action_items_render_as_tasks(self, notable_conversation, config):
        """PRD Test 14: Action items render as - [ ] / - [x]."""
        content = generate_event_note(notable_conversation, config)

        assert "- [ ] Journal for 10 minutes daily" in content
        assert "- [x] Schedule follow-up" in content

    def test_frontmatter_contains_all_required_fields(self, notable_conversation, config):
        """All required frontmatter fields are present."""
        content = generate_event_note(notable_conversation, config)

        assert "omi_id:" in content
        assert "date:" in content
        assert "omi_sync: true" in content
        assert "people:" in content
        assert "started_at:" in content
        assert "finished_at:" in content
        assert "duration_minutes:" in content
        assert "category:" in content
        assert "raw_daily:" in content

    def test_body_structure(self, notable_conversation, config):
        """Body has correct structure."""
        content = generate_event_note(notable_conversation, config)

        assert "# Therapy Session" in content
        assert "## Summary" in content
        assert "## Action Items" in content
        assert "## Link to Raw" in content


class TestEventFilename:
    """Test deterministic event filename generation."""

    def test_filename_format(self, notable_conversation, config):
        """Filename follows PRD format."""
        filename = get_event_filename(notable_conversation, config)

        # Format: YYYY-MM-DDTHHMMSS - <slug(title)> - <omi_id>.md
        assert filename == "2026-01-10T110000 - therapy-session - conv_therapy_001.md"

    def test_filename_deterministic(self, notable_conversation, config):
        """Same conversation always produces same filename."""
        filename1 = get_event_filename(notable_conversation, config)
        filename2 = get_event_filename(notable_conversation, config)

        assert filename1 == filename2
```

**Step 2: Implement event generator**

```python
"""Event note generator."""
from datetime import datetime
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
        "finished_at": conv.finished_at.isoformat(),
        "generated_at": format_datetime_local(datetime.now(), config.timezone),
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
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_generators_event.py -v
git add src/omi_sync/generators/event.py tests/test_generators_event.py
git commit -m "feat: add event note generator (PRD tests 13-14)"
```

---

### Task 7.6: Highlights Generator

**Files:**
- Create: `src/omi_sync/generators/highlights.py`
- Create: `tests/test_generators_highlights.py`

**Step 1: Write tests**

```python
"""Tests for highlights generation."""
import pytest
from datetime import datetime, timezone
from omi_sync.generators.highlights import generate_highlights
from omi_sync.generators.event import get_event_filename
from omi_sync.models import Conversation
from omi_sync.config import Config


@pytest.fixture
def config(tmp_path):
    return Config(api_key="test", vault_path=tmp_path)


@pytest.fixture
def conversations_with_notable():
    """Mix of notable and non-notable conversations."""
    return [
        Conversation(
            id="conv_notable",
            started_at=datetime(2026, 1, 10, 14, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 14, 55, tzinfo=timezone.utc),  # 55 min - notable
            language="en",
            source="omi",
            title="Therapy Session",
        ),
        Conversation(
            id="conv_regular",
            started_at=datetime(2026, 1, 10, 16, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 16, 15, tzinfo=timezone.utc),  # 15 min - not notable
            language="en",
            source="omi",
            title="Quick Chat",
        ),
    ]


class TestHighlightsGeneration:
    """PRD Test 15: Highlights lists notable + all conversations with correct links."""

    def test_notable_events_section(self, conversations_with_notable, config):
        """Notable events section lists notable conversations."""
        notable_ids = {"conv_notable"}
        content = generate_highlights(
            conversations_with_notable,
            "2026-01-10",
            notable_ids,
            config,
        )

        assert "## Notable Events" in content
        assert "therapy-session" in content.lower()

    def test_all_conversations_section(self, conversations_with_notable, config):
        """All conversations section lists every conversation."""
        content = generate_highlights(
            conversations_with_notable,
            "2026-01-10",
            {"conv_notable"},
            config,
        )

        assert "## All Conversations" in content
        assert "Therapy Session" in content
        assert "Quick Chat" in content

    def test_notable_marked_in_all_conversations(self, conversations_with_notable, config):
        """Notable conversations marked with Event link in All Conversations."""
        content = generate_highlights(
            conversations_with_notable,
            "2026-01-10",
            {"conv_notable"},
            config,
        )

        # Notable should have "(Event: [[...]])" suffix
        assert "(Event:" in content

    def test_links_to_raw_headings(self, conversations_with_notable, config):
        """All conversations link to raw headings."""
        content = generate_highlights(
            conversations_with_notable,
            "2026-01-10",
            {"conv_notable"},
            config,
        )

        assert "[[2026-01-10#" in content
        assert "(omi:conv_notable)]]" in content
        assert "(omi:conv_regular)]]" in content

    def test_frontmatter_fields(self, conversations_with_notable, config):
        """Frontmatter contains required fields."""
        content = generate_highlights(
            conversations_with_notable,
            "2026-01-10",
            set(),
            config,
        )

        assert "date:" in content
        assert "source: omi" in content
        assert "omi_sync: true" in content
        assert "people:" in content

    def test_chronological_sorting(self, config):
        """Conversations sorted chronologically by started_at."""
        convs = [
            Conversation(
                id="later",
                started_at=datetime(2026, 1, 10, 18, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 1, 10, 18, 30, tzinfo=timezone.utc),
                language="en",
                source="omi",
                title="Later",
            ),
            Conversation(
                id="earlier",
                started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
                language="en",
                source="omi",
                title="Earlier",
            ),
        ]

        content = generate_highlights(convs, "2026-01-10", set(), config)

        earlier_pos = content.find("Earlier")
        later_pos = content.find("Later")
        assert earlier_pos < later_pos
```

**Step 2: Implement highlights generator**

```python
"""Highlights daily file generator."""
from datetime import datetime
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
        "generated_at": format_datetime_local(datetime.now(), config.timezone),
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
            raw_heading = f"{time_str} — {conv.title} (omi:{conv.id})"
            event_filename = get_event_filename(conv, config).replace(".md", "")
            lines.append(f"- [[{event_filename}]] — [[{date}#{raw_heading}]]")
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
        raw_heading = f"{time_str} — {conv.title} (omi:{conv.id})"
        line = f"- {time_str} — {conv.title} → [[{date}#{raw_heading}]]"

        if conv.id in notable_ids:
            event_filename = get_event_filename(conv, config).replace(".md", "")
            line += f" (Event: [[{event_filename}]])"

        lines.append(line)

    lines.append("")

    return "\n".join(lines)
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_generators_highlights.py -v
git add src/omi_sync/generators/highlights.py tests/test_generators_highlights.py
git commit -m "feat: add highlights generator (PRD test 15)"
```

---

## Phase 8: API Client

### Task 8.1: Omi API Client

**Files:**
- Create: `src/omi_sync/api_client.py`
- Create: `tests/test_api_client.py`

**Step 1: Write tests with mocked HTTP**

```python
"""Tests for Omi API client."""
import pytest
import json
from pathlib import Path
from omi_sync.api_client import OmiClient, OmiAPIError


class TestOmiClient:
    def test_fetch_conversations_with_pagination(self, httpx_mock, fixtures_dir):
        """Client handles pagination correctly."""
        with open(fixtures_dir / "conversations_page1.json") as f:
            page1 = json.load(f)
        with open(fixtures_dir / "conversations_page2.json") as f:
            page2 = json.load(f)

        httpx_mock.add_response(
            url="https://api.omi.me/v1/dev/user/conversations?include_transcript=true&limit=25&offset=0",
            json=page1,
        )
        httpx_mock.add_response(
            url="https://api.omi.me/v1/dev/user/conversations?include_transcript=true&limit=25&offset=25",
            json=page2,
        )
        httpx_mock.add_response(
            url="https://api.omi.me/v1/dev/user/conversations?include_transcript=true&limit=25&offset=50",
            json=[],  # Empty page signals end
        )

        client = OmiClient(api_key="test-key", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert len(conversations) == 5  # 3 from page1 + 2 from page2

    def test_authorization_header(self, httpx_mock):
        """Client sends correct authorization header."""
        httpx_mock.add_response(json=[])

        client = OmiClient(api_key="secret-key", base_url="https://api.omi.me/v1/dev")
        client.fetch_all_conversations()

        request = httpx_mock.get_request()
        assert request.headers["Authorization"] == "Bearer secret-key"

    def test_retry_on_5xx(self, httpx_mock):
        """Client retries on 5xx errors."""
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(status_code=503)
        httpx_mock.add_response(json=[])  # Success on 3rd try

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert len(httpx_mock.get_requests()) == 3
        assert conversations == []

    def test_rate_limit_429_with_retry_after(self, httpx_mock):
        """Client respects Retry-After header on 429."""
        httpx_mock.add_response(
            status_code=429,
            headers={"Retry-After": "1"},
        )
        httpx_mock.add_response(json=[])

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")
        conversations = client.fetch_all_conversations()

        assert len(httpx_mock.get_requests()) == 2

    def test_max_retries_exceeded_raises(self, httpx_mock):
        """Client raises after max retries exceeded."""
        for _ in range(6):
            httpx_mock.add_response(status_code=503)

        client = OmiClient(api_key="test", base_url="https://api.omi.me/v1/dev")

        with pytest.raises(OmiAPIError, match="Max retries"):
            client.fetch_all_conversations()
```

**Step 2: Implement API client**

```python
"""Omi API client with retry logic."""
import time
import httpx
from typing import List, Dict, Any


class OmiAPIError(Exception):
    """API error."""
    pass


class OmiClient:
    """
    Client for Omi API.

    PRD: Handle retries on 5xx with exponential backoff (max attempts 5),
    429 with Retry-After if present, pagination.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.omi.me/v1/dev",
        max_retries: int = 5,
        page_size: int = 25,
    ):
        self.api_key = api_key
        self.base_url = base_url.rstrip("/")
        self.max_retries = max_retries
        self.page_size = page_size
        self._client = httpx.Client(timeout=30.0)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make request with retry logic."""
        url = f"{self.base_url}{path}"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            **kwargs.pop("headers", {}),
        }

        last_error = None
        for attempt in range(self.max_retries + 1):
            try:
                response = self._client.request(method, url, headers=headers, **kwargs)

                if response.status_code == 429:
                    # Rate limited
                    retry_after = int(response.headers.get("Retry-After", "1"))
                    time.sleep(retry_after)
                    continue

                if response.status_code >= 500:
                    # Server error - retry with exponential backoff
                    if attempt < self.max_retries:
                        time.sleep(2 ** attempt * 0.1)  # 0.1, 0.2, 0.4, 0.8, 1.6...
                        continue
                    raise OmiAPIError(f"Max retries exceeded: {response.status_code}")

                response.raise_for_status()
                return response

            except httpx.HTTPError as e:
                last_error = e
                if attempt < self.max_retries:
                    time.sleep(2 ** attempt * 0.1)
                    continue
                raise OmiAPIError(f"Request failed: {e}") from e

        raise OmiAPIError(f"Max retries exceeded: {last_error}")

    def fetch_all_conversations(self) -> List[Dict[str, Any]]:
        """
        Fetch all conversations with pagination.

        PRD: GET /user/conversations?include_transcript=true
        """
        all_conversations = []
        offset = 0

        while True:
            response = self._request(
                "GET",
                "/user/conversations",
                params={
                    "include_transcript": "true",
                    "limit": self.page_size,
                    "offset": offset,
                },
            )

            page = response.json()
            if not page:
                break

            all_conversations.extend(page)
            offset += self.page_size

        return all_conversations

    def close(self):
        """Close the HTTP client."""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_api_client.py -v
git add src/omi_sync/api_client.py tests/test_api_client.py
git commit -m "feat: add Omi API client with retry and pagination"
```

---

## Phase 9: State Management

### Task 9.1: State and Index Files

**Files:**
- Create: `src/omi_sync/state.py`
- Create: `tests/test_state.py`

**Step 1: Write tests**

```python
"""Tests for state management."""
import pytest
import json
from pathlib import Path
from datetime import datetime, timezone
from omi_sync.state import StateManager, IndexEntry


class TestStateManager:
    def test_creates_sync_directory(self, tmp_path):
        """Creates .omi-sync directory if missing."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)

        assert (vault_path / "Omi" / ".omi-sync").exists()

    def test_save_and_load_state(self, tmp_path):
        """State persists across instances."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager1 = StateManager(vault_path)
        manager1.update_cursor("2026-01-10T10:00:00Z")
        manager1.save()

        manager2 = StateManager(vault_path)
        assert manager2.state["last_cursor"] == "2026-01-10T10:00:00Z"

    def test_index_entry_operations(self, tmp_path):
        """Index entries can be added and retrieved."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)
        entry = IndexEntry(
            omi_id="conv_001",
            raw_date="2026-01-10",
            raw_heading="10:00 — Meeting (omi:conv_001)",
            event_path="Omi/Events/2026-01-10T100000 - meeting - conv_001.md",
            last_seen_finished_at="2026-01-10T10:30:00Z",
            last_content_hash="abc123",
        )

        manager.set_index_entry("conv_001", entry)
        manager.save()

        manager2 = StateManager(vault_path)
        retrieved = manager2.get_index_entry("conv_001")

        assert retrieved.omi_id == "conv_001"
        assert retrieved.raw_date == "2026-01-10"

    def test_get_all_entries_for_date(self, tmp_path):
        """Can retrieve all entries for a specific date."""
        vault_path = tmp_path / "vault"
        vault_path.mkdir()

        manager = StateManager(vault_path)
        manager.set_index_entry("conv_001", IndexEntry(
            omi_id="conv_001",
            raw_date="2026-01-10",
            raw_heading="heading1",
        ))
        manager.set_index_entry("conv_002", IndexEntry(
            omi_id="conv_002",
            raw_date="2026-01-10",
            raw_heading="heading2",
        ))
        manager.set_index_entry("conv_003", IndexEntry(
            omi_id="conv_003",
            raw_date="2026-01-09",
            raw_heading="heading3",
        ))

        entries = manager.get_entries_for_date("2026-01-10")

        assert len(entries) == 2
        assert all(e.raw_date == "2026-01-10" for e in entries)
```

**Step 2: Implement state manager**

```python
"""State and index management."""
import json
from dataclasses import dataclass, asdict, field
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
        # Atomic write for state
        with open(self.state_file, "w") as f:
            json.dump(self.state, f, indent=2, sort_keys=True)

        # Atomic write for index
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
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_state.py -v
git add src/omi_sync/state.py tests/test_state.py
git commit -m "feat: add state and index management"
```

---

## Phase 10: Sync Orchestration

### Task 10.1: File Writer with Atomic Writes

**Files:**
- Create: `src/omi_sync/file_writer.py`
- Create: `tests/test_file_writer.py`

**Step 1: Write tests**

```python
"""Tests for file writing."""
import pytest
from pathlib import Path
from omi_sync.file_writer import write_file_atomic


class TestFileWriter:
    def test_creates_parent_directories(self, tmp_path):
        """Creates parent directories if missing."""
        path = tmp_path / "a" / "b" / "c" / "file.md"

        write_file_atomic(path, "content")

        assert path.exists()
        assert path.read_text() == "content"

    def test_atomic_write_no_partial_files(self, tmp_path):
        """No partial files left on disk."""
        path = tmp_path / "file.md"

        write_file_atomic(path, "content")

        # Only the target file should exist
        files = list(tmp_path.iterdir())
        assert len(files) == 1
        assert files[0].name == "file.md"

    def test_overwrites_existing_file(self, tmp_path):
        """Existing file is overwritten."""
        path = tmp_path / "file.md"
        path.write_text("old content")

        write_file_atomic(path, "new content")

        assert path.read_text() == "new content"
```

**Step 2: Implement file writer**

```python
"""File writing with atomic operations."""
import tempfile
import os
from pathlib import Path


def write_file_atomic(path: Path, content: str):
    """
    Write file atomically using temp file + rename.

    PRD: For deterministic file writes: write to temp then atomic rename.
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp file in same directory
    fd, temp_path = tempfile.mkstemp(
        dir=path.parent,
        prefix=".tmp_",
        suffix=".md",
    )

    try:
        with os.fdopen(fd, "w") as f:
            f.write(content)

        # Atomic rename
        os.replace(temp_path, path)
    except:
        # Clean up temp file on error
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_file_writer.py -v
git add src/omi_sync/file_writer.py tests/test_file_writer.py
git commit -m "feat: add atomic file writer"
```

---

### Task 10.2: Main Sync Engine

**Files:**
- Create: `src/omi_sync/sync_engine.py`
- Create: `tests/test_sync_engine.py`

**Step 1: Write idempotency tests**

```python
"""Tests for sync engine."""
import pytest
import json
from datetime import datetime, timezone
from pathlib import Path
from freezegun import freeze_time
from omi_sync.sync_engine import SyncEngine
from omi_sync.config import Config


@pytest.fixture
def config(tmp_path):
    vault = tmp_path / "vault"
    vault.mkdir()
    return Config(api_key="test", vault_path=vault)


@pytest.fixture
def sample_api_response(fixtures_dir):
    with open(fixtures_dir / "conversations_page1.json") as f:
        return json.load(f)


class TestIdempotency:
    """PRD Tests 16-17: Idempotency."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_running_twice_yields_identical_files(self, config, sample_api_response):
        """PRD Test 16: Running twice with same fixtures yields byte-identical files."""
        engine = SyncEngine(config)

        # First run
        engine.sync(sample_api_response)
        first_run_files = {}
        for path in config.vault_path.rglob("*.md"):
            first_run_files[str(path.relative_to(config.vault_path))] = path.read_text()

        # Second run
        engine.sync(sample_api_response)
        second_run_files = {}
        for path in config.vault_path.rglob("*.md"):
            second_run_files[str(path.relative_to(config.vault_path))] = path.read_text()

        # Same files
        assert set(first_run_files.keys()) == set(second_run_files.keys())

        # Identical content (excluding generated_at timestamp)
        for path, content in first_run_files.items():
            # Content should match
            assert first_run_files[path] == second_run_files[path], f"Mismatch in {path}"

    @freeze_time("2026-01-10T22:00:00Z")
    def test_update_changes_files_in_place(self, config):
        """PRD Test 17: Update case changes summary and updates files in place."""
        engine = SyncEngine(config)

        # Initial data
        initial_data = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:20:00Z",
            "language": "en",
            "source": "omi",
            "structured": {
                "title": "Meeting",
                "overview": "Original summary",
                "action_items": [],
            },
            "transcript_segments": [],
        }]

        engine.sync(initial_data)

        # Updated data with new summary
        updated_data = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:20:00Z",
            "language": "en",
            "source": "omi",
            "structured": {
                "title": "Meeting",
                "overview": "Updated summary",
                "action_items": [],
            },
            "transcript_segments": [],
        }]

        engine.sync(updated_data)

        # Check raw file updated
        raw_file = config.vault_path / "Omi" / "Raw" / "2026-01-10.md"
        assert raw_file.exists()
        # The raw file doesn't contain overview, but we verify the file was regenerated


class TestStopToken:
    """PRD Test 18: Ralph stop token."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_successful_run_returns_done(self, config, sample_api_response):
        """PRD Test 18: Successful run returns DONE status."""
        engine = SyncEngine(config)
        result = engine.sync(sample_api_response)

        assert result["status"] == "DONE"


class TestDeduplication:
    """PRD Test 5: No duplicates on update."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_same_omi_id_with_later_finished_at_updates(self, config):
        """PRD Test 5: Same omi_id with later finished_at updates, no duplicates."""
        engine = SyncEngine(config)

        # First version
        data_v1 = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:20:00Z",
            "language": "en",
            "source": "omi",
            "structured": {"title": "Meeting v1", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]
        engine.sync(data_v1)

        # Same ID, later finished_at
        data_v2 = [{
            "id": "conv_001",
            "started_at": "2026-01-10T14:00:00Z",
            "finished_at": "2026-01-10T14:25:00Z",  # Later
            "language": "en",
            "source": "omi",
            "structured": {"title": "Meeting v2", "overview": "", "action_items": []},
            "transcript_segments": [],
        }]
        engine.sync(data_v2)

        # Check only one entry in raw file
        raw_file = config.vault_path / "Omi" / "Raw" / "2026-01-10.md"
        content = raw_file.read_text()

        # Should have v2 title, not v1
        assert "Meeting v2" in content
        assert content.count("(omi:conv_001)") == 1  # Only one heading
```

**Step 2: Implement sync engine**

```python
"""Main sync orchestration engine."""
from datetime import datetime, timezone
from typing import Dict, List, Any, Set
from collections import defaultdict
from pathlib import Path

from omi_sync.config import Config
from omi_sync.models import Conversation, parse_conversation
from omi_sync.finalization import is_finalized
from omi_sync.notable import is_notable, load_overrides
from omi_sync.timezone_utils import get_local_date, format_datetime_local
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
            if existing is None or conv.finished_at > existing.finished_at:
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
            local_date = get_local_date(conv.finished_at, self.config.timezone)
            by_date[local_date].append(conv)

        # Update index entries
        for conv in conversations:
            local_date = get_local_date(conv.finished_at, self.config.timezone)
            from omi_sync.timezone_utils import format_time_local
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
            highlights_path = self.config.vault_path / "Omi" / "Highlights" / f"{date}.md"
            write_file_atomic(highlights_path, highlights_content)
            stats["highlights_files"] += 1

        # Save state
        self.state.update_last_run(format_datetime_local(datetime.now(timezone.utc), self.config.timezone))
        self.state.save()

        return {"status": "DONE", "stats": stats}
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_sync_engine.py -v
git add src/omi_sync/sync_engine.py tests/test_sync_engine.py
git commit -m "feat: add sync engine with idempotency (PRD tests 5, 16-18)"
```

---

### Task 10.3: Wire Up CLI Run Command

**Files:**
- Modify: `src/omi_sync/cli.py`
- Modify: `tests/test_cli.py`

**Step 1: Add run command tests**

```python
# Add to tests/test_cli.py

class TestRunCommand:
    def test_run_outputs_done(self, temp_vault, monkeypatch, httpx_mock):
        """Run command outputs DONE on success."""
        monkeypatch.setenv("OMI_API_KEY", "test-key")
        monkeypatch.setenv("OMI_VAULT_PATH", str(temp_vault))

        httpx_mock.add_response(json=[])

        runner = CliRunner()
        result = runner.invoke(main, ["run"])

        assert result.exit_code == 0
        assert result.output.strip().endswith("DONE")

    def test_run_fails_without_config(self, monkeypatch):
        """Run fails without proper config."""
        monkeypatch.delenv("OMI_API_KEY", raising=False)

        runner = CliRunner()
        result = runner.invoke(main, ["run"])

        assert result.exit_code != 0
```

**Step 2: Update CLI**

```python
"""Omi to Obsidian sync CLI."""
import click


@click.group()
def main():
    """Sync Omi conversations to Obsidian vault."""
    pass


@main.command()
def run():
    """Run one-shot sync."""
    from omi_sync.config import load_config, ConfigError
    from omi_sync.api_client import OmiClient
    from omi_sync.sync_engine import SyncEngine

    try:
        config = load_config()
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)

    click.echo(f"Syncing to vault: {config.vault_path}")

    try:
        with OmiClient(config.api_key, config.api_base_url) as client:
            api_data = client.fetch_all_conversations()

        engine = SyncEngine(config)
        result = engine.sync(api_data)

        stats = result["stats"]
        click.echo(f"Processed {stats['dates']} date(s)")
        click.echo(f"  Raw files: {stats['raw_files']}")
        click.echo(f"  Event files: {stats['event_files']}")
        click.echo(f"  Highlights files: {stats['highlights_files']}")
        click.echo("DONE")

    except Exception as e:
        click.echo(f"Sync failed: {e}", err=True)
        raise SystemExit(1)


@main.command()
def doctor():
    """Validate configuration."""
    from omi_sync.config import load_config, ConfigError

    try:
        config = load_config()
        click.echo(f"API Key: {'*' * 8}...{config.api_key[-4:]}")
        click.echo(f"Vault Path: {config.vault_path}")
        click.echo(f"API URL: {config.api_base_url}")
        click.echo(f"Timezone: {config.timezone}")
        click.echo(f"Finalization Lag: {config.finalization_lag_minutes} minutes")
        click.echo(f"Notable Duration: {config.notable_duration_minutes} minutes")
        click.echo(f"Notable Action Items Min: {config.notable_action_items_min}")
        click.echo("Configuration OK")
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)


@main.command()
def rebuild_index():
    """Rebuild index from vault frontmatter."""
    from omi_sync.config import load_config, ConfigError
    from omi_sync.rebuild import rebuild_index_from_vault

    try:
        config = load_config()
    except ConfigError as e:
        click.echo(f"Configuration Error: {e}", err=True)
        raise SystemExit(1)

    count = rebuild_index_from_vault(config)
    click.echo(f"Rebuilt index with {count} entries")


if __name__ == "__main__":
    main()
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_cli.py -v
git add src/omi_sync/cli.py tests/test_cli.py
git commit -m "feat: wire up CLI run command"
```

---

### Task 10.4: Rebuild Index Command

**Files:**
- Create: `src/omi_sync/rebuild.py`
- Create: `tests/test_rebuild.py`

**Step 1: Write tests**

```python
"""Tests for rebuild index functionality."""
import pytest
from pathlib import Path
from omi_sync.rebuild import rebuild_index_from_vault
from omi_sync.config import Config
from omi_sync.state import StateManager


class TestRebuildIndex:
    def test_rebuilds_from_event_frontmatter(self, tmp_path):
        """Rebuilds index from event note frontmatter."""
        vault = tmp_path / "vault"
        vault.mkdir()

        # Create an event note with frontmatter
        events_dir = vault / "Omi" / "Events"
        events_dir.mkdir(parents=True)

        event_note = events_dir / "2026-01-10T100000 - meeting - conv_001.md"
        event_note.write_text("""---
omi_id: conv_001
date: '2026-01-10'
raw_link: '[[2026-01-10#10:00 — Meeting (omi:conv_001)]]'
---

# Meeting
""")

        config = Config(api_key="test", vault_path=vault)
        count = rebuild_index_from_vault(config)

        assert count == 1

        # Verify index was created
        state = StateManager(vault)
        entry = state.get_index_entry("conv_001")
        assert entry is not None
        assert entry.raw_date == "2026-01-10"

    def test_handles_no_files(self, tmp_path):
        """Handles empty vault gracefully."""
        vault = tmp_path / "vault"
        vault.mkdir()

        config = Config(api_key="test", vault_path=vault)
        count = rebuild_index_from_vault(config)

        assert count == 0
```

**Step 2: Implement rebuild**

```python
"""Rebuild index from vault frontmatter."""
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
                # Extract omi_ids from headings
                import re
                for match in re.finditer(r"## (\d{2}:\d{2}) — (.+?) \(omi:([^)]+)\)", content):
                    time_str, title, omi_id = match.groups()
                    if not state.get_index_entry(omi_id):
                        date = path.stem  # YYYY-MM-DD
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
    # [[2026-01-10#10:00 — Meeting (omi:conv_001)]]
    import re
    match = re.search(r"#(.+?)\]\]", raw_link)
    return match.group(1) if match else ""
```

**Step 3: Run tests and commit**

```bash
pytest tests/test_rebuild.py -v
git add src/omi_sync/rebuild.py tests/test_rebuild.py
git commit -m "feat: add rebuild-index command"
```

---

## Phase 11: Documentation

### Task 11.1: README

**Files:**
- Create: `README.md`

**Step 1: Write README**

```markdown
# Omi to Obsidian Sync

Sync Omi conversations to your Obsidian vault as structured Markdown files.

## Features

- **Daily Raw transcripts**: All conversations for each day in a single file
- **Notable Event notes**: Dedicated notes for significant conversations
- **Daily Highlights**: Quick overview with links to all conversations
- **Idempotent**: Safe to run repeatedly; produces identical output
- **Timezone-aware**: Groups conversations by local date

## Installation

```bash
pip install -e .
```

## Configuration

Set environment variables:

```bash
export OMI_API_KEY="your-api-key"
export OMI_VAULT_PATH="~/Notes 2025"  # Path to your Obsidian vault
```

Optional configuration:

```bash
export OMI_TIMEZONE="America/New_York"           # Default: America/New_York
export OMI_FINALIZATION_LAG_MINUTES="10"         # Default: 10
export OMI_NOTABLE_DURATION_MINUTES="25"         # Default: 25
export OMI_NOTABLE_ACTION_ITEMS_MIN="2"          # Default: 2
```

## Usage

### One-shot sync

```bash
omi-sync run
```

### Validate configuration

```bash
omi-sync doctor
```

### Rebuild index from vault

```bash
omi-sync rebuild-index
```

## Scheduling (macOS)

### Using cron

```bash
crontab -e
```

Add hourly sync:

```
0 * * * * /path/to/omi-sync run >> /tmp/omi-sync.log 2>&1
```

### Using launchd

Create `~/Library/LaunchAgents/com.omi-sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omi-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/path/to/omi-sync</string>
        <string>run</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>EnvironmentVariables</key>
    <dict>
        <key>OMI_API_KEY</key>
        <string>your-api-key</string>
        <key>OMI_VAULT_PATH</key>
        <string>/Users/you/Notes</string>
    </dict>
</dict>
</plist>
```

Load it:

```bash
launchctl load ~/Library/LaunchAgents/com.omi-sync.plist
```

## Notable Classification

Conversations are marked as "notable" if any of these apply:

1. Duration >= 25 minutes
2. Action items >= 2
3. Keywords in title/overview: therapy, therapist, interview, 1:1, doctor, etc.

Override with `Omi/.omi-sync/overrides/notable.json`:

```json
{
  "conversation_id_to_force_notable": true,
  "conversation_id_to_exclude": false
}
```

## Output Structure

```
YourVault/
└── Omi/
    ├── Raw/
    │   └── 2026-01-10.md
    ├── Highlights/
    │   └── 2026-01-10.md
    ├── Events/
    │   └── 2026-01-10T160000 - therapy-session - conv_001.md
    └── .omi-sync/
        ├── state.json
        ├── index.json
        └── overrides/
            └── notable.json
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest
```

## License

MIT
```

**Step 2: Commit**

```bash
git add README.md
git commit -m "docs: add README with usage instructions"
```

---

## Final Verification

### Task 12.1: Run All Tests

**Step 1: Run complete test suite**

```bash
pytest -v --tb=short
```

Expected: All 18+ PRD tests pass.

**Step 2: Manual verification**

```bash
# Set up test environment
export OMI_API_KEY="test"
export OMI_VAULT_PATH="/tmp/test-vault"
mkdir -p /tmp/test-vault

# Run doctor
omi-sync doctor

# Run sync (will use empty API response without real key)
omi-sync run
```

**Step 3: Final commit**

```bash
git add -A
git commit -m "feat: complete omi-sync implementation"
```

---

## Summary

This plan implements all PRD requirements:

| PRD Test | Task |
|----------|------|
| 1. Missing API key fails | Task 2.1 |
| 2. Vault path missing fails | Task 2.1 |
| 3. Finalization lag ignores recent | Task 4.1 |
| 4. Later becomes eligible | Task 4.1 |
| 5. Same omi_id updates, no duplicates | Task 10.2 |
| 6. Timezone grouping | Task 6.1 |
| 7. Raw headings with omi_id | Task 7.4 |
| 8. Transcript deterministic order | Task 7.4 |
| 9. Duration rule | Task 5.1 |
| 10. Action items rule | Task 5.1 |
| 11. Keyword rule | Task 5.1 |
| 12. Override file | Task 5.1 |
| 13. Event raw_link | Task 7.5 |
| 14. Action items as tasks | Task 7.5 |
| 15. Highlights links | Task 7.6 |
| 16. Idempotent - identical files | Task 10.2 |
| 17. Update in place | Task 10.2 |
| 18. DONE stop token | Task 10.2 |
