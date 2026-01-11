"""Tests for data models."""
import pytest
import json
from datetime import datetime, timezone
from omi_sync.models import Conversation, TranscriptSegment, ActionItem, parse_conversation


class TestConversationParsing:
    def test_parse_full_conversation(self, fixtures_dir):
        """Parse a complete conversation from API response."""
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
        with open(fixtures_dir / "edge_cases.json") as f:
            data = json.load(f)

        conv = parse_conversation(data[0])  # conv_missing_structured

        assert conv.id == "conv_missing_structured"
        assert conv.title == "Untitled"
        assert conv.overview == ""
        assert conv.action_items == []

    def test_parse_conversation_missing_transcript(self, fixtures_dir):
        """Handle conversation with null transcript_segments."""
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

    def test_parse_with_geolocation(self, fixtures_dir):
        """Parse conversation with geolocation data."""
        with open(fixtures_dir / "conversations_page1.json") as f:
            data = json.load(f)

        conv = parse_conversation(data[0])  # Feature Discussion has geolocation

        assert conv.geolocation is not None
        assert conv.geolocation.latitude == 40.7128
        assert conv.geolocation.address == "New York, NY, USA"

    def test_parse_without_geolocation(self, fixtures_dir):
        """Parse conversation without geolocation."""
        with open(fixtures_dir / "conversations_page1.json") as f:
            data = json.load(f)

        conv = parse_conversation(data[1])  # Quick Check-in has no geolocation

        assert conv.geolocation is None
