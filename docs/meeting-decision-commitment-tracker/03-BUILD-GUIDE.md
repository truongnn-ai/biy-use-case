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
| 5 | **Track B** — Commitments + Follow-up Radar; polish/theme | Canvas |
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

> **System "Owner" field gotcha (all four tables):** every Dataverse table auto-generates its own system **Owner** column (`ownerid` — tracks which Dataverse *user/team* administratively owns the row for security purposes). This is unrelated to the **Owner** lookup we designed on Commitment (which points to a Team Member and means "who committed to this"). Copilot-generated forms sometimes surface the system Owner field and mark it required, which blocks saving a new record until you manually pick a user. You **cannot delete it from the form** — Dataverse blocks removing a required column's only occurrence on a form — so instead select it → in the Properties panel check **Hide**, then **Save and publish**. Dataverse still auto-assigns ownership to the creating user behind the scenes; hiding just stops it from blocking you on save.

### A.4 Create the five custom views

Views live under each table → **Views** in the Pages tree.

1. Table → **Views** → **+ New view** → name it exactly as in the table below (so it matches the demo script and the checklist).
2. Open **Edit filters** → **+ New condition** (or **+ New group** when you need to mix AND/OR) → pick the **column**, the **operator**, and the **value**.
3. **Save**, then **Publish** (you can publish once at the end, after all five views are built).

| View | Table | Conditions (joined with AND unless noted) |
|---|---|---|
| **Overdue** | Commitment | Commitment Status **Does Not Equal** Done **AND** Does Not Equal Cancelled **AND** Due Date **Contains Data** **AND** (Due Date **Older Than X Days** `1` **OR** Due Date **Today**) — see tree below |
| **Ownerless** | Commitment | Owner **Does Not Contain Data** **AND** Commitment Status **Does Not Equal** Done **AND** Does Not Equal Cancelled |
| **Slipping** | Commitment | Times Postponed **Greater Than or Equal** `2` **AND** Commitment Status **Does Not Equal** Done **AND** Does Not Equal Cancelled |
| **Due for review** | Decision | Decision Status **Equals** Decided **AND** Review Date **Contains Data** **AND** (Review Date **Older Than X Days** `1` **OR** Review Date **Today**) |
| **Reversed / Superseded** | Decision | Decision Status **Equals** `Reversed / Superseded` — single condition, no OR group needed |

**Filter trees** (build each with **+ New condition** / **+ New group** in **Edit filters** — a `└── OR` line means: add a new group, set its join to **Or**, then add its child conditions inside):

**Overdue** (Commitment)
```
AND
├── Commitment Status | Does Not Equal | Done
├── Commitment Status | Does Not Equal | Cancelled
├── Due Date | Contains data
└── OR
    ├── Due Date | Older than X days | 1
    └── Due Date | Today
```

**Ownerless** (Commitment)
```
AND
├── Owner | Does not contain data
├── Commitment Status | Does Not Equal | Done
└── Commitment Status | Does Not Equal | Cancelled
```

**Slipping** (Commitment)
```
AND
├── Times Postponed | Greater Than or Equal | 2
├── Commitment Status | Does Not Equal | Done
└── Commitment Status | Does Not Equal | Cancelled
```

**Due for review** (Decision)
```
AND
├── Decision Status | Equals | Decided
├── Review Date | Contains data
└── OR
    ├── Review Date | Older than X days | 1
    └── Review Date | Today
```

**Reversed / Superseded** (Decision)
```
Decision Status | Equals | Reversed / Superseded
```

> **Why Overdue/Due for review use the Contains-data + OR shape, not a plain "Before Today":** this filter builder has no literal Before operator. **On** / **On or Before** / **On or After** pair with a **fixed calendar date** you pick once, so they go stale. **Older Than X Days** is dynamic (re-evaluated on every load) but only accepts **X ≥ 1** — entering `0` throws a validation error. **Today** is a separate dynamic operator that resolves to "equals today." OR'ing them together gives "at least 1 day old, or due today" — i.e. due on or before today — which matches the `'Due Date' < Today()` / `'Review Date' <= Today()` derived flags in 02-DATA-MODEL.md closely enough for the demo (same minor "counts due-today as overdue too" simplification called out there). **Contains data** guards against blank Due/Review Dates, since both columns are optional.

> **What clears a decision out of "Due for review":** the filter only matches `Decision Status = Decided`, so any status change removes it immediately — no need to fiddle with Review Date. When someone actually reviews a decision, they set its status to either **Reviewed** (still holds — done, no further action) or **Reversed / Superseded** (changed). Only if they want it to resurface again later do they leave it **Decided** and push Review Date to a new future date.

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

