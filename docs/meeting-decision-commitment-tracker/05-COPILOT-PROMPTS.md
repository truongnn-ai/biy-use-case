# Copilot-in-Power-Apps Prompts

Paste these into **Copilot** inside make.powerapps.com. Copilot generates a first draft;
always verify column types, choice values, and relationships against **02-DATA-MODEL.md**.

> **Demo scope:** only the lean core is created here, plus the one in-scope automation (the
> daily overdue reminder flow). No AI, no extra fields.
> Order: create tables → relationships → **model-driven app (first)** → **canvas app** →
> data → **reminder flow**.

---

## Prompt A — Create the three tables (lean core)

```
Create four Dataverse tables for a "Meeting Decision & Commitment Tracker":

1) Team Member — columns: Team Member Name (primary text), Role (text),
   Email (text, email format).
   (This holds fictional demo people only — no ID, no real personal data. Email is a
   fictional/dummy address used only as the recipient for the daily reminder flow.)

2) Meeting — columns: Meeting Name (primary text), Meeting Date (date only),
   Meeting Type (choice: Standup, Planning, Review, Steering, Ad-hoc, Other),
   Attendees (multiline text), Notes/Summary (multiline text).

3) Decision — columns: Decision Title (primary text), Context/Problem (multiline),
   Options Considered (multiline), Chosen Option (multiline), Rationale (multiline),
   Decision Date (date only),
   Decision Status (choice: Proposed, Decided, Deferred, Reversed, Superseded),
   Review Date (date only).
   (Decision Maker is added as a lookup in the next prompt.)

4) Commitment — columns: Commitment Title (primary text), Description (multiline),
   Due Date (date only), Original Due Date (date only),
   Times Postponed (whole number, default 0),
   Commitment Status (choice: Not Started, In Progress, Blocked, Done, Cancelled, Deferred).
   (Owner is added as a lookup in the next prompt.)
```

## Prompt B — Add the relationships

```
Add these relationships:
- Meeting to Decision: one-to-many (add a "Meeting" lookup on Decision).
- Meeting to Commitment: one-to-many (add a "Meeting" lookup on Commitment).
- Decision to Commitment: one-to-many and optional (add a "Related Decision" lookup on Commitment).
- Team Member to Decision: one-to-many and optional (add a "Decision Maker" lookup on Decision).
- Team Member to Commitment: one-to-many and optional (add an "Owner" lookup on Commitment).
```

## Prompt C — Generate the model-driven app FIRST (safety net)

```
Create a model-driven app that includes the Meeting, Decision, and Commitment tables in the
navigation, plus the Team Member table as a reference-data area. For the Commitment table add views:
- "Overdue": status is not Done or Cancelled and Due Date is before today.
- "Ownerless": Owner is empty and status is not Done or Cancelled.
- "Slipping": Times Postponed is greater than or equal to 2 and status is not Done or Cancelled.
For the Decision table add views:
- "Due for review": Decision Status is Decided and Review Date is on or before today.
- "Reversed / Superseded": Decision Status is Reversed or Superseded.
```

## Prompt D — Generate the canvas app (demo showpiece)

```
Create a canvas app (tablet layout) from the Meeting, Decision, and Commitment tables with:
- A Home dashboard with KPI tiles: open commitments, overdue commitments,
  decisions this month, decisions due for review, and reversed/superseded decisions.
- A Meetings screen (searchable gallery + form) and a Meeting detail screen showing the
  meeting plus its related decisions and commitments.
- A Decisions screen with search, a filter for Decision Status (including a Reversed filter),
  and a timeline view sorted by Decision Date.
- A Commitments screen with filter buttons for All, My commitments, Open, and Overdue.
- A "Follow-up Radar" screen with three lists: overdue commitments,
  ownerless commitments (Owner is blank), and slipping commitments (Times Postponed >= 2).
```

## Prompt E — Add derived logic + Postpone (canvas)

```
Help me add these in the canvas app:
- Overdue commitment = status not Done/Cancelled AND Due Date < today.
- Ownerless commitment = Owner is blank AND status not Done/Cancelled.
- Slipping commitment = Times Postponed >= 2 AND status not Done/Cancelled.
- Decision due for review = Decision Status is Decided AND Review Date <= today.
- A Postpone button on a commitment that sets Original Due Date (only if blank) to the
  current Due Date, sets Due Date to a newly picked date, and increments Times Postponed by 1.
```

## Prompt F — Load sample data (optional)

```
Add sample rows to the Team Member, Meeting, Decision, and Commitment tables using this data:
[paste the tables from 04-SAMPLE-DATA.md]
Enter Team Members first (incl. their fictional/dummy Email), then Meetings, then Decisions
(link Meeting + Decision Maker), then Commitments (link Meeting, Owner, and where given
the Related Decision).
```

## Prompt G — Build the daily overdue reminder flow (Power Automate)

```
Create a scheduled cloud flow that runs once daily:
1. Trigger: Recurrence, every 1 day.
2. List rows on the Commitment table where Commitment Status is not Done or Cancelled
   and Due Date is before today (mirrors the "Is Overdue" logic).
3. Filter out rows where Owner is blank (ownerless commitments have no recipient).
4. For each remaining commitment, look up the Owner's Team Member record to get their Email.
5. Send an email (Office 365 Outlook connector) to that Email with the Commitment Title
   and Due Date, one email per overdue commitment.
Use only the fictional/dummy Email values already on the Team Member records — never a
real employee's inbox.
```

## Verification checklist after Copilot runs

- [ ] Only the lean core columns exist (no extra fields Copilot may have invented).
- [ ] Choice columns match 02-DATA-MODEL.md exactly.
- [ ] Lookups exist: Decision.Meeting, Decision.Decision Maker, Commitment.Meeting, Commitment.Owner, Commitment.Related Decision.
- [ ] Times Postponed is a whole number, default 0.
- [ ] Model-driven views return the expected sample records (04-SAMPLE-DATA.md).
- [ ] Canvas Radar filters + KPI tiles compute from live data (not hard-coded).
- [ ] Both apps and the reminder flow are in the one solution; no real PII/financial fields; Team Member holds fictional people only (name, role, dummy email).
- [ ] Reminder flow, when run manually, emails only the seeded overdue commitments to their dummy addresses, and skips ownerless ones.

> **Deferred (do NOT ask Copilot to build now):** AI note summarizer,
> Priority/Confidence/Impact Area/Commitment Type/Notes fields. See 03-BUILD-GUIDE §Deferred.
