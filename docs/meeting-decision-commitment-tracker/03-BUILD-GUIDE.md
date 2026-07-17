# Build Guide — Meeting Decision & Commitment Tracker

**Two apps, one Dataverse.** For a **Power Platform beginner**, targeting **≤ 1 week**.

> **Demo scope rule:** build only the core below. AI and extra fields are **deferred** (see
> §Deferred). The **daily overdue email reminder** is in scope this phase. Simple and
> working beats feature-rich and unfinished.

## Two-app + one-flow approach

Both apps and the reminder flow sit on the **same 4 Dataverse tables** — no data
duplication, changes in one app appear instantly in the other, and the flow reads the
same live data.

```
   Dataverse (one solution): Team Member · Meeting · Decision · Commitment
          │                        │                        │
   Model-driven app            Canvas app          Power Automate flow
 (fast data entry/admin)  (demo visuals: dashboard   (daily overdue
                            + Radar)                  email reminder)
```

- **Model-driven** = your safety net. Mostly auto-generated once tables exist, so you get a
  usable app fast.
- **Canvas** = the demo showpiece (Home dashboard, Follow-up Radar, decision timeline).
- **Power Automate flow** = the "make it useful" piece — a daily scheduled flow that emails
  each Owner their overdue commitments (FR-10), built after both apps.

**Build the model-driven app FIRST** so you always have something to show, then invest the
remaining days in the canvas app and the reminder flow.

## Prerequisites

- A Power Platform environment with **Dataverse** enabled.
- Maker access to https://make.powerapps.com and https://make.powerautomate.com.
- No external SQL, no Client systems, no special internal permissions required.
- No AI Builder needed (deferred). The **Office 365 Outlook connector** is required for
  the daily reminder flow (standard connector, included with most licenses).

## Suggested week plan

| Day | Focus | Component |
|-----|-------|-----|
| 1 | Create solution + 4 tables (incl. Team Member + Email) + choices + relationships (02-DATA-MODEL.md) | — |
| 2 | Load sample data (04-SAMPLE-DATA.md); verify relationships | — |
| 3 | **Track A** — Model-driven app: forms, core views, sitemap (safety net) | Model-driven |
| 4 | **Track B** — Canvas shell: Home dashboard + nav; Meetings & Decisions screens | Canvas |
| 5 | **Track B** — Commitments + Postpone + Follow-up Radar; polish/theme | Canvas |
| 6 | **Track C** — Power Automate daily overdue reminder flow; buffer to fix issues, package in one solution | Flow + Both |
| 7 | Test all three against sample data; rehearse demo script | All |

---

## Step 1 — Solution, tables, relationships (shared)

1. make.powerapps.com → **Solutions** → **New solution** → "Meeting Decision & Commitment Tracker".
2. Inside the solution, **New → Table** for **Team Member**, **Meeting**, **Decision**, **Commitment** (columns per 02-DATA-MODEL.md). Team Member holds **fictional** people only — no PII.
3. Relationships:
   - Decision → **Lookup** "Meeting".
   - Decision → **Lookup** "Decision Maker" → Team Member (optional).
   - Commitment → **Lookup** "Meeting".
   - Commitment → **Lookup** "Owner" → Team Member (optional; blank = ownerless).
   - Commitment → **Lookup** "Related Decision" (optional).
4. **Do not** create calculated columns — derived flags are computed in the apps/views.

> Fastest path: paste the prompts in **05-COPILOT-PROMPTS.md** into Copilot, then verify types & choices.

## Step 2 — Load sample data (shared)

- Enter records from **04-SAMPLE-DATA.md** using the grid editor (**Team Members → Meetings → Decisions → Commitments** — people first so the Decision Maker/Owner lookups can resolve).

---

## Track A — Model-driven app (Day 3, build this first)

