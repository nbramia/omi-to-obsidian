"""Tests for highlights generation."""
import pytest
from datetime import datetime, timezone
from freezegun import freeze_time
from omi_sync.generators.highlights import generate_highlights
from omi_sync.generators.event import get_event_filename
from omi_sync.models import Conversation, TranscriptSegment
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
            transcript_segments=[
                TranscriptSegment(speaker="SPEAKER_00", start=0, end=10, text="Hello"),
            ],
        ),
        Conversation(
            id="conv_regular",
            started_at=datetime(2026, 1, 10, 16, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 16, 15, tzinfo=timezone.utc),  # 15 min - not notable
            language="en",
            source="omi",
            title="Quick Chat",
            transcript_segments=[
                TranscriptSegment(speaker="SPEAKER_01", start=0, end=5, text="Hi"),
            ],
        ),
    ]


class TestHighlightsGeneration:
    """PRD Test 15: Highlights lists notable + all conversations with correct links."""

    @freeze_time("2026-01-10T22:00:00Z")
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

    @freeze_time("2026-01-10T22:00:00Z")
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

    @freeze_time("2026-01-10T22:00:00Z")
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

    @freeze_time("2026-01-10T22:00:00Z")
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

    @freeze_time("2026-01-10T22:00:00Z")
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
        assert "generated_at:" in content
        assert "timezone:" in content

    @freeze_time("2026-01-10T22:00:00Z")
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

    @freeze_time("2026-01-10T22:00:00Z")
    def test_no_notable_events_placeholder(self, config):
        """Shows placeholder when no notable events."""
        convs = [
            Conversation(
                id="regular",
                started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
                finished_at=datetime(2026, 1, 10, 10, 15, tzinfo=timezone.utc),
                language="en",
                source="omi",
                title="Regular Meeting",
            ),
        ]

        content = generate_highlights(convs, "2026-01-10", set(), config)

        assert "*No notable events.*" in content
