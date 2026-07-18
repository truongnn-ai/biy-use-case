# Data Model — Meeting Decision & Commitment Tracker

Backend: **Microsoft Dataverse**. Four tables, shared by **both apps** (canvas +
model-driven). Build the tables once; both apps read/write the same rows.

> **Demo scope rule:** columns below are the **minimum core set** needed for the demo.
> Anything not listed is deliberately **deferred** (see bottom of file). Keep it lean.

> **People are fictional.** The **Team Member** table holds made-up demo people (name,
> role, and a **fictional/dummy email** — no real ID, no real PII). The Email exists only
> so the daily reminder flow (FR-10) has somewhere to send to. This is what keeps AYA Data
> at **Internal (2)**. Do **not** populate it with real employee addresses or wire it to
> real Microsoft 365 users for the demo (that would be PII → out of scope).

> Publisher/prefix: use your environment's default (e.g. `cr123_`). Put the 4 tables **and
> both apps** in a single solution named **Meeting Decision & Commitment Tracker**.

> **Primary keys are automatic — no need to add one.** Every Dataverse table gets a
> system-generated GUID primary key the moment it's created (e.g. `cr123_teammemberid`,
> `cr123_meetingid`, `cr123_decisionid`, `cr123_commitmentid`). All lookups below (Meeting,
> Decision Maker, Owner, Related Decision) reference that GUID internally, not the display
> name. The **"primary column"** listed for each table (Team Member Name, Meeting Name,
> Decision Title, Commitment Title) is Dataverse's **primary name column** — a required text
> label shown in lookups/search/views — not the primary key, and it must stay a text type
> (Dataverse doesn't allow it to be a GUID or lookup).



## Entity-relationship overview

```
Team Member (1) ──< (N) Decision      [Decision Maker]
Team Member (1) ──< (N) Commitment    [Owner]

Meeting (1) ────< (N) Decision
   │                    │
   │                    │ (1)
   │                    v
   └───────< (N) Commitment >──── (optional) linked to one Decision
```

- **Meeting → Decision**: one-to-many
- **Meeting → Commitment**: one-to-many
- **Decision → Commitment**: one-to-many, **optional**
- **Team Member → Decision** (as *Decision Maker*): one-to-many, **optional**
- **Team Member → Commitment** (as *Owner*): one-to-many, **optional** (blank = ownerless)
- **Attendees stay free-text** (multiline) — no relationship this phase (N:N deferred)

---



## Table 1 — Team Member  (3 columns) — fictional demo people


| Column (display name) | Data type                       | Required | Choices / notes                                                                                                                                                                           |
| --------------------- | ------------------------------- | -------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Team Member Name      | Single line text                | Yes      | Primary column. e.g. "Maya". Fictional — no PII                                                                                                                                           |
| Role                  | Single line text                | No       | e.g. "Team Lead", "Engineer", "Manager"                                                                                                                                                   |
| Email                 | Single line text (Email format) | No       | **Fictional/dummy address** (e.g. `maya.demo@example.com`) used only as the recipient for the daily reminder flow (FR-10). Never a real employee's address — blank = skipped by the flow. |




## Table 2 — Meeting  (5 columns)


| Column (display name) | Data type        | Required | Choices / notes                                                     |
| --------------------- | ---------------- | -------- | ------------------------------------------------------------------- |
| Meeting Name          | Single line text | Yes      | Primary column. e.g. "Weekly Team Sync — 2026-07-10"                |
| Meeting Date          | Date only        | Yes      |                                                                     |
| Meeting Type          | Choice           | Yes      | Standup, Planning, Review, Steering, Ad-hoc, Other                  |
| Attendees             | Multiline text   | No       | Comma-separated names/roles (**free text** — not linked this phase) |
| Notes                 | Multiline text   | No       | Raw meeting notes                                                   |




## Table 3 — Decision  (10 columns)


| Column (display name) | Data type                | Required | Choices / notes                                                     |
| --------------------- | ------------------------ | -------- | ------------------------------------------------------------------- |
| Decision Title        | Single line text         | Yes      | Primary column                                                      |
| Meeting               | Lookup → Meeting         | Yes      |                                                                     |
| Context               | Multiline text           | No       | Why it came up                                                      |
| Options Considered    | Multiline text           | No       | One per line                                                        |
| Chosen Option         | Multiline text           | Yes      | The decision                                                        |
| Rationale             | Multiline text           | No       | **The "why we decided that" — core value**                          |
| Decision Maker        | **Lookup → Team Member** | No       | Who's accountable                                                   |
| Decision Date         | Date only                | Yes      |                                                                     |
| Decision Status       | Choice                   | Yes      | Proposed, Decided, Reviewed, Reversed / Superseded — default Decided |
| Review Date           | Date only                | No       | Drives "due for review"                                             |




## Table 4 — Commitment  (9 columns)


| Column (display name) | Data type                | Required | Choices / notes                                                                    |
| --------------------- | ------------------------ | -------- | ---------------------------------------------------------------------------------- |
| Commitment Title      | Single line text         | Yes      | Primary column                                                                     |
| Meeting               | Lookup → Meeting         | Yes      |                                                                                    |
| Related Decision      | Lookup → Decision        | No       | Optional link                                                                      |
| Description           | Multiline text           | No       |                                                                                    |
| Owner                 | **Lookup → Team Member** | No       | **Blank = ownerless** (drives Radar)                                               |
| Due Date              | Date only                | No       |                                                                                    |
| Original Due Date     | Date only                | No       | Set once on create; never changed by Postpone                                      |
| Times Postponed       | Whole number             | Yes      | Default 0. **≥ 2 = slipping**                                                      |
| Commitment Status     | Choice                   | Yes      | Not Started, In Progress, Blocked, Done, Cancelled, Deferred — default Not Started |


---



## Derived flags — computed, NOT stored (keep it simple)

Do **not** create calculated/formula columns for the demo. Compute these in the **canvas
app** with Power Fx, and reproduce them as **filter conditions on model-driven views**.

> **Field-name note:** column display names that contain a space (`Commitment Status`, `Due Date`,
> `Decision Status`, `Review Date`, `Times Postponed`, `Original Due Date`, `Decision Date`,
> `Meeting Type`) must be wrapped in single quotes in Power Fx, e.g. `'Commitment Status'`.
>
> **Choice-column note:** **Commitment Status** and **Decision Status** are Choice columns. Some
> Dataverse connector versions reject `.Value` on them ("Name isn't valid. 'Value' isn't
> recognized"); wrapping in `Text(...)` (as below) reliably returns the display string instead
> and works across connector versions. Expect a harmless delegation warning at this demo's data
> scale.

```
// Is Overdue
!(Text('Commitment Status') in ["Done","Cancelled"]) && !IsBlank('Due Date') && 'Due Date' < Today()

// Is Ownerless  (Owner is a blank lookup)
IsBlank(Owner) && !(Text('Commitment Status') in ["Done","Cancelled"])

// Is Slipping
'Times Postponed' >= 2 && !(Text('Commitment Status') in ["Done","Cancelled"])

// Decision Due For Review
Text('Decision Status') = "Decided" && !IsBlank('Review Date') && 'Review Date' <= Today()
```



### "My commitments" (Owner is now a lookup)

Provide a **Team Member dropdown** (`cmbMe`) instead of typing a name, then filter by
comparing the lookup record directly — not by matching the display name (two demo people
could otherwise share a name and collide):

```
Filter(Commitments, Owner = cmbMe.Selected)
```



## Postpone behavior

When the user postpones a commitment (canvas app):

1. If **Original Due Date** is blank, set it to the current **Due Date**.
2. Set **Due Date** to the new chosen date.
3. Increment **Times Postponed** by 1.

```
Patch(Commitments, ThisItem,
    {
        'Original Due Date': Coalesce(ThisItem.'Original Due Date', ThisItem.'Due Date'),
        'Due Date': NewDate.SelectedDate,
        'Times Postponed': ThisItem.'Times Postponed' + 1
    }
)
```



## Choice set summary (for Copilot generation)

- **Meeting Type:** Standup · Planning · Review · Steering · Ad-hoc · Other
- **Decision Status:** Proposed · Decided · Reviewed · Reversed / Superseded

  *(Proposed = not decided yet, folds in the old "Deferred"; Decided = finalized, awaiting review; Reviewed = reviewed and still holds; Reversed / Superseded = reviewed and changed — merges the old "Reversed" and "Superseded" into one status.)*
- **Commitment Status:** Not Started · In Progress · Blocked · Done · Cancelled · Deferred

---



## Deferred (NOT in this phase) — keep the demo simple

These were considered and intentionally cut to stay focused on core value:

- Team Member: *job title, manager, photo, link to real M365 users* (would add PII → out of scope). Email is now included (fictional/dummy only, see Table 1) to support FR-10.
- Attendees as a **many-to-many** link to Team Member (kept as free-text this phase)
- Meeting: *Organizer*, *Meeting Status*
- Decision: *Confidence*, *Impact Area*, stored *Due-For-Review* column
- Commitment: *Commitment Type*, *Priority*, *Notes*, stored *Is-Overdue/Ownerless/Slipping* columns
- No AI fields

Add any of these later only if the client validates the concept and asks for them.