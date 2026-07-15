# Meeting Decision & Commitment Tracker — Documentation

A Microsoft Power Platform solution that captures **meeting decisions** (with rationale,
options considered, owner, and review date) and **commitments / follow-ups** (owner,
due date, status), so they stop getting lost in meeting notes.

Delivered as **two apps over one shared Dataverse** (see architecture below).

> **Intended use of these docs:** Feed them to **Microsoft Copilot inside Power Apps**
> to scaffold the Dataverse tables and the apps, then refine by hand. Read the files in
> order.

> **⭐ Number-one rule: keep it simple — this is a demo.** Build only the core feature set.
> Non-essential features (AI, extra fields) are explicitly **deferred** and called out in
> each doc under a "Deferred" note. The **daily overdue email reminder** is now **in scope**
> for this phase (it's what makes the app actually useful day-to-day). Working and simple
> beats feature-rich and unfinished.

## Solution architecture — two apps + one flow, one data source

Both apps (and the reminder flow) sit on the **same 4 Dataverse tables** in **one
solution**. No data duplication; a record created in one app appears instantly in the
other, and the flow reads live from the same tables.

```
        ┌─────────────────────────────────────┐
        │  Dataverse (one solution)           │
        │  Team Member · Meeting ·            │
        │  Decision · Commitment              │
        └──────────┬──────────┬───────────────┘
                   │          │
        ┌──────────▼─────┐  ┌─▼────────────────┐  ┌───────────────────────┐
        │ Model-driven   │  │ Canvas app        │  │ Power Automate flow   │
        │ (build FIRST — │  │ (demo showpiece — │  │ (daily, scheduled) —  │
        │  safety net,   │  │  dashboard + Radar│  │  emails each Owner    │
        │  fast admin)   │  │  + timeline)      │  │  their overdue items  │
        └────────────────┘  └───────────────────┘  └───────────────────────┘
```

- **Model-driven** is mostly auto-generated once the tables exist → build it first so you
  always have something to show.
- **Canvas** carries the demo wow-factor (Home KPIs, Follow-up Radar, decision timeline).
- **Power Automate flow** runs daily, queries overdue Commitments, and emails each Owner
  via Office 365 Outlook — using the fictional/dummy Email on their Team Member record.

## Document index

| # | File | Purpose |
|---|------|---------|
| 1 | [01-PRD.md](01-PRD.md) | Product requirements: problem, users, scope, features, user stories, success metrics |
| 2 | [02-DATA-MODEL.md](02-DATA-MODEL.md) | Dataverse tables, columns, data types, choices, relationships |
| 3 | [03-BUILD-GUIDE.md](03-BUILD-GUIDE.md) | Step-by-step build order for a Power Platform beginner (≤1 week) |
| 4 | [04-SAMPLE-DATA.md](04-SAMPLE-DATA.md) | Fictional, PII-free sample records to load for the demo |
| 5 | [05-COPILOT-PROMPTS.md](05-COPILOT-PROMPTS.md) | Ready-to-paste prompts for Copilot in Power Apps |
| 6 | [06-AYA-ASSESSMENT.md](06-AYA-ASSESSMENT.md) | Filled-in AYA scorecard proving the app is in-scope (Personal/Team) |
| 7 | [07-DEMO-PITCH.md](07-DEMO-PITCH.md) | One-page pitch & talking points for the client demo session |

## At a glance

- **AYA category:** Team / Single department (in-scope — no Enterprise dimensions)
- **Apps:** Two — a **model-driven** app + a **canvas** app, plus one **Power Automate** flow — over the same data
- **Backend:** Dataverse (4 lean tables incl. a fictional Team Member table) — no external SQL, no Client systems
- **Data:** Internal only — no PII, no financial, no client data (sample data and Team Member emails are fictional/dummy)
- **AI:** None in this phase (AYA score 1) — AI note-summarizer is deferred
- **Build target:** Beginner, ≤1 week; model-driven first (safety net), then canvas, then the reminder flow
- **Dependencies:** Dataverse + Office 365 Outlook connector (daily overdue-reminder flow, in scope this phase)