Canvas is 1366×768 (Tablet, landscape) by default — the coordinates below assume that; adjust proportionally if you picked a different size. Every screen shares the same top-left **Back** icon pattern and the same nav bar from `scrHome`, so build `scrHome` first.

> **Field-name gotcha:** Dataverse column **display names that contain a space** — `Commitment Status`, `Due Date`, `Decision Status`, `Review Date`, `Decision Date`, `Meeting Type`, `Times Postponed`, `Original Due Date` — must be wrapped in **single quotes** when referenced in a Power Fx formula, e.g. `'Commitment Status'`, not `CommitmentStatus`. Every formula below already does this. If Studio still throws **"Name isn't valid. 'X' isn't recognized"**, open the **Data** pane (left sidebar) → click **Commitments**/**Decisions**/**Meetings** to see the exact column names Power Apps recognizes, or just start typing inside the `Filter(...)` and let IntelliSense show you the real name — your environment's publisher/Copilot generation can occasionally rename a column slightly differently than the table in 02-DATA-MODEL.md.
>
> **Choice-column gotcha:** **Commitment Status** and **Decision Status** are Choice (option set) columns. Depending on your environment's Dataverse connector version, the classic `'Commitment Status'.Value` syntax can throw **"Name isn't valid. 'Value' isn't recognized."** The formulas below use `Text('Commitment Status')` instead — wrapping a Choice column in `Text()` reliably returns its display string (`"Done"`, `"Cancelled"`, etc.) across connector versions. Expect a yellow **delegation warning** on these formulas (`Text()` isn't delegable) — harmless at this demo's small data scale (04-SAMPLE-DATA.md), so ignore it.

### B.1 Create the app shell

1. Inside the solution → **New** → **App** → **Canvas app**.
2. Name it (e.g. `MDC Tracker – Canvas`), format **Tablet** → **Create**.
3. In Power Apps Studio: command bar → **Add data** (or the **connect to data** link in the middle of the blank canvas) → search **Dataverse** → add **Meetings**, **Decisions**, **Commitments**, **Team Members** (Team Members is needed later for the "My commitments" filter). Older Studio versions nest this under a **View** tab → **Data sources**; current Studio surfaces **Add data** directly in the command bar.
4. In the **Tree view** (left panel, **Screens** tab), double-click the default screen's name and rename it `scrHome`.
5. Click **New screen** in the command bar → choose **Blank** (not one of the header/scrollable templates — you want an empty canvas each time) → repeat 7 times, naming them in the Tree view as you go: `scrMeetings`, `scrMeetingDetail`, `scrDecisions`, `scrDecisionDetail`, `scrCommitments`, `scrCommitmentDetail`, `scrRadar`.
6. **File** → **Save** now, and again after every screen below.
7. Select **App** in the Tree view → formula bar → **OnStart**, and set:
   `Set(varSelectedMeeting, First(Meetings)); Set(varSelectedDecision, First(Decisions)); Set(varSelectedCommitment, First(Commitments)); Set(varPrefillMeeting, First(Decisions).Meeting); Set(varPrefillDecision, First(Decisions))`
   This pre-declares the session variables used across B.3–B.5 (`galMeetingDecisions`, `galMeetingCommitments`, the detail-screen `OnSelect`/`Patch` formulas, and the commitment prefill logic) so Power Fx recognizes their names — and their record types — right away. Use `First(TableName)` rather than `Blank()`: Power Fx infers a variable's type from the shape of the formula, so `First(Meetings)` types the variable as a `Meetings` record even when the table is empty at runtime (it'll just hold a blank value until something real is `Set()` later), whereas `Blank()` alone has no type and throws "No type found for variable... ensure it is Set to a non-blank value somewhere in the app." Note `varPrefillMeeting` is seeded from `First(Decisions).Meeting` (a lookup-shaped record), not `First(Meetings)` (a full-table record) — it must match the shape it's actually assigned later in B.4 step 3 (`Set(varPrefillMeeting, varSelectedDecision.Meeting)`), otherwise Power Fx will flag the same "incompatible record type" problem on that later `Set()`. If `App.OnStart` doesn't run automatically in Studio, force it once via **App** → **OnStart** → the "run OnStart" prompt, or add a manual **Button** with the same formula temporarily.

### B.2 Screen — Home / Dashboard (KPI tiles)