1. In the solution: **New → App → Model-driven app**.
2. Add Meeting, Decision, Commitment to the **sitemap** (one nav group each); add **Team Member** as a small "Reference data" nav item so you can manage the people list.
3. **Forms:** open each table's main form; arrange the core columns top-to-bottom (Copilot/default form is fine).
4. **Views** — create these (they reproduce the derived flags as filters):
   - Commitments → **Overdue** = Commitment Status not in (Done, Cancelled) AND Due Date is before Today.
   - Commitments → **Ownerless** = Owner does not contain data AND Commitment Status not in (Done, Cancelled).
   - Commitments → **Slipping** = Times Postponed ≥ 2 AND Commitment Status not in (Done, Cancelled).
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

- Gallery with filter buttons: **All · My commitments · Open · Overdue**. "My commitments" uses a Team Member dropdown `cmbMe`: `Filter(Commitments, Owner = cmbMe.Selected)` (compares the lookup record directly, not the display name). Color due date red when overdue.
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

## Track C — Power Automate reminder flow (Day 6, make it useful)

1. In the solution: **New → Automation → Cloud flow → Scheduled cloud flow.**
2. **Trigger:** Recurrence — Interval `1`, Frequency `Day`, at a fixed time (e.g. 8:00 AM).
3. **List rows** (Dataverse) on **Commitments**, filter:
   `Commitment Status ne 'Done' and Commitment Status ne 'Cancelled' and Due Date lt {utcNow()}`
   (mirrors the **Is Overdue** logic in 02-DATA-MODEL.md — keep the flow and the apps' derived flags consistent).
4. **Filter array** to drop rows with no Owner (ownerless commitments have no recipient; they still surface via the canvas Follow-up Radar).
5. **Apply to each** overdue commitment → **Get a row by ID** (Dataverse) on **Team Member** using the Owner lookup, to read their **Email**.
6. Group by Owner (or just send one email per commitment for simplicity — see note below) and **Send an email (V2)** (Office 365 Outlook connector):
   - To: the Team Member's Email (fictional/dummy address).
   - Subject: "You have an overdue commitment: {Commitment Title}".
   - Body: Commitment Title, Due Date, and a link/reference back to the record.
7. **Save** and **Run now** to test against the sample data (04-SAMPLE-DATA.md) — confirm only the seeded overdue commitments trigger an email, sent to their dummy address.
8. **Turn on** the flow.

> **Keep it simple for the demo:** one email per overdue commitment (not batched into a
> single digest per owner) is fine and far less flow logic. Batch-by-owner only if you
> have time to spare.

> **AYA guardrail:** only use fictional/dummy addresses in Team Member.Email (see
> 06-AYA-ASSESSMENT.md). Never point this flow at real employee inboxes for the demo.

---

## Package & test (Day 7)

- Confirm both apps **and** the flow are inside the **one solution**.
- Create a record in the model-driven app → verify it appears in the canvas app (same data proof).
- Walk the demo script; confirm Radar/KPIs match the sample data (04-SAMPLE-DATA.md).
- Run the reminder flow once more; confirm the sample overdue commitments each produced one email to their dummy address.

## Demo script (5 minutes)

1. Canvas **Home dashboard** — Overdue and "Decisions due for review" tiles.
2. Open a **meeting** → decisions + commitments captured together.
3. Open a **decision** → rationale + options; filter Decisions to **Reversed**.
4. **Follow-up Radar** → Overdue / Ownerless / Slipping.
5. **Postpone** a commitment → Times Postponed increments → it appears under Slipping.
6. Switch to the **model-driven app** → "same data, a fast admin view" (create/edit a record live).
7. Show the **Power Automate flow run history** → "this already emailed the overdue owners this morning."

---

## §Deferred — NOT in this phase (keep it simple)

Explicitly out of scope for the demo; add later only if the client validates:

- AI note summarizer (Copilot/AI Builder)
- Extra fields (Priority, Confidence, Impact Area, Commitment Type, Notes)
- Approvals, Teams/Outlook sync, role-based views, trend analytics

Re-run the AYA form before building any of these — several would raise the app's scoring.
