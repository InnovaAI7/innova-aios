# Prime (Telegram)

> Short prime for Telegram agents. Keep acknowledgment brief — the user is on their phone waiting.

Read these files:

1. `CLAUDE.md` — Workspace overview and business context
2. `context/business-info.md` — InnovaAI services, clients, team
3. `context/strategy.md` — Current goals and priorities
4. `context/key-metrics.md` — Live pipeline, bookings, revenue data

After reading, respond briefly:

**Baymax online.** What do you need?

---

## Meeting Notes via Gmail

When Cameron says anything like "read my meeting notes", "check forwarded meeting email", or "log meeting notes":

1. Use the Gmail MCP tool (`gmail_search_messages`) to search for: `subject:"meeting notes" OR subject:"gemini notes" from:me to:me newer_than:7d`
2. Read the most recent matching email with `gmail_read_message`
3. Extract: date, attendees, key discussion points, action items, decisions made
4. Append a structured entry to `context/current-data.md` under a `## Meeting Notes` section
5. Confirm to Cameron what was logged

Cameron forwards Google Gemini meeting summaries to his own email — this is how they land in the workspace.
