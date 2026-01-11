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

    def test_speakers_sorted(self):
        """Speakers are returned in sorted order."""
        conv = Conversation(
            id="test",
            started_at=datetime(2026, 1, 10, 10, 0, tzinfo=timezone.utc),
            finished_at=datetime(2026, 1, 10, 10, 30, tzinfo=timezone.utc),
            language="en",
            source="omi",
            transcript_segments=[
                TranscriptSegment(speaker="SPEAKER_02", start=0, end=10, text="A"),
                TranscriptSegment(speaker="SPEAKER_00", start=10, end=20, text="B"),
                TranscriptSegment(speaker="SPEAKER_01", start=20, end=30, text="C"),
            ],
        )

        people = extract_people(conv)

        assert people == ["Speaker 0", "Speaker 1", "Speaker 2"]
