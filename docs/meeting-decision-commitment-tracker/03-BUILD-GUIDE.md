# Build Guide — Meeting Decision & Commitment Tracker

**Two apps, one Dataverse.** For a **Power Platform beginner**, targeting **≤ 1 week**.

> **Demo scope rule:** build only the core below. AI, email reminders, and extra fields are
> **deferred** (see §Deferred). Simple and working beats feature-rich and unfinished.

## Two-app approach

Both apps sit on the **same 3 Dataverse tables** — no data duplication, changes in one
appear instantly in the other.

```
   Dataverse (one solution): Meeting · Decision · Commitment
                 │                        │
        Model-driven app            Canvas app
     (fast data entry/admin)   (demo visuals: dashboard + Radar)
```

- **Model-driven** = your safety net. Mostly auto-generated once tables exist, so you get a
  usable app fast.
- **Canvas** = the demo showpiece (Home dashboard, Follow-up Radar, decision timeline).

**Build the model-driven app FIRST** so you always have something to show, then invest the
remaining days in the canvas app.

## Prerequisites

- A Power Platform environment with **Dataverse** enabled.
- Maker access to https://make.powerapps.com.
- No external SQL, no Client systems, no special internal permissions required.
- No AI Builder, no Outlook connector needed (those features are deferred).

## Suggested week plan

| Day | Focus | App |
|-----|-------|-----|
| 1 | Create solution + 3 tables + choices + relationships (02-DATA-MODEL.md) | — |
| 2 | Load sample data (04-SAMPLE-DATA.md); verify relationships | — |
| 3 | **Track A** — Model-driven app: forms, core views, sitemap (safety net) | Model-driven |
| 4 | **Track B** — Canvas shell: Home dashboard + nav; Meetings & Decisions screens | Canvas |
| 5 | **Track B** — Commitments + Postpone + Follow-up Radar; polish/theme | Canvas |
| 6 | Buffer: fix issues, tidy both apps, package in one solution | Both |
| 7 | Test both against sample data; rehearse demo script | Both |

---

## Step 1 — Solution, tables, relationships (shared)

1. make.powerapps.com → **Solutions** → **New solution** → "Meeting Decision & Commitment Tracker".
2. Inside the solution, **New → Table** for **Meeting**, **Decision**, **Commitment** (columns per 02-DATA-MODEL.md).
3. Relationships:
   - Decision → **Lookup** "Meeting".
   - Commitment → **Lookup** "Meeting".
   - Commitment → **Lookup** "Related Decision" (optional).
4. **Do not** create calculated columns — derived flags are computed in the apps/views.

> Fastest path: paste the prompts in **05-COPILOT-PROMPTS.md** into Copilot, then verify types & choices.

## Step 2 — Load sample data (shared)

- Enter records from **04-SAMPLE-DATA.md** using the grid editor (Meetings → Decisions → Commitments).

---

## Track A — Model-driven app (Day 3, build this first)

1. In the solution: **New → App → Model-driven app**.
2. Add the three tables to the **sitemap** (one nav group each).
3. **Forms:** open each table's main form; arrange the core columns top-to-bottom (Copilot/default form is fine).
4. **Views** — create these (they reproduce the derived flags as filters):
   - Commitments → **Overdue** = Status not in (Done, Cancelled) AND Due Date is before Today.
   - Commitments → **Ownerless** = Owner does not contain data AND Status not in (Done, Cancelled).
   - Commitments → **Slipping** = Times Postponed ≥ 2 AND Status not in (Done, Cancelled).
   - Decisions → **Due for review** = Decision Status = Decided AND Review Date on or before Today.
   - Decisions → **Reversed / Superseded** = Decision Status in (Reversed, Superseded).
5. (Optional, still simple) Add a native **chart**: Commitments count by Commitment Status.
6. **Publish.** You now have a complete, usable app as a safety net.

---