```
┌────────────────────────────────────────────────────────────────────┐
│  [Meetings]   [Decisions]   [Commitments]   [Follow-up Radar]       │  ← nav bar, y=0, h=80
├────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐  ┌────────┐        │
│  │   12   │  │   4    │  │   7    │  │   2    │  │   3    │        │  ← number label
│  │        │  │        │  │        │  │        │  │        │        │
│  │  Open  │  │Overdue │  │Decisions│ │Due for │  │Reversed│        │  ← caption label
│  │Commit- │  │        │  │this mo. │ │ review │  │/Super. │        │
│  │ ments  │  │        │  │        │  │        │  │        │        │
│  └────────┘  └────────┘  └────────┘  └────────┘  └────────┘        │
│                                                                      │
└────────────────────────────────────────────────────────────────────┘
```

**Nav bar**

1. On `scrHome`, click **Insert** → type `button` in the search box → click **Button**.
2. Properties panel → **Advanced** tab → **Size and position**: `X = 20`, `Y = 0`, `Width = 200`, `Height = 60`.
3. Formula bar: switch the property dropdown (top-left, shows the currently edited property) to **Text** → type `"Meetings"` → Enter.
4. Switch the property dropdown to **OnSelect** → `Navigate(scrMeetings, ScreenTransition.Fade)` → Enter.
5. Tree view → double-click the button's default name (e.g. `Button1`) → rename `btnNavMeetings`.
6. Select it → Ctrl+C → Ctrl+V three times. For each copy, only change `X` (230, 440, 650), `Text` (`"Decisions"`, `"Commitments"`, `"Follow-up Radar"`), `OnSelect` (`Navigate(scrDecisions, ScreenTransition.Fade)`, `Navigate(scrCommitments, ScreenTransition.Fade)`, `Navigate(scrRadar, ScreenTransition.Fade)`), and rename (`btnNavDecisions`, `btnNavCommitments`, `btnNavRadar`).

**One KPI tile (then clone it)**

1. **Insert** → type `rectangle` → click **Rectangle**. Advanced → Size and position: `X = 20`, `Y = 110`, `Width = 245`, `Height = 150`. Display tab → **Fill** → a light card color. Rename `rectTileOpen`.
2. **Insert** → type `label` → click **Text label**. Position inside the rectangle: `X = 20`, `Y = 130`, `Width = 245`, `Height = 60`. If it renders behind the rectangle, drag it lower in the Tree view list (items lower in the tree paint on top). Text tab → Size ≈ 36, Align Center. Formula bar → property dropdown **Text** → paste:
   ```
   CountRows(Filter(Commitments, !(Text('Commitment Status') in ["Done","Cancelled"])))
   ```
   Rename `lblOpenCount`.
3. **Insert** → **Text label** again. Position: `X = 20`, `Y = 190`, `Width = 245`, `Height = 60`. Text = `"Open Commitments"` (plain text). Size ≈ 14, Align Center, gray color. Rename `lblOpenCaption`.
4. Select all three (rectangle + 2 labels) → right-click → **Group**, rename the group `grpTileOpen`.
5. Select `grpTileOpen` → Ctrl+C → Ctrl+V four times. For each copy change only the group's `X` (285, 550, 815, 1080), the number label's **Text** formula, and the caption label's **Text**:

   | Tile | X | Number label formula | Caption |
   |---|---|---|---|
   | Overdue | 285 | `CountRows(Filter(Commitments, !(Text('Commitment Status') in ["Done","Cancelled"]) && !IsBlank('Due Date') && 'Due Date' < Today()))` | `"Overdue"` |
   | Decisions this month | 550 | `CountRows(Filter(Decisions, Year('Decision Date')=Year(Today()) && Month('Decision Date')=Month(Today())))` | `"Decisions this month"` |
   | Decisions due for review | 815 | `CountRows(Filter(Decisions, Text('Decision Status')="Decided" && !IsBlank('Review Date') && 'Review Date' <= Today()))` | `"Decisions due for review"` |
   | Reversed / Superseded | 1080 | `CountRows(Filter(Decisions, Text('Decision Status') = "Reversed / Superseded"))` | `"Reversed / Superseded"` |

   Rename each group (`grpTileOverdue`, `grpTileDecisionsMonth`, `grpTileDueReview`, `grpTileReversed`).
6. Optional: select all 5 tiles → **Arrange** (top command bar, or under its **⋯** overflow) → **Align** → Align Top, then **Distribute** → Distribute Horizontally, to snap them into an even row.
7. Press **F5** (Preview), confirm each tile's number matches what you'd expect from 04-SAMPLE-DATA.md, click each nav button to confirm it switches screens, then **Esc** to exit Preview.

### B.3 Screen — Meetings + Meeting detail

Build `scrMeetingDetail` first — it's the navigation target, so it needs to exist before you wire the list screen's `OnSelect` to it.

