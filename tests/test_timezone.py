"""Tests for timezone utilities."""
import pytest
from datetime import datetime, timezone
from omi_sync.timezone_utils import get_local_date, format_time_local, format_datetime_local
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

    def test_format_datetime_local(self):
        """Format full datetime in local timezone."""
        dt = datetime(2026, 1, 10, 18, 30, 0, tzinfo=timezone.utc)
        dt_str = format_datetime_local(dt, "America/New_York")
        assert "2026-01-10" in dt_str
        assert "13:30" in dt_str

    def test_naive_datetime_treated_as_utc(self):
        """Naive datetime is treated as UTC."""
        dt = datetime(2026, 1, 10, 18, 0, 0)  # No timezone
        local_date = get_local_date(dt, "America/New_York")
        assert local_date == "2026-01-10"

    def test_different_timezone(self):
        """Works with different timezones."""
        dt = datetime(2026, 1, 10, 18, 0, 0, tzinfo=timezone.utc)
        local_date = get_local_date(dt, "America/Los_Angeles")  # PST = UTC-8
        assert local_date == "2026-01-10"  # 10 AM PST, same day

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
