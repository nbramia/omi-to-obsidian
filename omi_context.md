Here’s a starter fixture set that mirrors the official Omi Developer API conversation shape (including the example fields for structured, geolocation, and transcript_segments) per Omi’s docs.  ￼

I’m giving you:
	•	fixtures/conversations_page1.json — what GET /user/conversations?limit=...&include_transcript=true&offset=0 could return
	•	fixtures/conversations_page2.json — second “page” (so the agent implements pagination/offset loops even if you later don’t need it)
	•	fixtures/overrides_notable.json — local override file example
	•	fixtures/edge_cases.json — conversations that trigger notable rules, missing structured, missing transcript, etc.

These are designed to exercise the PRD rules: notable by duration, notable by action items, keyword notable, override false, and the “finalization lag” case (conversation too recent → must be ignored). The timestamps are realistic and ISO8601.

⸻

fixtures/conversations_page1.json

[
  {
    "id": "conv_20260110_0001",
    "created_at": "2026-01-10T13:50:00Z",
    "started_at": "2026-01-10T13:50:00Z",
    "finished_at": "2026-01-10T14:10:00Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Feature Discussion",
      "overview": "Brainstorming session for new features and prioritization for the next sprint.",
      "emoji": "💼",
      "category": "business",
      "action_items": [
        {
          "description": "Create mockups for new UI",
          "completed": false,
          "created_at": "2026-01-10T14:10:00Z",
          "updated_at": "2026-01-10T14:10:00Z",
          "due_at": null,
          "completed_at": null
        }
      ],
      "events": []
    },
    "geolocation": {
      "latitude": 40.7128,
      "longitude": -74.006,
      "address": "New York, NY, USA",
      "google_place_id": "ChIJOwg_06VPwokRYv534QaPC8g",
      "location_type": "locality"
    },
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 9.2,
        "text": "Okay, let’s talk about the next sprint and what we can realistically ship.",
        "is_user": true,
        "person_id": null
      },
      {
        "speaker": "SPEAKER_01",
        "start": 9.2,
        "end": 20.0,
        "text": "I think the highest leverage is improving onboarding and reducing drop-off.",
        "is_user": false,
        "person_id": null
      },
      {
        "speaker": "SPEAKER_00",
        "start": 20.0,
        "end": 33.5,
        "text": "Agreed. Let’s define what good looks like and sketch the flow.",
        "is_user": true,
        "person_id": null
      }
    ]
  },
  {
    "id": "conv_20260110_0002",
    "created_at": "2026-01-10T15:05:00Z",
    "started_at": "2026-01-10T15:05:00Z",
    "finished_at": "2026-01-10T15:14:30Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Quick Check-in",
      "overview": "Short status check-in about errands and weekend plans.",
      "emoji": "🗒️",
      "category": "personal",
      "action_items": [],
      "events": []
    },
    "geolocation": null,
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 8.7,
        "text": "Let’s keep it quick—what are the top priorities for today?",
        "is_user": true,
        "person_id": null
      },
      {
        "speaker": "SPEAKER_01",
        "start": 8.7,
        "end": 16.9,
        "text": "Groceries, then I’ll swing by the pharmacy.",
        "is_user": false,
        "person_id": null
      }
    ]
  },
  {
    "id": "conv_20260110_0003",
    "created_at": "2026-01-10T16:00:00Z",
    "started_at": "2026-01-10T16:00:00Z",
    "finished_at": "2026-01-10T16:55:00Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Therapy Session",
      "overview": "Therapy session focusing on stress patterns, boundaries, and recovery habits.",
      "emoji": "🧠",
      "category": "personal",
      "action_items": [
        {
          "description": "Journal for 10 minutes after work at least 3 days this week",
          "completed": false,
          "created_at": "2026-01-10T16:55:00Z",
          "updated_at": "2026-01-10T16:55:00Z",
          "due_at": null,
          "completed_at": null
        },
        {
          "description": "Schedule next therapy session",
          "completed": true,
          "created_at": "2026-01-10T16:55:00Z",
          "updated_at": "2026-01-10T17:02:00Z",
          "due_at": null,
          "completed_at": "2026-01-10T17:02:00Z"
        }
      ],
      "events": []
    },
    "geolocation": {
      "latitude": 40.7411,
      "longitude": -73.9897,
      "address": "Manhattan, NY, USA",
      "google_place_id": null,
      "location_type": "locality"
    },
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 11.3,
        "text": "I want to talk about how I keep defaulting to overwork when I feel anxious.",
        "is_user": true,
        "person_id": null
      },
      {
        "speaker": "SPEAKER_01",
        "start": 11.3,
        "end": 24.8,
        "text": "Let’s map the trigger and the story you tell yourself in those moments.",
        "is_user": false,
        "person_id": null
      }
    ]
  }
]

What this covers:
	•	A business convo with 1 action item
	•	A short personal convo (should not be notable)
	•	A therapy session (keyword notable, duration notable, action items notable)

⸻

fixtures/conversations_page2.json

