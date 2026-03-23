---
name: baymax-sow-generator
description: >
  Generate a complete, client-ready Scheme of Work (SOW) for InnovaAI Integration Ltd
  within the Baymax project. Use this skill whenever Cameron mentions creating, writing,
  drafting, or building an SOW, Scheme of Work, proposal, or scoping document — even if
  phrased casually (e.g. "write up the SOW for X", "scope out a build for Y", "put
  together a proposal for Z", "here are my notes from the call"). Input is raw notes,
  discovery call notes, or a brief description of the client and project.
  CRITICAL: Always duplicate the Canva template before editing — never overwrite the master.
  Output: populated Canva design saved in Canva + PDF exported to
  ~/Downloads/Baymax/ClientName_Scheme_of_Work/
---

# Baymax SOW Generator

## Identity
**Business:** InnovaAI Integration Ltd
**Project:** Baymax
**Founders:** Cameron Atwal & Manjot Kaur
**Contact:** cameron@innovaaiintegration.com | www.innovaaiintegration.com

---

## Master Template

**Canva Template Design ID:** `DAHATWf39ac`

> CRITICAL RULE: NEVER edit the master template directly.
> You MUST duplicate it first. Every SOW gets its own copy.
> The master must always remain clean and unpopulated.

---

## Output Location

All completed SOW PDFs save to:
```
~/Downloads/Baymax/ClientName_Scheme_of_Work/ClientName_SOW_YYYY-MM.pdf
```

Where:
- `ClientName` = client name with spaces replaced by underscores
- `YYYY-MM` = current year and month (e.g. 2026-03)
- If file already exists → append `_v2`, `_v3` etc. — never overwrite
- Create the folder automatically if it doesn't exist

Example:
```
~/Downloads/Baymax/Westdale_Scheme_of_Work/Westdale_SOW_2026-03.pdf
```

---

## Step-by-Step Workflow

---

### STEP 0 — Ingest meeting notes from email

Cameron forwards meeting notes (typically Gemini summaries) to himself. When Cameron triggers the SOW skill:

1. **If Cameron pastes notes directly** — skip to Step 1.
2. **If Cameron says to check email / pull from email** — use the Gmail MCP to find the notes:
   - Search: `subject:"meeting notes" OR subject:"gemini notes" OR subject:"SOW" from:me to:me newer_than:7d`
   - If multiple results, list them by date and subject — ask Cameron which one
   - If one clear match, read the full message body
3. **Extract the raw content** — pull out:
   - Meeting date and attendees
   - Discussion points and client requirements
   - Any action items or decisions made
   - Cameron's additional notes (often added above the forwarded summary)
4. **Confirm with Cameron:** Show a brief summary of what was extracted and ask: **"Is this the right meeting? Anything to add before I start scoping?"**

> Never proceed past this step without Cameron confirming the source material is correct.

---

### STEP 1 — Discovery Q&A (mandatory before building)

Before writing any SOW content, Baymax MUST ask Cameron targeted questions to fill gaps. This step is NOT optional — even if the notes seem comprehensive.

**Always ask these core questions:**

1. **Client snapshot:** "What does [CLIENT_NAME] do, and roughly how big are they? (sector, team size, revenue ballpark if known)"
2. **The trigger:** "What made them reach out now? What's broken or painful enough that they're spending money on it?"
3. **Dream outcome:** "If this build goes perfectly, what does their day-to-day look like 3 months after delivery?"
4. **Budget / timeline signals:** "Did they mention a budget range or deadline? Any constraints I should know?"
5. **Tech landscape:** "What tools/platforms are they already using that we'd need to integrate with?"
6. **Decision maker:** "Who signs off — is it the person you spoke to, or someone else?"

**Then ask layer-specific questions based on what the notes suggest:**
- If notes mention data/documents: "What format is the data in? How much volume per week?"
- If notes mention AI/automation: "What currently requires human judgement vs what can be fully automated?"
- If notes mention integrations: "Who holds admin access to those systems? Any API limitations?"
- If notes mention reporting: "What metrics matter most? Who sees the reports?"

**Format:** Present all questions in a single numbered list. Wait for Cameron's answers before proceeding.

> CRITICAL: Do NOT start structuring layers or writing SOW content until Cameron has answered.
> If Cameron says "just go with what you have" — flag the gaps as `[NEEDS CONFIRMATION]` but still proceed.

---

### STEP 2 — Parse and structure the combined input

Take everything from Step 0 (email/notes) + Step 1 (Cameron's answers) and extract these fields:

| Field | Description |
|---|---|
| `CLIENT_NAME` | Full client / company name |
| `CLIENT_BACKGROUND` | Who they are, what they do, their size/sector (2-3 sentences) |
| `CLIENT_PROBLEM` | The core pain points they are experiencing — be specific, use their language |
| `SOLUTION_HEADLINE` | One-line summary of what InnovaAI is building |
| `SOLUTION_OVERVIEW` | 4-6 sentence executive summary of the full solution |
| `LAYERS` | Array of solution layers — see Layer Format below |
| `KEY_QUESTIONS` | Specific clarification questions needed from the client |
| `ROI_SUMMARY` | Quantified expected return — time, money, risk, or efficiency |
| `POSITIVE_IMPACT` | How the client's day-to-day changes after delivery |
| `OUT_OF_SCOPE` | Explicit list of what is NOT included |

**If any field cannot be inferred from the notes:**
- Flag it clearly with `[NEEDS CONFIRMATION]`
- List all flagged items before proceeding
- Ask Cameron to fill them in — do not invent details

---

### STEP 3 — Structure the solution layers

This is the most important section — layers are how the project gets costed and timed.

**Each layer must follow this exact format:**

```
Layer N: [Layer Name]

Purpose:
[What this layer does and why it matters to the client's outcome — 2-3 sentences]

What it includes:
- [Specific component or feature 1]
- [Specific component or feature 2]
- [Specific component or feature 3]
- [Add more as needed]

Outputs / Deliverables:
- [Tangible thing the client receives from this layer]
- [Tangible thing 2]

Complexity drivers:
- [What makes this layer complex — integrations, data volume, edge cases]

Questions to confirm for this layer:
- [Specific question 1 needed before build can start]
- [Specific question 2]
```

**Layer count:** Minimum 2, typical range 3-6. Each layer should map to a logical, separable part of the build.

**Layer reference patterns — adapt to the client's use case:**
- Data Capture / Intake
- AI Processing / Classification / Enrichment
- Automation / Workflow Logic
- Document Generation / Output
- Integration Layer (CRM, M365, Google Workspace, etc.)
- Dashboard / Reporting / Monitoring
- Training / Handover Layer

---

### STEP 4 — Build the Questions to Confirm section

Compile a master list of ALL questions across all layers, plus these standard ones:

**Business:**
- What is the single metric this must improve — time saved, revenue, accuracy, compliance?
- Who owns this process internally? Who is the day-to-day contact?

**Data:**
- What data sources are involved?
- Is any PII or sensitive data involved? UK-only storage requirement?

**Workflow:**
- What triggers the automation?
- What must be human-approved vs fully automated?

**Integrations:**
- Which tools must we integrate with?
- Who provides API keys and admin access?

**Volume:**
- How many items per day/week (emails, leads, documents, etc.)?
- Are there peak times or seasonal spikes?

**Quality:**
- What does a "good output" look like? Can you provide examples?
- Any brand tone or formatting requirements?

**Security:**
- Are user roles or access controls required?
- Is an audit trail required?

---

### STEP 5 — Build the ROI section

**This must be specific. No vague claims.**

Structure it as:

```
Current State:
[What the client is doing manually now — time, cost, error rate]

After Delivery:
[What changes — quantify wherever possible]

Estimated ROI:
- Time saved: [X hours/week or X hours/month]
- Cost saving: [£X/year if calculable]
- Risk reduction: [What failure or error is eliminated]
- Revenue impact: [If applicable — faster pipeline, more capacity, etc.]

Payback period: [Estimated time to recover the investment]
```

If Cameron hasn't provided enough data to quantify, use reasonable estimates and mark them `[ESTIMATED — TO CONFIRM WITH CLIENT]`.

---

### STEP 6 — Build the Positive Impact section

Describe how the client's working life improves after delivery. Write this in plain English, not technical language. Cover:

- What they stop doing manually
- What they gain visibility of
- How their team's day changes
- What becomes possible that wasn't before
- Any strategic or competitive advantage

---

### STEP 7 — Build the Out of Scope section

Always include these as a minimum, plus anything specific to this project:

```
The following are explicitly out of scope for this project:

- Any functionality not described in the layer breakdown above
- Changes to integrations or platforms not listed in this SOW
- Data migration from legacy systems unless explicitly stated
- Ongoing maintenance beyond the hypercare period (available separately)
- Training beyond what is specified in the deliverables
- Legal, compliance, or regulatory advice
- Third-party licensing costs (APIs, platforms, tools)

Any request outside this scope will be handled via a formal Change Request,
scoped and priced separately before work begins.
```

---

### STEP 8 — Duplicate the Canva template

Using the Canva MCP:

1. Call `create-design-from-candidate` or the appropriate duplication method to duplicate design `DAHATWf39ac`
2. Name the new design: `[CLIENT_NAME] — Scheme of Work [YYYY-MM]`
3. Confirm the duplicate has been created before proceeding
4. Note the new design ID — all subsequent edits go to the duplicate only

> If duplication fails: stop immediately and inform Cameron.
> Never proceed with editing the master template.

---

### STEP 9 — Populate the duplicate design

Using `start-editing-transaction` on the **duplicate only**, replace all existing content:

| Template Section | Content to Insert |
|---|---|
| Cover / Title | `[CLIENT_NAME] — Scheme of Work` + today's date |
| Executive Summary | `CLIENT_BACKGROUND` + `CLIENT_PROBLEM` + `SOLUTION_OVERVIEW` |
| Phase / Layer Summary | One paragraph per layer (name + purpose) |
| In-Depth Layer Breakdown | Full layer content (Purpose, Includes, Outputs, Complexity, Questions) |
| Key Assumptions & Notes | All `[NEEDS CONFIRMATION]` flags + dependencies |
| ROI Section | Full ROI structure from Step 4 |
| Positive Impact | Full impact narrative from Step 5 |
| Out of Scope | Full out of scope clause from Step 6 |
| Questions to Confirm | Master questions list from Step 3 |
| Thank You / Contact | Leave unchanged — Cameron's details already correct |

**Find and replace ALL instances of:**
- "J Group" → `[CLIENT_NAME]`
- Any previous client references → `[CLIENT_NAME]`

After editing each page, call `get-design-thumbnail` and show Cameron a preview.

---

### STEP 10 — Confirm with Cameron

Before committing, show Cameron:
- Summary of all sections populated
- Any `[NEEDS CONFIRMATION]` flags remaining
- Thumbnail previews of key pages

Ask: **"Does this look right? Shall I commit and export?"**

Only proceed after explicit confirmation.

---

### STEP 11 — Commit and export

1. Call `commit-editing-transaction` to save the duplicate design in Canva
2. Export as PDF using `export-design`
3. Save to:

```
~/Downloads/Baymax/ClientName_Scheme_of_Work/ClientName_SOW_YYYY-MM.pdf
```

**Naming rules:**
- `ClientName` = client name with spaces replaced by underscores
- `YYYY-MM` = current year and month
- If a file already exists with the same name → append `_v2`, `_v3` etc. — never overwrite
- Create the folder if it doesn't exist

Confirm to Cameron: **"PDF saved to ~/Downloads/Baymax/[ClientName]_Scheme_of_Work/"**

---

## SOW Content Rules (always enforce)

1. **Never write vague scope** — every layer must have concrete, specific deliverables
2. **Never invent client details** — flag unknowns, ask Cameron to confirm
3. **Layers must be separable** — each one should be independently understandable and costable
4. **ROI must be specific** — time, money, risk, or efficiency. No generic claims.
5. **Questions must be actionable** — each question should unlock a build decision
6. **Out of scope clause is mandatory** — always include it, never skip it
7. **Tone:** Professional, clear, premium. Client must read this and understand exactly what they're getting.
8. **UK English** throughout — £ not $

---

## Error Handling

| Scenario | Action |
|---|---|
| Raw notes too vague to infer layers | Ask Cameron 3-5 targeted questions before proceeding |
| Canva duplication fails | Stop immediately — inform Cameron — never edit the master |
| Export fails | Save structured SOW as markdown file to `~/Downloads/Baymax/` as fallback |
| Client name has special characters | Sanitise for folder/filename (remove `/` `\` `:` `*` `?`) |
| File already exists with same name | Append `_v2` — never overwrite |
| Missing field can't be inferred | Flag as `[NEEDS CONFIRMATION]` — don't fabricate |
