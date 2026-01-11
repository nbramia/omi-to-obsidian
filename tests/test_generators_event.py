"""Tests for event note generation."""
import pytest
from datetime import datetime, timezone
from freezegun import freeze_time
from omi_sync.generators.event import generate_event_note, get_event_filename
from omi_sync.models import Conversation, ActionItem, TranscriptSegment
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
        transcript_segments=[
            TranscriptSegment(speaker="SPEAKER_00", start=0, end=10, text="Hello"),
        ],
    )


class TestEventNoteGeneration:
    """PRD Tests 13-14: Event note generation."""

    @freeze_time("2026-01-10T22:00:00Z")
    def test_frontmatter_includes_raw_link(self, notable_conversation, config):
        """PRD Test 13: Event note frontmatter includes raw_link to exact raw heading."""
        content = generate_event_note(notable_conversation, config)

        assert "raw_link:" in content
        assert "[[2026-01-10#11:00 — Therapy Session (omi:conv_therapy_001)]]" in content

    @freeze_time("2026-01-10T22:00:00Z")
    def test_action_items_render_as_tasks(self, notable_conversation, config):
        """PRD Test 14: Action items render as - [ ] / - [x]."""
        content = generate_event_note(notable_conversation, config)

        assert "- [ ] Journal for 10 minutes daily" in content
        assert "- [x] Schedule follow-up" in content

    @freeze_time("2026-01-10T22:00:00Z")
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
        assert "generated_at:" in content

    @freeze_time("2026-01-10T22:00:00Z")
    def test_body_structure(self, notable_conversation, config):
        """Body has correct structure."""
        content = generate_event_note(notable_conversation, config)

        assert "# Therapy Session" in content
        assert "## Summary" in content
        assert "## Action Items" in content
        assert "## Link to Raw" in content

    @freeze_time("2026-01-10T22:00:00Z")
    def test_summary_includes_overview(self, notable_conversation, config):
        """Summary section includes the overview."""
        content = generate_event_note(notable_conversation, config)

        assert "Discussed stress patterns and coping strategies." in content

    @freeze_time("2026-01-10T22:00:00Z")
    def test_no_action_items_placeholder(self, config):
        """Shows placeholder when no action items."""
        conv = Conversation(
            id="conv_empty",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="Quick Meeting",
            action_items=[],
        )

        content = generate_event_note(conv, config)

        assert "*No action items.*" in content


class TestEventFilename:
    """Test deterministic event filename generation."""

    def test_filename_format(self, notable_conversation, config):
        """Filename follows PRD format: YYYY-MM-DDTHHMMSS - <slug(title)> - <omi_id>.md"""
        filename = get_event_filename(notable_conversation, config)

        # 16:55 UTC = 11:55 EST, so finished_at time
        assert filename == "2026-01-10T115500 - therapy-session - conv_therapy_001.md"

    def test_filename_deterministic(self, notable_conversation, config):
        """Same conversation always produces same filename."""
        filename1 = get_event_filename(notable_conversation, config)
        filename2 = get_event_filename(notable_conversation, config)

        assert filename1 == filename2

    def test_filename_handles_special_chars_in_title(self, config):
        """Filename handles special characters in title."""
        conv = Conversation(
            id="conv_special",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
            language="en",
            source="omi",
            title="Meeting: Q1 Planning!!! @Home",
        )

        filename = get_event_filename(conv, config)

        assert "meeting-q1-planning-home" in filename
        assert conv.id in filename
