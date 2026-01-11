"""Tests for raw daily file generation."""
import pytest
from datetime import datetime, timezone
from freezegun import freeze_time
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

    @freeze_time("2026-01-10T22:00:00Z")
    def test_raw_file_contains_correct_headings(self, sample_conversations, config):
        """PRD Test 7: Raw daily file contains correct headings including (omi:<id>)."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "# Omi Raw — 2026-01-10" in content
        assert "## 09:00 — Morning Meeting (omi:conv_001)" in content
        assert "## 11:00 — Afternoon Chat (omi:conv_002)" in content

    @freeze_time("2026-01-10T22:00:00Z")
    def test_transcript_segments_deterministic_order(self, sample_conversations, config):
        """PRD Test 8: Transcript segments render deterministically in order."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        # Check segments are in order
        hello_pos = content.find("Hello everyone")
        hi_pos = content.find("Hi there")
        assert hello_pos < hi_pos

    @freeze_time("2026-01-10T22:00:00Z")
    def test_frontmatter_contains_required_fields(self, sample_conversations, config):
        """Frontmatter contains all required fields."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "date:" in content
        assert "source: omi" in content
        assert "omi_sync: true" in content
        assert "people:" in content
        assert "generated_at:" in content
        assert "timezone: America/New_York" in content

    @freeze_time("2026-01-10T22:00:00Z")
    def test_transcript_in_details_block(self, sample_conversations, config):
        """Transcript is wrapped in details/summary block."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "<details>" in content
        assert "<summary>Transcript</summary>" in content
        assert "</details>" in content

    @freeze_time("2026-01-10T22:00:00Z")
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

    @freeze_time("2026-01-10T22:00:00Z")
    def test_metadata_bullets_present(self, sample_conversations, config):
        """Metadata bullets are present for each conversation."""
        content = generate_raw_daily(sample_conversations, "2026-01-10", config)

        assert "**Started**:" in content
        assert "**Finished**:" in content
        assert "**Duration**:" in content
        assert "**Category**:" in content
