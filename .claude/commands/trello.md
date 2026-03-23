---
name: baymax-trello
description: >
  Manage InnovaAI's client pipeline via Trello. Use this skill whenever Cameron asks
  about client status, pipeline updates, moving clients between stages, adding notes,
  or checking for overdue/stale projects. Triggers on: "show me my pipeline", "what's
  happening with [client]", "move [client] to [stage]", "update [client]", "any overdue
  clients?", "trello update", or any casual reference to client tracking.
---

# Baymax Trello — Client Pipeline Manager

## Identity
**Board:** InnovaAI Client Tracking
**Board ID:** Read from `TRELLO_BOARD_ID` in `.env`
**API credentials:** `TRELLO_API_KEY` and `TRELLO_TOKEN` in `.env`

---

## Pipeline Stages (in order)

| # | Stage | Meaning |
|---|---|---|
| 1 | Business Opportunities | Lead identified, not yet contacted |
| 2 | Discovery | Initial conversation / discovery call booked or done |
| 3 | Inital SOW | First scope of work being drafted |
| 4 | Deep Audit / SOW | Detailed scoping, refined SOW |
| 5 | Agreement | SOW sent, awaiting sign-off / payment |
| 6 | Build + Feedback | Active build with client feedback loops |
| 7 | Final Build | Final iteration before handover |
| 8 | Testing | QA and client testing |
| 9 | Training | Client training and documentation |
| 10 | Launch | Going live |
| 11 | Marketing / Testimonials | Post-launch — collecting results and social proof |
| 12 | Complete | Project delivered and closed |
| 13 | Project Cancelled / On Pause | Inactive |

---

## How to access Trello

Use the helper script at `scripts/trello_api.py` for all Trello operations.

Run via Bash tool:
```
python3 scripts/trello_api.py <command> [args]
```

Available commands:
- `python3 scripts/trello_api.py pipeline` — full pipeline overview
- `python3 scripts/trello_api.py client "Client Name"` — detailed client card info
- `python3 scripts/trello_api.py search "keyword"` — search cards by name
- `python3 scripts/trello_api.py move "Card ID" "List Name"` — move card to a stage
- `python3 scripts/trello_api.py comment "Card ID" "Note text"` — add a comment to a card
- `python3 scripts/trello_api.py due "Card ID" "YYYY-MM-DD"` — set/update due date
- `python3 scripts/trello_api.py stale 14` — show cards with no activity in N days
- `python3 scripts/trello_api.py labels "Card ID"` — show labels on a card
- `python3 scripts/trello_api.py add-label "Card ID" "Label Name"` — add a label

---

## Modes

### MODE 1 — Pipeline Overview
**Triggered by:** "show me my pipeline", "trello update", "where are my clients?", "pipeline status"

1. Run `python3 scripts/trello_api.py pipeline`
2. Present as a clean stage-by-stage summary
3. Highlight:
   - Total active clients (exclude Complete and Cancelled)
   - Which stages have the most cards (bottlenecks)
   - Any cards with overdue dates
4. Format:

```
PIPELINE OVERVIEW — [today's date]

[Stage Name] — [X] clients
  - Client A (last activity: X days ago)
  - Client B (due: YYYY-MM-DD)

...

SUMMARY
Active clients: X
Bottleneck: [stage with most cards]
Overdue: [list any overdue cards]
Stale (14+ days no activity): [list any]
```

### MODE 2 — Client Lookup
**Triggered by:** "what's happening with [client]?", "status on [client]", "check [client]"

1. Run `python3 scripts/trello_api.py search "client name"`
2. If found, run `python3 scripts/trello_api.py client "card_id"` for full details
3. Present:
   - Current stage
   - Due date (if set)
   - Last activity date + how many days ago
   - Recent comments (last 3)
   - Labels
   - Any checklist progress
4. If multiple matches, list them and ask Cameron which one

### MODE 3 — Move Client
**Triggered by:** "move [client] to [stage]", "push [client] to build"

1. Search for the client card
2. Confirm with Cameron: **"Move [Client Name] from [Current Stage] to [New Stage]?"**
3. Only proceed after confirmation
4. Run `python3 scripts/trello_api.py move "card_id" "List Name"`
5. Confirm: **"Done — [Client Name] is now in [New Stage]."**

### MODE 4 — Add Note / Comment
**Triggered by:** "add a note to [client]", "update [client] with...", "log this on [client]"

1. Search for the client card
2. Confirm the note content with Cameron
3. Run `python3 scripts/trello_api.py comment "card_id" "note text"`
4. Confirm: **"Note added to [Client Name]."**

### MODE 5 — Set Due Date
**Triggered by:** "set due date for [client]", "[client] is due [date]"

1. Search for the client card
2. Confirm: **"Set due date for [Client Name] to [date]?"**
3. Run `python3 scripts/trello_api.py due "card_id" "YYYY-MM-DD"`
4. Confirm done

### MODE 6 — Stale / Overdue Check
**Triggered by:** "any stale clients?", "overdue projects?", "what needs attention?"

1. Run `python3 scripts/trello_api.py stale 14`
2. Present cards with no activity in 14+ days
3. Also flag any cards past their due date
4. Suggest actions: "Want me to add a follow-up note or move any of these?"

---

## Presentation Rules

- Always show dates as relative where helpful: "3 days ago", "due in 5 days", "2 weeks overdue"
- Use the pipeline stage order — never sort alphabetically
- Bold client names for scannability
- If Cameron asks a vague question ("how's the pipeline?"), default to Mode 1
- Never modify cards without explicit confirmation from Cameron
- Keep output concise — Cameron wants a quick read, not a wall of text

---

## Error Handling

| Scenario | Action |
|---|---|
| Client name not found | Suggest closest matches or ask Cameron to clarify |
| Stage name doesn't match | Show the list of valid stages and ask again |
| API error / timeout | Report the error plainly and suggest retrying |
| Multiple cards match a search | List all matches with their current stage, ask which one |

$ARGUMENTS
