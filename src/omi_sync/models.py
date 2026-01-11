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
    finished_at: Optional[datetime]
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
        if self.finished_at is None:
            return 0
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

    finished_at = None
    if data.get("finished_at"):
        finished_at = date_parser.isoparse(data["finished_at"])

    return Conversation(
        id=data["id"],
        started_at=date_parser.isoparse(data["started_at"]),
        finished_at=finished_at,
        language=data.get("language", ""),
        source=data.get("source", ""),
        title=structured.get("title", "Untitled"),
        overview=structured.get("overview", ""),
        category=structured.get("category", ""),
        action_items=action_items,
        transcript_segments=transcript_segments,
        geolocation=geolocation,
    )
