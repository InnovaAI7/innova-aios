---
name: baymax-marketing-strategy
description: >
  Build Cameron's weekly LinkedIn marketing strategy for InnovaAI Integration. Use this
  skill whenever Cameron asks about his content plan, weekly strategy, what to post this
  week, marketing plan, content calendar, posting schedule, or anything related to
  planning his LinkedIn output — even casually (e.g. "plan my week", "what's my content
  strategy?", "what should I post this week?", "give me a plan", "marketing strategy",
  "content calendar for the week").
---

# Baymax Marketing Strategy Engine

## Purpose
Build a complete, actionable weekly LinkedIn content strategy for Cameron. Sits between trend research (`/trends`) and content creation (`/linkedin`). This is the planning layer — it turns raw trends and business context into a structured week of content.

## Cameron's Profile
**Name:** Cameron Atwal
**Business:** InnovaAI Integration Ltd — custom AI agents, automation, apps for SMEs and property businesses
**Audiences:** UK property developers/investors, SME founders/directors
**Brand:** Tech-forward, real, no corporate fluff. Short punchy lines. Building in public.
**LinkedIn:** linkedin.com/in/cameron-atwal-270b5a251

---

## Step-by-Step Workflow

### STEP 0 — Gather context

Before building the strategy, collect inputs from multiple sources:

**A. Trends (required)**
Run `/trends` research (or use results if already run this session). This gives the raw material — what's hot right now that Cameron can ride.

**B. Cameron's week (ask)**
Ask Cameron:
1. **"Any wins, milestones, or client updates from this week I should work into the content?"**
2. **"Anything coming up this week — calls, launches, events, deadlines?"**
3. **"Any specific topic you want to push this week?"**

If Cameron says "just go with what you have" — proceed using trends + business context only.

**C. Business context (pull automatically)**
- Check Trello pipeline: `python3 scripts/trello_api.py pipeline` — what stages are active, any recent movement
- Check calendar if relevant — any events, meetings, or deadlines this week
- Review Cameron's recent posts (if available) to avoid repetition

---

### STEP 1 — Define the weekly theme

Every week should have a **loose theme** that ties the content together. This creates narrative momentum and makes Cameron's profile feel intentional, not random.

**Theme sources (pick one or blend):**
- A strong trend from the research
- A milestone or win from Cameron's week
- A business principle Cameron lives by
- A client story or result
- A seasonal/timely hook (start of quarter, end of year, budget season, etc.)

Example themes:
- "The week I automated my own SOW process"
- "Why UK property businesses are 3 years behind on AI"
- "Building in public — what the first 6 months really looked like"

---

### STEP 2 — Plan the posting schedule

**Optimal LinkedIn posting for Cameron's audience:**

| Day | Time (UK) | Why |
|---|---|---|
| Monday | 7:30–8:30am | Decision-makers check LinkedIn before their week starts |
| Tuesday | 7:30–8:30am | Highest mid-week engagement for B2B |
| Wednesday | 12:00–1:00pm | Lunchtime scroll — good for lighter/story content |
| Thursday | 7:30–8:30am | Strong B2B day, good for educational content |
| Friday | 8:00–9:00am | Weekly reflections perform well on Fridays |
| Saturday | 9:00–10:00am | Lower competition, personal/story posts cut through |
| Sunday | Skip or optional | Rest day or light teaser for the week ahead |

**Recommended frequency:** 3–5 posts per week. Quality over quantity. Never post just to fill a slot.

---

### STEP 3 — Assign post types across the week

Use a mix of post types to keep the feed varied and hit different psychological triggers.

**Post type rotation:**

| Post Type | Purpose | Frequency |
|---|---|---|
| **Weekly Reflection** | Recap wins, lessons, teasers. Builds consistency. | 1x per week (Friday) |
| **Education / How-To** | Position Cameron as the AI expert. Teach something specific. | 1–2x per week |
| **Story / Personal** | Build relatability and trust. Behind the scenes, founder life. | 1x per week |
| **Results / Case Study** | Social proof. Specific numbers, real client outcomes. | 1x per week (if available) |
| **Hot Take / Opinion** | Ride a trend. Bold stance. Drives comments. | 0–1x per week |
| **Caption** | Pair with a graphic or video. Short, punchy. | As needed |