```
scrMeetings                                         scrMeetingDetail
┌───────────────────────────────────────┐   ┌───────────────────────────────────────┐
│ [<] Meetings          [+ New meeting]  │   │ [<] Back                      [Save] │
├───────────────────────────────────────┤   ├───────────────┬───────────────────────┤
│ [ Search meetings...  ] [Type:  All v]│   │ frmMeeting     │ Decisions             │
├───────────────────────────────────────┤   │ Meeting Name   │ ┌───────────────────┐ │
│ ┌─────────────────────────────────┐   │   │ Meeting Date   │ │galMeetingDecisions│ │
│ │ Weekly Ops Sync       2026-07-14│   │   │ Meeting Type   │ └───────────────────┘ │
│ │ Product Roadmap Rev.  2026-07-10│   │   │                │ Commitments           │
│ │ ...  (galMeetings)              │   │   │                │ ┌───────────────────┐ │
│ └─────────────────────────────────┘   │   │                │ │galMeetingCommit-  │ │
└───────────────────────────────────────┘   │                │ │ments              │ │
                                             │                │ └───────────────────┘ │
                                             └───────────────┴───────────────────────┘
```

1. On `scrMeetingDetail`: **Insert** → type `edit form` → click **Edit form**. Advanced → Size and position: `X = 20`, `Y = 20`, `Width = 400`, `Height = 600`. In the Properties panel (right side), set **Data source** = `Meetings`. Rename `frmMeeting`. Formula bar → **Item**: `varSelectedMeeting`.
   **Don't skip this:** `EditForm(frmMeeting)` (used in step 8 below) only switches the form into Edit *mode* — it does **not** pick which record to show. That's the form's separate `Item` property. Without setting it, the form renders "No item to display" even though the related Decisions/Commitments galleries (which filter on `varSelectedMeeting` directly) work fine.
   **System state/status field gotcha (all Canvas Edit forms — `frmMeeting`, `frmDecision`, `frmCommitment`):** every Dataverse table also auto-generates system-managed **Status** (`statecode`) and **Status Reason** (`statuscode`) columns — distinct from any business "status" column you designed (e.g. `Commitment Status`, `Decision Status`). Copilot's default field list often adds these two to the form automatically. Submitting the form with them present throws **"Column 'statecode' is generated by the server and can't be specified"**, because the server assigns that value and rejects any value the client sends. Setting the card's `Visible = false` does **not** fix it — an Edit form still includes hidden-but-present cards in what `SubmitForm` writes. The fix is to remove the field from the form entirely: select the form → right panel **Fields** → **Edit fields** → remove **Status** and **Status Reason** from the list → **Save** → **Publish**.
2. **Insert** → type `gallery` → pick a **Vertical gallery** layout (e.g. "Title, subtitle"). Position it to the right of the form: `X = 440`, `Y = 60`, `Width = 900`, `Height = 280`. Formula bar → **Items**:
   `Filter(Decisions, Meeting.'Meeting Name' = varSelectedMeeting.'Meeting Name')`
   Rename `galMeetingDecisions`. Add a label above it with Text `"Decisions from this meeting"`.
   **Why not `Meeting = varSelectedMeeting`:** a Lookup column (`Meeting` on Decisions) and a full-table record (`varSelectedMeeting`, a Meetings row) are different record shapes even though they both "point at" Meetings — comparing them with `=` throws **"Incompatible types for comparison. Record, Record."** Compare the primary name column instead (`'Meeting Name'`, guaranteed present on both sides) — this is Microsoft's documented pattern for filtering by a Dataverse lookup. The same fix applies anywhere below that compares a lookup column to a variable/selected record.
3. **Insert** another **Vertical gallery** below it: `X = 440`, `Y = 380`, `Width = 900`, `Height = 280`. **Items**:
   `Filter(Commitments, Meeting.'Meeting Name' = varSelectedMeeting.'Meeting Name')`
   Rename `galMeetingCommitments`. Add a label above it with Text `"Commitments from this meeting"`.
4. **Insert** → type `icon` → pick the **Back arrow** icon. Position top-left: `X = 20`, `Y = 20`, `Width = 40`, `Height = 40`. **OnSelect**: `Navigate(scrMeetings, ScreenTransition.Fade)`.
5. **Insert** → **Button**, top-right: `X = 1150`, `Y = 20`, `Width = 150`, `Height = 50`. Text = `"Save"`. **OnSelect**: `SubmitForm(frmMeeting)`.
   This is the step that actually creates/updates the record — without it, `frmMeeting` just sits in New/Edit mode holding unsaved input and there is no way to persist a new meeting.
   Select `frmMeeting` → formula bar → **OnSuccess**:
   `Set(varSelectedMeeting, frmMeeting.LastSubmit); Navigate(scrMeetings, ScreenTransition.Fade)`
   `frmMeeting.LastSubmit` is the just-saved record (with its new ID populated) — reassigning `varSelectedMeeting` to it keeps the variable in sync in case the user reopens the detail screen, then the app returns to the list so the new meeting is visible in `galMeetings`. Optional: add an **OnError** on the form (e.g. a label showing `frmMeeting.Error`) so a failed save isn't silent.
