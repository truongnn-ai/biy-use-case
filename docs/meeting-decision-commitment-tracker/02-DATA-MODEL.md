# Data Model — Meeting Decision & Commitment Tracker

Backend: **Microsoft Dataverse**. Three tables, shared by **both apps** (canvas +
model-driven). Build the tables once; both apps read/write the same rows.

> **Demo scope rule:** columns below are the **minimum core set** needed for the demo.
> Anything not listed is deliberately **deferred** (see bottom of file). Keep it lean.

> Publisher/prefix: use your environment's default (e.g. `cr123_`). Put the 3 tables **and
> both apps** in a single solution named **Meeting Decision & Commitment Tracker**.

## Entity-relationship overview

```
Meeting (1) ────< (N) Decision
   │                    │
   │                    │ (1)
   │                    v
   └───────< (N) Commitment >──── (optional) linked to one Decision
```

- **Meeting → Decision**: one-to-many
- **Meeting → Commitment**: one-to-many
- **Decision → Commitment**: one-to-many, **optional**

---

## Table 1 — Meeting  (5 columns)

| Column (display name) | Data type | Required | Choices / notes |
|-----------------------|-----------|----------|-----------------|
| Meeting Name | Single line text | Yes | Primary column. e.g. "Weekly Team Sync — 2026-07-10" |
| Meeting Date | Date only | Yes | |
| Meeting Type | Choice | Yes | Standup, Planning, Review, Steering, Ad-hoc, Other |
| Attendees | Multiline text | No | Comma-separated names/roles (free text — not PII) |
| Notes / Summary | Multiline text | No | Raw meeting notes |

## Table 2 — Decision  (10 columns)

| Column (display name) | Data type | Required | Choices / notes |
|-----------------------|-----------|----------|-----------------|
| Decision Title | Single line text | Yes | Primary column |
| Meeting | Lookup → Meeting | Yes | |
| Context / Problem | Multiline text | No | Why it came up |
| Options Considered | Multiline text | No | One per line |
| Chosen Option | Multiline text | Yes | The decision |
| Rationale | Multiline text | No | **The "why we decided that" — core value** |
| Decision Maker | Single line text | No | Free-text label |
| Decision Date | Date only | Yes | |
| Decision Status | Choice | Yes | Proposed, Decided, Deferred, Reversed, Superseded — default Decided |
| Review Date | Date only | No | Drives "due for review" |

## Table 3 — Commitment  (9 columns)

| Column (display name) | Data type | Required | Choices / notes |
|-----------------------|-----------|----------|-----------------|
| Commitment Title | Single line text | Yes | Primary column |
| Meeting | Lookup → Meeting | Yes | |
| Related Decision | Lookup → Decision | No | Optional link |
| Description | Multiline text | No | |
| Owner | Single line text | No | **Blank = ownerless** (drives Radar) |
| Due Date | Date only | No | |
| Original Due Date | Date only | No | Set once on create; never changed by Postpone |
| Times Postponed | Whole number | Yes | Default 0. **≥ 2 = slipping** |
| Commitment Status | Choice | Yes | Not Started, In Progress, Blocked, Done, Cancelled, Deferred — default Not Started |

---

## Derived flags — computed, NOT stored (keep it simple)

Do **not** create calculated/formula columns for the demo. Compute these in the **canvas
app** with Power Fx, and reproduce them as **filter conditions on model-driven views**.

```
// Is Overdue
!(CommitmentStatus.Value in ["Done","Cancelled"]) && !IsBlank(DueDate) && DueDate < Today()

// Is Ownerless
IsBlank(Owner) && !(CommitmentStatus.Value in ["Done","Cancelled"])

// Is Slipping
TimesPostponed >= 2 && !(CommitmentStatus.Value in ["Done","Cancelled"])

// Decision Due For Review
DecisionStatus.Value = "Decided" && !IsBlank(ReviewDate) && ReviewDate <= Today()
```

## Postpone behavior

When the user postpones a commitment (canvas app):
1. If **Original Due Date** is blank, set it to the current **Due Date**.
2. Set **Due Date** to the new chosen date.
3. Increment **Times Postponed** by 1.

```
Patch(Commitments, ThisItem,
    {
        OriginalDueDate: Coalesce(ThisItem.OriginalDueDate, ThisItem.DueDate),
        DueDate: NewDate.SelectedDate,
        TimesPostponed: ThisItem.TimesPostponed + 1
    }
)
```

## Choice set summary (for Copilot generation)

- **Meeting Type:** Standup · Planning · Review · Steering · Ad-hoc · Other
- **Decision Status:** Proposed · Decided · Deferred · Reversed · Superseded
- **Commitment Status:** Not Started · In Progress · Blocked · Done · Cancelled · Deferred

---

## Deferred (NOT in this phase) — keep the demo simple

These were considered and intentionally cut to stay focused on core value:

- Meeting: *Organizer*, *Meeting Status*
- Decision: *Confidence*, *Impact Area*, stored *Due-For-Review* column
- Commitment: *Commitment Type*, *Priority*, *Notes*, stored *Is-Overdue/Ownerless/Slipping* columns
- No AI fields, no reminder/automation fields

Add any of these later only if the client validates the concept and asks for them.