[
  {
    "id": "conv_20260109_0001",
    "created_at": "2026-01-10T01:30:00Z",
    "started_at": "2026-01-10T01:10:00Z",
    "finished_at": "2026-01-10T01:30:00Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Late Night Planning",
      "overview": "Planning next day agenda and deciding top three outcomes.",
      "emoji": "🌙",
      "category": "personal",
      "action_items": [
        {
          "description": "Draft tomorrow's agenda before breakfast",
          "completed": false,
          "created_at": "2026-01-10T01:30:00Z",
          "updated_at": "2026-01-10T01:30:00Z",
          "due_at": null,
          "completed_at": null
        }
      ],
      "events": []
    },
    "geolocation": null,
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 7.2,
        "text": "Tomorrow I need a tight agenda—three outcomes and nothing else.",
        "is_user": true,
        "person_id": null
      }
    ]
  },
  {
    "id": "conv_20260110_0004",
    "created_at": "2026-01-10T18:00:00Z",
    "started_at": "2026-01-10T18:00:00Z",
    "finished_at": "2026-01-10T18:40:00Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Hiring Interview: Ops Lead",
      "overview": "Interview discussion covering experience, compensation, and role scope.",
      "emoji": "🧑‍💼",
      "category": "business",
      "action_items": [
        {
          "description": "Send follow-up email to candidate",
          "completed": false,
          "created_at": "2026-01-10T18:40:00Z",
          "updated_at": "2026-01-10T18:40:00Z",
          "due_at": null,
          "completed_at": null
        },
        {
          "description": "Share interview notes with team",
          "completed": false,
          "created_at": "2026-01-10T18:40:00Z",
          "updated_at": "2026-01-10T18:40:00Z",
          "due_at": null,
          "completed_at": null
        }
      ],
      "events": []
    },
    "geolocation": null,
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 10.0,
        "text": "Thanks for taking the time—want to start with your last role and what you owned?",
        "is_user": true,
        "person_id": null
      },
      {
        "speaker": "SPEAKER_01",
        "start": 10.0,
        "end": 28.0,
        "text": "Sure. I led ops across finance, people, and vendor management.",
        "is_user": false,
        "person_id": null
      }
    ]
  }
]

What this covers:
	•	Interview is notable by duration and 2 action items
	•	Provides another day boundary possibility depending on timezone handling (you’ll group by finished_at in America/New_York)

⸻

fixtures/edge_cases.json

[
  {
    "id": "conv_missing_structured",
    "created_at": "2026-01-10T19:00:00Z",
    "started_at": "2026-01-10T19:00:00Z",
    "finished_at": "2026-01-10T19:05:00Z",
    "language": "en",
    "source": "omi",
    "structured": null,
    "geolocation": null,
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 4.0,
        "text": "This record has no structured output for some reason.",
        "is_user": true,
        "person_id": null
      }
    ]
  },
  {
    "id": "conv_no_transcript_segments",
    "created_at": "2026-01-10T20:00:00Z",
    "started_at": "2026-01-10T20:00:00Z",
    "finished_at": "2026-01-10T20:10:00Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "No Transcript Returned",
      "overview": "Structured exists but transcript segments are missing.",
      "emoji": "⚠️",
      "category": "business",
      "action_items": [],
      "events": []
    },
    "geolocation": null,
    "transcript_segments": null
  },
  {
    "id": "conv_too_recent_should_be_ignored",
    "created_at": "2026-01-10T21:55:00Z",
    "started_at": "2026-01-10T21:40:00Z",
    "finished_at": "2026-01-10T21:58:30Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Still Warm",
      "overview": "This conversation finished very recently and should be skipped until lag passes.",
      "emoji": "⏳",
      "category": "business",
      "action_items": [],
      "events": []
    },
    "geolocation": null,
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 3.0,
        "text": "If we sync right now, we might race post-processing.",
        "is_user": true,
        "person_id": null
      }
    ]
  },
  {
    "id": "conv_with_extra_fields_plugins_postprocessing",
    "created_at": "2026-01-10T12:00:00Z",
    "started_at": "2026-01-10T12:00:00Z",
    "finished_at": "2026-01-10T12:30:00Z",
    "language": "en",
    "source": "omi",
    "structured": {
      "title": "Plugin-Enhanced Conversation",
      "overview": "Example including plugins_results and postprocessing fields.",
      "emoji": "🧩",
      "category": "business",
      "action_items": [],
      "events": []
    },
    "geolocation": null,
    "transcript_segments": [
      {
        "speaker": "SPEAKER_00",
        "start": 0.0,
        "end": 6.0,
        "text": "This one has extra fields your parser should ignore safely.",
        "is_user": true,
        "person_id": null
      }
    ],
    "plugins_results": {
      "some_plugin": {
        "status": "success",
        "output": { "key": "value" }
      }
    },
    "postprocessing": {
      "status": "in_progress",
      "model": "fal_whisperx",
      "fail_reason": null
    },
    "discarded": false,
    "deleted": false,
    "visibility": "private"
  }
]

This mirrors documented “extra” keys Omi may include (plugins_results, postprocessing, discarded, deleted, visibility) and forces the agent to parse robustly.  ￼

⸻

fixtures/overrides_notable.json

{
  "conv_20260110_0003": false,
  "conv_20260110_0002": true
}

Meaning:
	•	Force “Therapy Session” to not create an event note (even though it matches keyword/duration/action-items)
	•	Force “Quick Check-in” to create an event note (useful to test overrides)

⸻

Minimal mock HTTP mapping (how the agent should use fixtures)

You can tell the agent: in tests, mock:
	•	GET /v1/dev/user/conversations?limit=25&offset=0&include_transcript=true
	•	returns conversations_page1.json
	•	GET /v1/dev/user/conversations?limit=25&offset=25&include_transcript=true
	•	returns conversations_page2.json

…and separately include edge_cases.json for targeted tests (finalization lag, missing structured, etc.).

The field set is aligned with Omi’s documented response examples and field descriptions.  ￼