6. On `scrMeetings`: **Insert** → type `text input` → click **Text input**, position `X = 20`, `Y = 70`, `Width = 500`, `Height = 40`, rename `txtSearchMeetings`. **Insert** → type `drop down` → click **Drop down**, position `X = 540`, `Y = 70`, `Width = 250`, `Height = 40`, rename `ddMeetingType`, set **Items** = `Choices(Meetings.'Meeting Type')`.
7. **Insert** → **Vertical gallery** (layout: Title + subtitle). Position: `X = 20`, `Y = 140`, `Width = 1326`, `Height = 580`. Rename `galMeetings`. **Items**:
   `Filter(Search(Meetings, txtSearchMeetings.Text, 'Meeting Name'), Text(ddMeetingType.Selected.Value) = Text('Meeting Type') || IsBlank(ddMeetingType.Selected))`
   Build the search box and dropdown before the gallery — the gallery's `Items` formula references both controls by name, and Studio throws **"Name isn't valid... isn't recognized"** if you set it before they exist.
   **Quoting note:** `Search()`'s column argument is a **field reference**, not a string literal — use single quotes (`'Meeting Name'`), not double quotes (`"Meeting Name"`). Double-quoting it is what throws **"Expected identifier name"** (Power Fx sees a text literal where it expects a column identifier).
   **Choice-column note:** `ddMeetingType.Selected.Value` is an `OptionSetValue`, not plain text — comparing it directly to `Text('Meeting Type')` throws **"Incompatible types for comparison... OptionSetValue, Text."** Wrap it in `Text(...)` too, same as the `Commitment Status`/`Decision Status` comparisons elsewhere in this guide.
8. Select `galMeetings`'s template (click once on the gallery, then again on the first row to select the template) → formula bar → **OnSelect**:
   `Set(varSelectedMeeting, ThisItem); EditForm(frmMeeting); Navigate(scrMeetingDetail, ScreenTransition.Fade)`
9. **Insert** → **Button**, top-right: `X = 1150`, `Y = 20`, `Width = 196`, `Height = 50`. Text = `"+ New meeting"`. **OnSelect**:
   `Set(varSelectedMeeting, Defaults(Meetings)); NewForm(frmMeeting); Navigate(scrMeetingDetail, ScreenTransition.Fade)`
   The `Set(varSelectedMeeting, Defaults(Meetings))` matters even though `NewForm` ignores the form's `Item` — `galMeetingDecisions`/`galMeetingCommitments` filter on `varSelectedMeeting` directly, not on the form. Without resetting it, those galleries keep showing the previously selected meeting's decisions/commitments on a brand-new (unsaved) meeting. `Defaults(Meetings)` gives a correctly-typed blank Meetings record that won't match any real `Meeting.'Meeting Name'`, so both galleries render empty until the new meeting is saved and actually selected.

### B.4 Screen — Decisions + Decision detail

```
scrDecisions                                        scrDecisionDetail
┌───────────────────────────────────────┐   ┌───────────────────────────────────────┐
│ [<] Decisions                         │   │ [<] Back  [+ Add commitment]  [Save]  │
├───────────────────────────────────────┤   ├───────────────────────────────────────┤
│ [ Search decisions...           ]     │   │ frmDecision                            │
│ (All)(Proposed)(Decided)(Reviewed)    │   │  Decision Title:  ...                  │
│ (Reversed / Superseded)               │   │  Rationale / Options: ...              │
├───────────────────────────────────────┤   │  Decision Status: ...                  │
│ ┌─────────────────────────────────┐   │   │  Review Date: ...                      │
│ │● Adopt new CRM vendor  [Decided]│   │   └───────────────────────────────────────┘
│ │  2026-07-12                     │   │
│ │● Freeze feature X   [Reversed]  │   │
│ │  2026-06-30 (galDecisions)      │   │
│ └─────────────────────────────────┘   │
└───────────────────────────────────────┘
```

1. On `scrDecisionDetail`: **Insert** → **Edit form**, `X = 20`, `Y = 20`, `Width = 900`, `Height = 650`, **Data source** = `Decisions`, rename `frmDecision`. Formula bar → **Item**: `varSelectedDecision` (same reason as `frmMeeting` in B.3 step 1 — `EditForm()` sets mode, not which record).
   **Field cleanup (same as B.3):** select `frmDecision` → right panel **Fields** → **Edit fields** → remove the auto-added system **Status** (`statecode`) and **Status Reason** (`statuscode`) fields — these are Dataverse-generated and distinct from the business **Decision Status** column you designed; leaving them in throws **"Column 'statecode' is generated by the server and can't be specified"** on Save. While you're there, also remove any other system/plumbing fields Copilot added (e.g. Record Created On, Import Sequence Number, Time Zone Rule Version Number) that aren't in 02-DATA-MODEL.md's Decision column list.
