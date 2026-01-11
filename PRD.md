# Agent Prompt: Build Omi → Obsidian Sync (Hourly, Raw + Highlights + Notable Events)

You are implementing a local sync service that pulls Omi conversations via API and writes deterministic Markdown into an Obsidian vault.

## Ralph Wiggum method constraints
You are running in an autonomous loop. You stop only when:
1) all tests pass, and  
2) the CLI’s final output line is exactly `DONE`.

Design for deterministic outputs and idempotency so repeated runs converge.

---

## Operating environment
- Host: Mac mini (local filesystem access)
- Obsidian vault path (default): `~/nathanramia/Notes 2025/`
- Obsidian Sync exists but is irrelevant; treat as local disk.

---

## Primary goal
Hourly pull from Omi API and write:
1) One daily **Raw transcript** note with *all* transcripts for that day  
2) One daily **Highlights** note with key items and links  
3) One **Notable Event** note per notable conversation with link back to the Raw daily section.

Must be idempotent (update existing), no deletions downstream if Omi deletes.

---

## Critical correctness requirement: avoid mid-conversation partials
Only sync *finalized* conversations:
- Eligible if `finished_at` is present AND `finished_at <= now - FINALIZATION_LAG_MINUTES`
- Default `FINALIZATION_LAG_MINUTES = 10`

Additionally:
- Use a cursor buffer: when syncing, re-fetch from `(last_cursor - 10 minutes)` and dedupe by `omi_id`.

---

## Folder structure (inside vault)
Create:
- `Omi/Raw/`
- `Omi/Highlights/`
- `Omi/Events/`
- `Omi/.omi-sync/` (hidden state + index + config)

### Filenames
- Daily Raw: `Omi/Raw/YYYY-MM-DD.md`
- Daily Highlights: `Omi/Highlights/YYYY-MM-DD.md`
- Event notes: `Omi/Events/YYYY-MM-DDTHHMMSS - <slug(title)> - <omi_id>.md`

All names MUST be deterministic.

---

## API requirements
- Base URL default: `https://api.omi.me/v1/dev`
- Auth: `Authorization: Bearer <OMI_API_KEY>`
- Fetch conversations using: `GET /user/conversations?include_transcript=true`
- Handle:
  - retries on 5xx with exponential backoff (max attempts 5)
  - 429 with Retry-After if present
  - pagination if present (or loop until no more results)

You must NOT print the API key.

---

## Notable event classification (v1)
Implement `is_notable(conversation) -> bool` with these rules (ordered):

1) Duration >= `NOTABLE_DURATION_MINUTES` (default 25)  
2) Action items count >= `NOTABLE_ACTION_ITEMS_MIN` (default 2)  
3) Keyword match (case-insensitive) in title or overview against `NOTABLE_KEYWORDS` default:
   - therapy, therapist, session
   - 1:1, one-on-one, standup, retro, planning, interview
   - doctor, appointment
4) Manual overrides file: `Omi/.omi-sync/overrides/notable.json`:
   - `{ "<omi_id>": true|false, ... }` applies last

---

## Markdown output formats

### A) Daily Raw file format
Path: `Omi/Raw/YYYY-MM-DD.md`

Frontmatter required:
```yaml
---
date: YYYY-MM-DD
source: omi
omi_sync: true
people: ["<extracted participant names>"]
generated_at: <ISO8601 local time>
timezone: America/New_York
---
```

The `people` field should contain unique participant names extracted from the conversation (from `transcript_segments` speaker identification or structured data).

Body required:
	•	# Omi Raw — YYYY-MM-DD

For each conversation (sorted by started_at ascending, grouped by local day based on finished_at in TIMEZONE):
	•	Section heading MUST be stable and include omi_id:
	•	## HH:MM — <Title> (omi:<omi_id>)
	•	Metadata bullets (include anything present; ok to store location):
	•	started_at, finished_at, duration_minutes, category, language, source, location fields
	•	Transcript in <details>:
	•	<details><summary>Transcript</summary>
	•	Each transcript segment as:
	•	- **Speaker_0**: text
	•	</details>

B) Event note format (for notable convos)

Path: Omi/Events/YYYY-MM-DDTHHMMSS - <slug(title)> - <omi_id>.md

Frontmatter required:

---
omi_id: "<omi_id>"
date: "YYYY-MM-DD"
omi_sync: true
people: ["<extracted participant names>"]
started_at: "<ISO8601>"
finished_at: "<ISO8601>"
duration_minutes: <number>
category: "<string or empty>"
language: "<string or empty>"
source: "<string or empty>"
raw_daily: "[[YYYY-MM-DD]]"
raw_link: "[[YYYY-MM-DD#HH:MM — <Title> (omi:<omi_id>)]]"
generated_at: "<ISO8601 local time>"
---

Body required:
	•	# <Title>
	•	## Summary
	•	include structured overview (or placeholder if missing)
	•	## Action Items
	•	render as markdown tasks:
	•	incomplete: - [ ] ...
	•	complete: - [x] ...
	•	## Link to Raw
	•	include the raw_link

C) Daily Highlights format

Path: Omi/Highlights/YYYY-MM-DD.md

Frontmatter required:

---
date: YYYY-MM-DD
source: omi
omi_sync: true
people: ["<all unique participants from day's conversations>"]
generated_at: <ISO8601 local time>
timezone: America/New_York
---

Body required:
	•	# Omi Highlights — YYYY-MM-DD

Sections:
	1.	## Notable Events
	•	one bullet per notable conversation:
	•	- [[<event note filename>]] — [[YYYY-MM-DD#HH:MM — <Title> (omi:<omi_id>)]]
	2.	## All Conversations
	•	one bullet per conversation:
	•	- HH:MM — <Title> → [[YYYY-MM-DD#HH:MM — <Title> (omi:<omi_id>)]]
	•	if notable, append  (Event: [[<event note filename>]])

Sorting is chronological by started_at.

⸻

Idempotency + update rules
	•	Primary key: omi_id
	•	Maintain:
	•	Omi/.omi-sync/state.json (cursor + last run times)
	•	Omi/.omi-sync/index.json mapping omi_id -> { raw_date, raw_heading, event_path, last_seen_finished_at, last_content_hash }

On each run:
	•	Fetch eligible finalized conversations (see FINALIZATION_LAG)
	•	For each conversation:
	•	Compute local day from finished_at in TIMEZONE
	•	Update index entry
	•	Regenerate affected days’ Raw and Highlights files from scratch (deterministic)
	•	Regenerate event notes for all notable conversations (overwrite deterministically)
	•	If Omi deletes conversations later: do nothing (no local deletion).

⸻

CLI commands

Implement a CLI with at least:
	•	omi-sync run (one-shot run, suitable for cron/launchd)
	•	omi-sync doctor (validates config, vault paths, and can do a sample API call)
	•	omi-sync rebuild-index (scan vault to rebuild index from frontmatter omi_id)

omi-sync run must end with final output line exactly:
DONE

⸻

Scheduling

Do NOT implement launchd/cron scripts unless trivial; focus on the one-shot run that can be scheduled externally.
Assume hourly scheduling by cron/launchd.

⸻

Tests (must implement)

Use fixtures + mocked HTTP. No live API calls in tests.

Config tests
	1.	Missing API key fails fast and writes nothing
	2.	Vault path missing fails fast

Finalization / partial avoidance
	3.	Conversation with finished_at within lag window is ignored
	4.	Same conversation later becomes eligible and is ingested
	5.	If same omi_id appears with later finished_at, outputs update (no duplicates)

Timezone grouping
	6.	Groups by finished_at in America/New_York correctly across UTC day boundary

Raw file generation
	7.	Raw daily file exists and contains correct headings including (omi:<id>)
	8.	Transcript segments render deterministically in order

Notable classification
	9.	Duration rule triggers
	10.	Action-items rule triggers
	11.	Keyword rule triggers
	12.	Override file forces true/false

Event notes
	13.	Event note frontmatter includes raw_link to exact raw heading
	14.	Action items render as - [ ] / - [x]

Highlights
	15.	Highlights lists notable + all conversations with correct links

Idempotency
	16.	Running twice with same fixtures yields byte-identical files and no extra files
	17.	Update case changes summary and updates files in place

Ralph stop token
	18.	Successful run ends with final line DONE

⸻

Implementation preferences
	•	Language: choose Python (recommended) or Node; prioritize testability.
	•	Use a small slugify helper (stable).
	•	Use a YAML frontmatter writer that preserves stable ordering of keys.
	•	For deterministic file writes: write to temp then atomic rename.

⸻

Deliverables
	•	Source code
	•	Tests
	•	A README explaining:
	•	config
	•	how to run once
	•	how to schedule hourly on macOS (example launchd plist or cron line is ok)
	•	how to run tests

When everything is green, print DONE as the final line of omi-sync run.
