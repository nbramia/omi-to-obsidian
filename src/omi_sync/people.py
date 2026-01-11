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
