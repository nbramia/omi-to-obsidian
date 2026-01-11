# Omi to Obsidian Sync

Sync Omi conversations to your Obsidian vault as structured Markdown files.

## Features

- **Daily Raw transcripts**: All conversations for each day in a single file with collapsible transcripts
- **Notable Event notes**: Dedicated notes for significant conversations (therapy, interviews, long meetings)
- **Daily Highlights**: Quick overview with links to all conversations
- **Idempotent**: Safe to run repeatedly; produces identical output
- **Timezone-aware**: Groups conversations by local date (default: America/New_York)
- **People extraction**: Extracts participant names for downstream integrations

## Installation

```bash
cd /path/to/omi_to_obsidian
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Configuration

### Using a `.env` file (recommended)

Create a `.env` file in the project root:

```bash
# Required
OMI_API_KEY=your-omi-api-key
OMI_VAULT_PATH=~/Notes 2025

# Optional
OMI_TIMEZONE=America/New_York
OMI_FINALIZATION_LAG_MINUTES=10
OMI_NOTABLE_DURATION_MINUTES=25
OMI_NOTABLE_ACTION_ITEMS_MIN=2
OMI_API_BASE_URL=https://api.omi.me/v1/dev
```

The CLI automatically loads `.env` files from the current directory.

### Using environment variables

Alternatively, export variables directly:

```bash
export OMI_API_KEY="your-omi-api-key"
export OMI_VAULT_PATH="~/Notes 2025"
```

## Usage

### One-shot sync

```bash
omi-sync run
```

Outputs `DONE` on successful completion.

### Validate configuration

```bash
omi-sync doctor
```

### Rebuild index from vault

If your index gets out of sync, rebuild it from vault frontmatter:

```bash
omi-sync rebuild-index
```

## Scheduling (macOS)

### Using launchd (recommended)

1. Create a wrapper script `run-sync.sh` in your project directory:

```bash
#!/bin/bash
cd /path/to/omi_to_obsidian
export PYTHONPATH="/path/to/omi_to_obsidian/src"
/path/to/omi_to_obsidian/.venv/bin/python -m omi_sync.cli run
```

Make it executable:

```bash
chmod +x run-sync.sh
```

2. Create `~/Library/LaunchAgents/com.omi-sync.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.omi-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/path/to/omi_to_obsidian/run-sync.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>900</integer>
    <key>StandardOutPath</key>
    <string>/Users/you/Library/Logs/omi-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/you/Library/Logs/omi-sync.log</string>
    <key>RunAtLoad</key>
    <true/>
</dict>
</plist>
```

3. Load the job:

```bash
launchctl load ~/Library/LaunchAgents/com.omi-sync.plist
```

4. Useful commands:

```bash
# Check status
launchctl list com.omi-sync

# View logs
cat ~/Library/Logs/omi-sync.log

# Manually trigger
launchctl start com.omi-sync

# Stop scheduled job
launchctl unload ~/Library/LaunchAgents/com.omi-sync.plist
```

### Using cron

```bash
crontab -e
```

Add (runs every 15 minutes):

```
*/15 * * * * cd /path/to/omi_to_obsidian && /path/to/.venv/bin/omi-sync run >> /tmp/omi-sync.log 2>&1
```

## Notable Classification

Conversations are marked as "notable" if any of these criteria are met:

1. **Duration** >= 25 minutes
2. **Action items** >= 2
3. **Keywords** in title or overview (case-insensitive):
   - therapy, therapist, session
   - 1:1, one-on-one, standup, retro, planning, interview
   - doctor, appointment

### Manual Overrides

Override automatic classification by editing `Omi/.omi-sync/overrides/notable.json`:

```json
{
  "conversation_id_to_force_notable": true,
  "conversation_id_to_exclude": false
}
```

## Output Structure

```
YourVault/
└── Omi/
    ├── Raw/
    │   └── 2026-01-10.md                    # Daily raw transcripts
    ├── Highlights/
    │   └── 2026-01-10 Highlights.md         # Daily highlights with links
    ├── Events/
    │   └── 2026-01-10T160000 - therapy-session - abc123.md
    └── .omi-sync/
        ├── state.json                       # Sync state (last run time)
        ├── index.json                       # Conversation index
        └── overrides/
            └── notable.json                 # Manual notable overrides
```

## File Formats

### Raw Daily (`Omi/Raw/YYYY-MM-DD.md`)

```markdown
---
date: '2026-01-10'
source: omi
omi_sync: true
people: ['Speaker 0', 'Speaker 1']
generated_at: '2026-01-10T17:00:00-05:00'
timezone: America/New_York
---

# Omi Raw — 2026-01-10

## 09:00 — Meeting Title (omi:abc123)

- **Started**: 2026-01-10T14:00:00+00:00
- **Finished**: 2026-01-10T14:20:00+00:00
- **Duration**: 20 minutes
- **Category**: business

<details>
<summary>Transcript</summary>

- **SPEAKER_00**: Hello everyone
- **SPEAKER_01**: Hi there

</details>
```

### Highlights (`Omi/Highlights/YYYY-MM-DD Highlights.md`)

```markdown
---
date: '2026-01-10'
source: omi
omi_sync: true
people: ['Speaker 0']
generated_at: '2026-01-10T17:00:00-05:00'
timezone: America/New_York
---

# Omi Highlights — 2026-01-10

## Notable Events

- 16:00 — [[2026-01-10T160000 - therapy-session - abc123]]

## All Conversations

- 09:00 — Team standup → [[2026-01-10]]
- 16:00 — Therapy session → [[2026-01-10]] | [[2026-01-10T160000 - therapy-session - abc123]]
```

### Event Note (`Omi/Events/...md`)

```markdown
---
omi_id: abc123
date: '2026-01-10'
omi_sync: true
people: ['Speaker 0']
...
---

# Therapy Session

## Summary

Session overview here.

## Action Items

- [ ] Incomplete task
- [x] Completed task

## Transcript

<details>
<summary>Full transcript</summary>

- **SPEAKER_00**: ...

</details>
```

## Running Tests

```bash
pip install -e ".[dev]"
pytest -v
```

## API Reference

The sync uses the Omi Developer API:
- Endpoint: `GET /v1/conversations?include_transcript=true`
- Auth: `Authorization: <OMI_API_KEY>`
- Handles pagination, rate limiting (429), and retries (5xx)

## License

MIT