2. **Insert** → **Back arrow** icon, `X = 20`, `Y = 20` (in front of the form — nudge the form down to `Y = 90` if it overlaps), **OnSelect**: `Navigate(scrDecisions, ScreenTransition.Fade)`.
3. **Insert** → **Button**, top-right: `X = 1150`, `Y = 20`, `Width = 150`, `Height = 50`. Text = `"Save"`. **OnSelect**: `SubmitForm(frmDecision)`.
   Select `frmDecision` → formula bar → **OnSuccess**:
   `Set(varSelectedDecision, frmDecision.LastSubmit); Navigate(scrDecisions, ScreenTransition.Fade)`
   Same pattern as `frmMeeting` in B.3 — without this, a new decision's fields are never actually persisted.
4. **Insert** → **Button**, top-right (left of Save): `X = 950`, `Y = 20`, `Width = 180`, `Height = 50`. Text = `"+ Add commitment"`. **OnSelect**:
   `Set(varPrefillMeeting, varSelectedDecision.Meeting); Set(varPrefillDecision, varSelectedDecision); NewForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)`
   **Build-order dependency:** this formula references `frmCommitment`, the Edit form built in **B.5 step 1** on `scrCommitmentDetail` — if you're building strictly in order, Studio will throw **"Name isn't valid. 'frmCommitment' isn't recognized"** because that control doesn't exist yet. Jump ahead and do just B.5 step 1 (insert the Edit form on `scrCommitmentDetail`, set **Data source** = `Commitments`, rename it `frmCommitment`) before finishing this OnSelect, then return here — or skip this button for now and wire it after you've completed B.5 in full.
   On `scrCommitmentDetail`, default the Commitment form's Meeting and Related Decision fields from `varPrefillMeeting` / `varPrefillDecision` while the form is in New mode (set each field card's **Default** property, e.g. `varPrefillMeeting`, only used when `frmCommitment.Mode = FormMode.New`).
