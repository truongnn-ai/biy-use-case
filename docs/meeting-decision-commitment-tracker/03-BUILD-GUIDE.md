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

### A.1 Create the app shell

1. Open your solution (**Meeting Decision & Commitment Tracker**) in make.powerapps.com.
2. Command bar → **New** → **App** → **Model-driven app**.
3. In the **New model-driven app** dialog, enter **Name** (e.g. `MDC Tracker – Admin`), leave **Description** blank, select **Create**.
4. The app designer opens with three panes: **Pages** (left — the sitemap tree), the **preview** (center), and **Properties** (right). Everything below happens from the Pages pane and the command bar above it.

### A.2 Add the four tables to navigation

Repeat for **Meeting**, **Decision**, **Commitment**, then **Team Member**:

1. Command bar → **Add page** → **Dataverse table**.
2. Tick the table → **Next**.
3. Accept the default **Form** (Main/Information) and **Views** (Active, All) selections → **Add**.
4. The table appears in the Pages tree as its own group, with **Views** and **Forms** underneath it.

Once all four are added:

5. Reorder the groups so **Meeting**, **Decision**, **Commitment** come first: select a group in the Pages tree and drag it, or use its **⋯** menu → **Move up** / **Move down**.
6. Make **Team Member** read as reference data rather than a primary work area: select the Team Member group → the rename (pencil) icon → change the group's display label to **Reference Data**. (This only relabels the nav group — the underlying table is unchanged.)

### A.3 Check (and optionally tidy) the forms

1. In the Pages tree, expand **Commitment** → **Forms** → select the main form to preview it in the center pane.
2. The Copilot-generated default form already lists every column — that's good enough for the demo as-is.
3. Optional polish: select the form → **Edit** → drag fields into a top-to-bottom order such as Commitment Title, Owner, Due Date, Commitment Status, Times Postponed, Description → **Save** → **Publish**.
4. Repeat for Decision and Meeting only if time allows — this step is not required for a working app.

### A.4 Create the five custom views

Views live under each table → **Views** in the Pages tree.

1. Table → **Views** → **+ New view** → name it exactly as in the table below (so it matches the demo script and the checklist).
2. Open **Edit filters** → **+ New condition** (or **+ New group** when you need to mix AND/OR) → pick the **column**, the **operator**, and the **value**.
3. **Save**, then **Publish** (you can publish once at the end, after all five views are built).

