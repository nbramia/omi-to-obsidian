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

    @freeze_time("2026-01-10T22:10:00Z")
    def test_old_conversation_eligible(self):
        """Old conversations are always eligible."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 9, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 9, 11, 0, tzinfo=timezone.utc),  # Yesterday
            language="en",
            source="omi",
        )

        assert is_finalized(conv, lag_minutes=10) is True