5. On `scrDecisions`: **Insert** → **Text input** `txtSearchDecisions` (`X = 20`, `Y = 70`).
6. Add 5 filter chips below the search box: **Insert** → **Button**, all at `Y = 120`, `Height = 50`, one per row below (the last chip is wider since its label is longer). For each: set **X**, **Width**, **Text**, **OnSelect** as shown, then rename it in the Tree view.

   | Chip | X | Width | Text | OnSelect | Rename |
   |---|---|---|---|---|---|
   | 1 | 20 | 150 | `"All"` | `Set(varStatusFilter, "")` | `btnFilterAll` |
   | 2 | 180 | 150 | `"Proposed"` | `Set(varStatusFilter, "Proposed")` | `btnFilterProposed` |
   | 3 | 340 | 150 | `"Decided"` | `Set(varStatusFilter, "Decided")` | `btnFilterDecided` |
   | 4 | 500 | 150 | `"Reviewed"` | `Set(varStatusFilter, "Reviewed")` | `btnFilterReviewed` |
   | 5 | 660 | 220 | `"Reversed / Superseded"` | `Set(varStatusFilter, "Reversed / Superseded")` | `btnFilterReversed` |

   Easiest build: create chip 1, set its `X`/`Width`/`Text`/`OnSelect`/rename, then Ctrl+C → Ctrl+V four times and only change those same four properties on each copy. Chip 5 is the differentiator (matches the model-driven app's **Reversed / Superseded** view) — keep it standalone rather than folding it into "All". `varStatusFilter` starts blank/uninitialized until a chip is clicked, which is fine: the gallery's `Items` formula in step 7 already treats blank the same as `""` (shows all decisions) until the user picks a chip.
7. **Insert** → **Vertical gallery**, `X = 20`, `Y = 190`, `Width = 1326`, `Height = 530`. Rename `galDecisions`. **Items**:
   `Filter(Search(Decisions, txtSearchDecisions.Text, 'Decision Title'), varStatusFilter = "" || Text('Decision Status') = varStatusFilter)`
   Build the search box and filter chips before the gallery — its `Items` formula references both `txtSearchDecisions` and `varStatusFilter` by name.
8. **Timeline styling**: reuse the same gallery — wrap **Items** in `SortByColumns(..., "Decision Date", Descending)`. Then add a color dot inside the gallery's template: click `galDecisions` once to select the gallery, then click again directly on its **first row** to select the template (not the gallery container) — with the template focused, **Insert** → **Icon** (a filled circle) or **Shape** places the new control nested inside the template. Only then does it get its own `ThisItem` context. Set its **Fill**:
   `Switch(Text(ThisItem.'Decision Status'), "Decided", Color.Green, "Reviewed", Color.Blue, "Reversed / Superseded", Color.Red, Color.Gray)`
   **If you get "Name isn't valid. 'ThisItem' isn't recognized":** the shape/label landed outside the gallery instead of inside its template — check the Tree view; it should be nested *under* `galDecisions`, not a sibling of it. If it's a sibling, cut it (Ctrl+X), click into the gallery's template (as above), then paste (Ctrl+V) to re-parent it inside.
9. Select the gallery template → **OnSelect**:
   `Set(varSelectedDecision, ThisItem); EditForm(frmDecision); Navigate(scrDecisionDetail, ScreenTransition.Fade)`

### B.5 Screen — Commitments + Commitment detail

```
scrCommitments                                      scrCommitmentDetail
┌───────────────────────────────────────┐   ┌───────────────────────────────────────┐
│ [<] Commitments      [+ New commitment]│   │ [<] Back                      [Save] │
├───────────────────────────────────────┤   ├───────────────────────────────────────┤
│ Me: [ cmbMe: pick team member    v]   │   │ frmCommitment                          │
│ (All)(My commitments)(Open)(Overdue)  │   │  Commitment Title: ...                 │
├───────────────────────────────────────┤   │  Owner: ...                            │
│ ┌─────────────────────────────────┐   │   │  Due Date: ...                         │
│ │ Ship v2 API docs   Due 07-15(red)│  │   │  Commitment Status: ...                │
│ │ Owner: Jane D.                   │   │   │  Times Postponed: ...                  │
│ │ Finalize vendor bud. Due 07-20   │   │   └───────────────────────────────────────┘
│ │ Owner: (none)  (galCommitments)  │   │
│ └─────────────────────────────────┘   │
└───────────────────────────────────────┘
```

1. On `scrCommitmentDetail`: **Insert** → **Edit form**, `X = 20`, `Y = 90`, `Width = 900`, `Height = 500`, **Data source** = `Commitments`, rename `frmCommitment`. Formula bar → **Item**: `varSelectedCommitment` (same reason as `frmMeeting` in B.3 step 1 — `EditForm()` sets mode, not which record). **Insert** → **Back arrow** icon at `X = 20, Y = 20` → **OnSelect**: `Navigate(scrCommitments, ScreenTransition.Fade)`.
   **Field cleanup (same as B.3):** select `frmCommitment` → right panel **Fields** → **Edit fields** → remove the auto-added system **Status** (`statecode`) and **Status Reason** (`statuscode`) fields — distinct from the business **Commitment Status** column you designed; leaving them in throws **"Column 'statecode' is generated by the server and can't be specified"** on Save. Also remove any other system/plumbing fields Copilot added (e.g. Record Created On, Import Sequence Number, Time Zone Rule Version Number) that aren't in 02-DATA-MODEL.md's Commitment column list.
2. **Insert** → **Button**, top-right: `X = 1150`, `Y = 20`, `Width = 150`, `Height = 50`. Text = `"Save"`. **OnSelect**: `SubmitForm(frmCommitment)`.
   Select `frmCommitment` → formula bar → **OnSuccess**:
   `Set(varSelectedCommitment, frmCommitment.LastSubmit); Navigate(scrCommitments, ScreenTransition.Fade)`
   Same pattern as `frmMeeting` in B.3 — without this, edits made on this form (and new commitments created via "+ Add commitment" from Decision detail, or "+ New commitment" below) are never persisted.
3. On `scrCommitments`: **Insert** → type `combo box` → click **Combo box**, `X = 20`, `Y = 70`, `Width = 400`, rename `cmbMe`, **Items** = `Team Members` (needed for "My commitments" below).
4. Below it, add filter chips (buttons) **All · My commitments · Open · Overdue**, `Y = 130`, each setting `Set(varCommitmentFilter, "...")` in its **OnSelect** (e.g. `Set(varCommitmentFilter, "My")`).
5. **Insert** → **Vertical gallery**, `X = 20`, `Y = 190`, `Width = 1326`, `Height = 530`, rename `galCommitments`. **Items**:
   ```
   Filter(Commitments,
       Switch(varCommitmentFilter,
           "My", Owner.'Team Member Name' = cmbMe.Selected.'Team Member Name',
           "Open", !(Text('Commitment Status') in ["Done","Cancelled"]),
           "Overdue", !(Text('Commitment Status') in ["Done","Cancelled"]) && !IsBlank('Due Date') && 'Due Date' < Today(),
           true))
   ```
   `Owner.'Team Member Name' = cmbMe.Selected.'Team Member Name'` compares the primary name column on both sides — the same fix as the `Meeting` lookup comparisons in B.3, needed because `Owner` (a lookup) and `cmbMe.Selected` (a full Team Members record) are different record shapes and can't be compared directly with `=`.
6. Inside the gallery template, select the due-date label → **Color**:
   `If(!(Text(ThisItem.'Commitment Status') in ["Done","Cancelled"]) && ThisItem.'Due Date' < Today(), Color.Red, Color.Black)`
7. Select the gallery template → **OnSelect**:
   `Set(varSelectedCommitment, ThisItem); EditForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)`
8. **Insert** → **Button**, top-right: `X = 1150`, `Y = 20`, `Width = 210`, `Height = 50`. Text = `"+ New commitment"`. **OnSelect**:
   `Set(varSelectedCommitment, Defaults(Commitments)); Set(varPrefillMeeting, Defaults(Meetings)); Set(varPrefillDecision, Defaults(Decisions)); NewForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)`
   Same reasoning as `scrMeetings`' "+ New meeting" button in B.3 — resets `varSelectedCommitment` so the detail screen doesn't show stale data from whatever was last selected, and clears the prefill variables so a commitment created directly from this screen (not via "+ Add commitment" on a Decision) doesn't inherit the previous Meeting/Decision prefill.

### B.6 Screen — Follow-up Radar (the wow screen)

```
┌──────────────────────────────────────────────────────────────────────┐
│ [<] Follow-up Radar                                                   │
├─────────────────────┬─────────────────────┬───────────────────────────┤
│ Overdue (7)          │ Ownerless (3)       │ Slipping (2)              │
│ ┌─────────────────┐  │ ┌─────────────────┐ │ ┌───────────────────────┐ │
│ │galRadarOverdue   │  │ │galRadarOwnerless│ │ │galRadarSlipping        │ │
│ │ row · row · row  │  │ │ row · row       │ │ │ row · row              │ │
│ └─────────────────┘  │ └─────────────────┘ │ └───────────────────────┘ │
└─────────────────────┴─────────────────────┴───────────────────────────┘
```

1. On `scrRadar`, add a label above each of the three columns showing a live count badge, using the same filter as the gallery beneath it, e.g. `"Overdue (" & CountRows(Filter(Commitments, ...)) & ")"`.
2. **Insert** → **Vertical gallery**, left column: `X = 20`, `Y = 70`, `Width = 430`, `Height = 650`. Rename `galRadarOverdue`. **Items**:
   `Filter(Commitments, !(Text('Commitment Status') in ["Done","Cancelled"]) && !IsBlank('Due Date') && 'Due Date' < Today())`
3. **Insert** → **Vertical gallery**, middle column: `X = 468`, `Y = 70`, `Width = 430`, `Height = 650`. Rename `galRadarOwnerless`. **Items**:
   `Filter(Commitments, IsBlank(Owner) && !(Text('Commitment Status') in ["Done","Cancelled"]))`
4. **Insert** → **Vertical gallery**, right column: `X = 916`, `Y = 70`, `Width = 430`, `Height = 650`. Rename `galRadarSlipping`. **Items**:
   `Filter(Commitments, 'Times Postponed' >= 2 && !(Text('Commitment Status') in ["Done","Cancelled"]))`
5. Select each gallery's template → **OnSelect**:
   `Set(varSelectedCommitment, ThisItem); EditForm(frmCommitment); Navigate(scrCommitmentDetail, ScreenTransition.Fade)`
   — tapping any row jumps straight to Commitment detail.
6. End-to-end check: confirm the pre-seeded "Compare tooling vendor quotes" commitment (`Times Postponed = 3` in 04-SAMPLE-DATA.md) appears under **Slipping**.

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
3. Open a **decision** → rationale + options; filter Decisions to **Reversed / Superseded**.
4. **Follow-up Radar** → Overdue / Ownerless / Slipping.
5. Switch to the **model-driven app** → "same data, a fast admin view" (create/edit a record live).
6. Show the **Power Automate flow run history** → "this already emailed the overdue owners this morning."

---

## §Deferred — NOT in this phase (keep it simple)

Explicitly out of scope for the demo; add later only if the client validates:

- AI note summarizer (Copilot/AI Builder)
- Extra fields (Priority, Confidence, Impact Area, Commitment Type, Notes)
- Approvals, Teams/Outlook sync, role-based views, trend analytics

Re-run the AYA form before building any of these — several would raise the app's scoring.