| View | Table | Conditions (joined with AND unless noted) |
|---|---|---|
| **Overdue** | Commitment | Commitment Status **Does Not Equal** Done **AND** Does Not Equal Cancelled **AND** Due Date **Before** Today |
| **Ownerless** | Commitment | Owner **Does Not Contain Data** **AND** Commitment Status **Does Not Equal** Done **AND** Does Not Equal Cancelled |
| **Slipping** | Commitment | Times Postponed **Greater Than or Equal** `2` **AND** Commitment Status **Does Not Equal** Done **AND** Does Not Equal Cancelled |
| **Due for review** | Decision | Decision Status **Equals** Decided **AND** Review Date **On or Before** Today |
| **Reversed / Superseded** | Decision | Decision Status **Equals** Reversed **OR** Decision Status **Equals** Superseded — put both in one **OR** group (**+ New group**, set the group's join to **Or**) |

> The exact date-operator label can vary slightly by environment version — look for **Before** (strictly earlier than today). If your filter builder only offers **On or Before**, that's an acceptable substitute for a demo (it also counts anything due today as overdue, which is a minor difference).

### A.5 Optional: add a chart

1. Table → **Commitment** → **Charts** → **+ New chart**.
2. Chart type **Bar** → **Series**: Count of records → **Group by**: Commitment Status → **Save**.
3. No further wiring needed — it surfaces automatically as a visual pane on the Commitment grid page.

### A.6 Preview, save, publish

1. Command bar → **Save**.
2. Command bar → **Publish**.
3. Command bar → **Play** → click through Meeting → Decision → Commitment → Reference Data. For Commitment and Decision, use the view-picker dropdown at the top-left of the grid to confirm all five custom views load and return the expected rows from 04-SAMPLE-DATA.md.

You now have a complete, usable app as your safety net before touching the canvas app.

---

## Track B — Canvas app (Days 4–5, the demo showpiece)

### B.1 Create the app shell

1. Inside the solution → **New** → **App** → **Canvas app**.
2. Name it (e.g. `MDC Tracker – Canvas`), format **Tablet** → **Create**.
3. In Power Apps Studio: **View** tab → **Data sources** → **+ Add data** → search **Dataverse** → add **Meetings**, **Decisions**, **Commitments**, **Team Members** (Team Members is needed later for the "My commitments" filter and the Postpone step).
4. In the **Screens** panel, rename the default screen to `scrHome`. Add screens (**New screen** → **Blank**) named `scrMeetings`, `scrMeetingDetail`, `scrDecisions`, `scrDecisionDetail`, `scrCommitments`, `scrCommitmentDetail`, `scrRadar`.
5. **File** → **Save** early and often as you build.

### B.2 Screen 1 — Home / Dashboard (KPI tiles)

1. On `scrHome`, insert 5 rectangles (or blank containers), each holding one **Label** for the number and one **Label** for the caption underneath (e.g. "Overdue").
2. Select each number label and paste its formula into the **Text** property:

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

3. Insert 4 **Icon** or **Button** controls in a nav bar at the top: Meetings, Decisions, Commitments, Follow-up Radar. Set each **OnSelect**:
   - `Navigate(scrMeetings, ScreenTransition.Fade)`
   - `Navigate(scrDecisions, ScreenTransition.Fade)`
   - `Navigate(scrCommitments, ScreenTransition.Fade)`
   - `Navigate(scrRadar, ScreenTransition.Fade)`
4. Press **F5** (Preview) and confirm each tile's number matches what you'd expect from 04-SAMPLE-DATA.md, and each nav button switches screens.

### B.3 Screen — Meetings + Meeting detail

1. Build `scrMeetingDetail` first (the target before the link to it): insert a **Form** control, rename it `frmMeeting`, set **Data source** = `Meetings`.
2. Add two **Vertical galleries** below it:
   - `galMeetingDecisions` → **Items**: `Filter(Decisions, Meeting = varSelectedMeeting)`
   - `galMeetingCommitments` → **Items**: `Filter(Commitments, Meeting = varSelectedMeeting)`
3. Add a **Back** icon → **OnSelect**: `Navigate(scrMeetings, ScreenTransition.Fade)`.
4. `scrMeetings`: insert a **Vertical gallery** `galMeetings` (layout: Title + subtitle), **Items**:
   `Search(Meetings, txtSearchMeetings.Text, "MeetingName")`
5. Above the gallery, add a **Text input** `txtSearchMeetings` and a **Dropdown** `ddMeetingType` with **Items** = `Choices(Meetings.MeetingType)`. Update the gallery **Items** to combine both filters:
   `Filter(Search(Meetings, txtSearchMeetings.Text, "MeetingName"), ddMeetingType.Selected.Value = MeetingType.Value || IsBlank(ddMeetingType.Selected))`
6. Set the gallery template's **OnSelect**: `Set(varSelectedMeeting, ThisItem); EditForm(frmMeeting); Navigate(scrMeetingDetail, ScreenTransition.Fade)`.
7. Add a **+ New meeting** button → **OnSelect**: `NewForm(frmMeeting); Navigate(scrMeetingDetail, ScreenTransition.Fade)`.

### B.4 Screen — Decisions + Decision detail

1. `scrDecisionDetail`: **Form** `frmDecision`, **Data source** = `Decisions`; add a **Back** icon (`Navigate(scrDecisions, ScreenTransition.Fade)`); add an **Add commitment** button → **OnSelect**: `Set(varPrefillMeeting, varSelectedDecision.Meeting); Set(varPrefillDecision, varSelectedDecision); NewForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)` — on `scrCommitmentDetail`, default the Commitment form's Meeting and Related Decision fields from `varPrefillMeeting` / `varPrefillDecision` while the form is in New mode.
2. `scrDecisions`: **Vertical gallery** `galDecisions`, **Items**:
   `Search(Decisions, txtSearchDecisions.Text, "DecisionTitle")`
3. Add filter chips for each Decision Status (include a standalone **Reversed** chip — the differentiator). Each chip's **OnSelect** sets a variable, e.g. `Set(varStatusFilter, "Reversed")`; an **All** chip sets `Set(varStatusFilter, "")`. Update the gallery **Items**:
   `Filter(Search(Decisions, txtSearchDecisions.Text, "DecisionTitle"), varStatusFilter = "" || DecisionStatus.Value = varStatusFilter)`
4. **Timeline**: reuse the same gallery, wrap **Items** in `SortByColumns(..., "DecisionDate", Descending)`, and add a colored status tag — a small label whose **Fill** is `Switch(ThisItem.DecisionStatus.Value, "Decided", Color.Green, "Reversed", Color.Red, "Superseded", Color.Orange, Color.Gray)`.
5. Gallery template **OnSelect**: `Set(varSelectedDecision, ThisItem); EditForm(frmDecision); Navigate(scrDecisionDetail, ScreenTransition.Fade)`.

### B.5 Screen — Commitments + Commitment detail

1. `scrCommitmentDetail`: **Form** `frmCommitment`, **Data source** = `Commitments`; add a **Back** icon.
2. Add a **Postpone** section: a **Date picker** `dtpNewDueDate` and a **Postpone** button → **OnSelect**:
   ```
   Patch(Commitments, varSelectedCommitment, {
       'Original Due Date': If(IsBlank(varSelectedCommitment.'Original Due Date'), varSelectedCommitment.DueDate, varSelectedCommitment.'Original Due Date'),
       DueDate: dtpNewDueDate.SelectedDate,
       'Times Postponed': varSelectedCommitment.'Times Postponed' + 1
   });
   Set(varSelectedCommitment, LookUp(Commitments, Commitment = varSelectedCommitment.Commitment))
   ```
   (the trailing `Set` refreshes the local variable so the form and labels reflect the new values immediately — this follows the Postpone logic in 02-DATA-MODEL.md).
3. `scrCommitments`: **Vertical gallery** `galCommitments`; filter buttons **All · My commitments · Open · Overdue**, each setting `Set(varCommitmentFilter, "...")`, feeding gallery **Items**:
   ```
   Filter(Commitments,
       Switch(varCommitmentFilter,
           "My", Owner = cmbMe.Selected,
           "Open", !(CommitmentStatus.Value in ["Done","Cancelled"]),
           "Overdue", !(CommitmentStatus.Value in ["Done","Cancelled"]) && !IsBlank(DueDate) && DueDate < Today(),
           true))
   ```
   Add a **Team Member** combo box `cmbMe` (Items = Team Members) above the filter row for "My commitments" — `Owner = cmbMe.Selected` compares the lookup record directly, not the display name.
4. Color the due-date label red when overdue: label **Color** = `If(!(ThisItem.CommitmentStatus.Value in ["Done","Cancelled"]) && ThisItem.DueDate < Today(), Color.Red, Color.Black)`.
5. Gallery template **OnSelect**: `Set(varSelectedCommitment, ThisItem); EditForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)`.

### B.6 Screen — Follow-up Radar (the wow screen)

1. On `scrRadar`, insert three **Vertical galleries** (side by side or stacked), each with a **Label** above it showing a live count badge (`CountRows(...)` using the same filter as the gallery below it).
2. **Overdue** gallery **Items**:
   `Filter(Commitments, !(CommitmentStatus.Value in ["Done","Cancelled"]) && !IsBlank(DueDate) && DueDate < Today())`
3. **Ownerless** gallery **Items**:
   `Filter(Commitments, IsBlank(Owner) && !(CommitmentStatus.Value in ["Done","Cancelled"]))`
4. **Slipping** gallery **Items**:
   `Filter(Commitments, TimesPostponed >= 2 && !(CommitmentStatus.Value in ["Done","Cancelled"]))`
5. Each gallery template's **OnSelect**: `Set(varSelectedCommitment, ThisItem); EditForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)` — tapping any row jumps straight to Commitment detail.
6. End-to-end check: postpone a commitment twice on `scrCommitmentDetail`, navigate back to Radar, confirm it now appears under **Slipping**.

---

## Track C — Power Automate reminder flow (Day 6, make it useful)

### C.1 Create the flow shell

1. Inside the solution → **New** → **Automation** → **Cloud flow** → **Scheduled cloud flow**.
2. Name it `Daily overdue commitment reminder`, set **Starting**: today's date, **Repeat every**: `1` **Day**, at a fixed time (e.g. 08:00) → **Create**.

### C.2 List the overdue commitments

1. **+ New step** → search **Dataverse** → action **List rows**.
2. **Table name**: Commitments.
3. **Filter rows** (OData syntax):
   `Commitment Status ne 'Done' and Commitment Status ne 'Cancelled' and Due Date lt '@{utcNow()}'`
   (mirrors the **Is Overdue** logic in 02-DATA-MODEL.md — keep the flow and the apps' derived flags consistent; if the filter-builder helper shows different schema names for these columns, use those instead).
4. Save now — you'll test the whole flow in C.6 rather than guessing at field names blind.

### C.3 Drop ownerless commitments

1. **+ New step** → **Filter array**.
2. **From**: the `value` output of **List rows**.
3. **Condition**: the Owner lookup field **is not equal to** blank — use the visual picker to select the Owner field from dynamic content if it's offered directly; otherwise use the expression `item()?['_owner_value']` **is not equal to** *(leave the compare value empty)*.

### C.4 Loop through each overdue, owned commitment

1. **+ New step** → **Apply to each** → **Select an output from previous steps**: the Filter array's output.
2. Inside the loop, **+ Add an action** → **Dataverse** → **Get a row by ID**.
3. **Table name**: Team Members. **Row ID**: the current item's Owner lookup value (pick it from dynamic content on the Apply to each item).

### C.5 Send the email

1. Still inside the loop, **+ Add an action** → **Office 365 Outlook** → **Send an email (V2)**.
2. **To**: the **Email** field from the **Get a row by ID** step (dynamic content) — the Team Member's fictional/dummy address.
3. **Subject**: `You have an overdue commitment: ` + dynamic content **Commitment Title** from the Apply to each item.
4. **Body**: Commitment Title and Due Date (dynamic content), plus optionally a plain-text reference back to the record.

### C.6 Test, save, turn on

1. **Save** the flow.
2. **Test** → **Manually** → **Run flow**. Open **Run history** and confirm: one email per seeded overdue commitment in 04-SAMPLE-DATA.md, each sent to its owner's dummy address, and ownerless ones skipped.
3. If a step errors, expand it in the run history — it shows the exact input/output payload, the fastest way to spot a wrong field name or filter.
4. Once a manual run succeeds cleanly, toggle the flow **On** (top of the flow's overview page) so the daily Recurrence trigger takes over.

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