## Track B — Canvas app (Days 4–5, the demo showpiece)

1. In the solution: **New → App → Canvas** (Tablet layout).
2. Add data sources: Meetings, Decisions, Commitments.

### Screen 1 — Home / Dashboard (KPI tiles)

```
// Open commitments
CountRows(Filter(Commitments, !(CommitmentStatus.Value in ["Done","Cancelled"])))

// Overdue
CountRows(Filter(Commitments,
    !(CommitmentStatus.Value in ["Done","Cancelled"]) && !IsBlank(DueDate) && DueDate < Today()))

// Decisions this month
CountRows(Filter(Decisions,
    Year(DecisionDate)=Year(Today()) && Month(DecisionDate)=Month(Today())))

// Decisions due for review
CountRows(Filter(Decisions,
    DecisionStatus.Value="Decided" && !IsBlank(ReviewDate) && ReviewDate <= Today()))

// Reversed / superseded decisions
CountRows(Filter(Decisions, DecisionStatus.Value in ["Reversed","Superseded"]))
```

Add nav buttons/icons to Meetings, Decisions, Commitments, Follow-up Radar.

### Screen 2 — Meetings + Meeting detail

- Gallery over `Meetings`, search on Meeting Name, dropdown filter on Meeting Type, "New" → form.
- Meeting detail: `EditForm` + two galleries filtered to the selected meeting (Decisions, Commitments).

### Screen 3 — Decisions + Decision detail

- Gallery + search; filter buttons by **Decision Status** (include a **Reversed** chip — the differentiator).
- **Timeline** = same gallery sorted by `DecisionDate` descending with a colored status tag.
- Decision detail: `EditForm` showing rationale + options; button "Add commitment" → new Commitment form with Meeting + Related Decision pre-set.

### Screen 4 — Commitments + Commitment detail

- Gallery with filter buttons: **All · My commitments (`Owner = MyNameInput.Text`) · Open · Overdue**. Color due date red when overdue.
- Commitment detail: `EditForm` + **Postpone** button (date picker → Patch from 02-DATA-MODEL.md).

### Screen 5 — Follow-up Radar (the wow screen)

Three galleries with a count badge each:

```
// Overdue
Filter(Commitments, !(CommitmentStatus.Value in ["Done","Cancelled"]) && !IsBlank(DueDate) && DueDate < Today())

// Ownerless
Filter(Commitments, IsBlank(Owner) && !(CommitmentStatus.Value in ["Done","Cancelled"]))

// Slipping (postponed >= 2)
Filter(Commitments, TimesPostponed >= 2 && !(CommitmentStatus.Value in ["Done","Cancelled"]))
```

Tapping a row navigates to Commitment detail.

---

## Package & test (Days 6–7)

- Confirm both apps are inside the **one solution**.
- Create a record in the model-driven app → verify it appears in the canvas app (same data proof).
- Walk the demo script; confirm Radar/KPIs match the sample data (04-SAMPLE-DATA.md).

## Demo script (5 minutes)

1. Canvas **Home dashboard** — Overdue and "Decisions due for review" tiles.
2. Open a **meeting** → decisions + commitments captured together.
3. Open a **decision** → rationale + options; filter Decisions to **Reversed**.
4. **Follow-up Radar** → Overdue / Ownerless / Slipping.
5. **Postpone** a commitment → Times Postponed increments → it appears under Slipping.
6. Switch to the **model-driven app** → "same data, a fast admin view" (create/edit a record live).

---

## §Deferred — NOT in this phase (keep it simple)

Explicitly out of scope for the demo; add later only if the client validates:

- AI note summarizer (Copilot/AI Builder)
- Daily overdue email reminder (Power Automate + Outlook)
- Extra fields (Priority, Confidence, Impact Area, Commitment Type, Notes)
- Approvals, Teams/Outlook sync, role-based views, trend analytics

Re-run the AYA form before building any of these — several would raise the app's scoring.
