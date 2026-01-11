"""Tests for notable conversation classification."""
import pytest
from datetime import datetime, timezone
from pathlib import Path
from omi_sync.notable import is_notable, load_overrides
from omi_sync.models import Conversation, ActionItem
from omi_sync.config import Config


@pytest.fixture
def config(tmp_path):
    """Default config for notable tests."""
    return Config(
        api_key="test",
        vault_path=tmp_path,
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

    def test_invalid_json_returns_empty(self, tmp_path):
        """Invalid JSON returns empty dict."""
        overrides_file = tmp_path / "notable.json"
        overrides_file.write_text('not valid json')

        overrides = load_overrides(overrides_file)
        assert overrides == {}