**Weekly template (adapt, don't follow rigidly):**

```
Monday    → Education / How-To (start the week with value)
Tuesday   → Story / Personal OR Hot Take (engagement driver)
Wednesday → Results / Case Study (midweek credibility)
Thursday  → Education OR Trend-based post
Friday    → Weekly Reflection (consistent anchor)
```

---

### STEP 4 — Build the content briefs

For each planned post, create a brief that Cameron can hand straight to `/linkedin`:

```
POST [N] — [Day, Date]
Type: [Education / Story / Results / Weekly / Hot Take / Caption]
Topic: [Specific topic — not vague]
Angle: [The unique spin — what makes this Cameron's take, not generic]
Trend tie-in: [Which trend this connects to, if any]
Key message: [The one thing the reader should take away]
Psychological triggers: [2-3 from the LinkedIn skill's framework]
Keywords: [3-5 keywords/phrases to naturally include for discoverability]
CTA: [What Cameron wants the reader to do]
Suggested hook: [One punchy opening line]
```

---

### STEP 5 — Keyword strategy

For each week, identify **5-10 keywords** Cameron should weave naturally into his posts. These improve LinkedIn search discoverability.

**Keyword sources:**
- Trending search terms from the trend research
- Cameron's core terms: AI agents, automation, custom AI, property tech, SME, workflow
- Audience pain points: manual processes, scaling, admin overload, tech stack
- Timely terms: whatever's in the news (e.g. a specific AI model launch, budget announcement)

**Rules:**
- Never keyword-stuff — weave them in naturally
- Use them in hooks and first 2 lines (LinkedIn truncates after ~3 lines)
- Hashtags should align with keywords (5-6 per post)

---

### STEP 6 — Engagement windows

After posting, Cameron should spend 15-20 minutes engaging to boost reach:

- **First 30 mins after posting:** Reply to every comment. LinkedIn's algorithm weights early engagement heavily.
- **Engage on 5-10 other posts** in his niche before and after posting — this signals activity to the algorithm.
- **Comment strategy:** Add value, ask questions, share opinions. Never just "Great post!"

Include specific engagement suggestions:
- "Comment on posts about [trending topic] with your AI perspective"
- "Engage with [specific creator or niche] posts this week"

---

### STEP 7 — Present the weekly strategy

Format the output exactly like this:

```
WEEKLY MARKETING STRATEGY — Week of [date]
Theme: [Weekly theme]

---

CONTENT CALENDAR

MONDAY [date] — 7:30am
Post type: [Type]
Topic: [Topic]
Angle: [Angle]
Hook: "[Suggested hook line]"
Keywords: [keyword1, keyword2, keyword3]
CTA: [CTA]
Psych triggers: [trigger1, trigger2]

TUESDAY [date] — 7:30am
...

(repeat for each planned post day)

---

KEYWORDS THIS WEEK
Primary: [3-5 keywords to use in every post]
Secondary: [3-5 keywords to rotate across posts]
Hashtags: [6-8 hashtags to rotate from]

---

ENGAGEMENT PLAN
- Before posting: Engage on [X] posts in [niche]
- After posting: Reply to all comments within 30 mins
- Midday: Comment on [specific type of content]
- Creators to engage with: [Suggest 2-3 types of accounts]

---

NOTES
- [Any strategic observations — e.g. "Burger Boi case study is ready to use", "Avoid posting about X, market is saturated"]
- [Connection to Cameron's pipeline — e.g. "Property content could warm up WestDale lead"]
```

---

## After the Strategy

Ask Cameron:
**"Happy with the plan? Want me to start writing any of these posts now?"**

If yes — hand off each post brief to `/linkedin` one at a time, in order.

---

## Rules

1. **Every post must have a clear purpose** — never "post for the sake of posting"
2. **Mix post types** — never 3 educational posts in a row. Variety keeps the audience engaged.
3. **Tie content to business goals** — if Cameron needs more discovery calls, weight CTAs toward booking links. If he's building authority, weight toward education and results.
4. **Be specific** — "Post about AI" is useless. "Post about how you built a retirement property finder for a client in 2 weeks using AI agents" is useful.
5. **Respect Cameron's bandwidth** — 3 strong posts beat 5 rushed ones. If he's had a busy week, recommend 3 and make them count.
6. **UK audience first** — times, language, references should all be UK-centric
7. **No repetition** — check what Cameron posted recently and avoid the same angles
8. **Trends decay fast** — if a trend is more than a week old, only use it if it's still generating conversation

---

## Error Handling

| Scenario | Action |
|---|---|
| Cameron gives no context about his week | Build strategy from trends + pipeline data only |
| No strong trends found | Fall back on evergreen topics + pipeline-driven content |
| Cameron wants fewer posts | Prioritise the highest-impact 2-3 and cut the rest |
| Cameron wants to push a specific topic | Build the week around that topic as the theme |
| Midweek pivot needed | Cameron can ask "update the strategy" — adjust remaining days |

$ARGUMENTS
