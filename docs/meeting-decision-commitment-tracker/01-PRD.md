# PRD — Meeting Decision & Commitment Tracker

- **Version:** 1.0 (demo)
- **Owner:** (provider team)
- **Status:** Draft for client validation
- **Platform:** Microsoft Power Platform — **two apps** (model-driven + canvas) over **one Dataverse**
- **Target build effort:** ≤ 1 week, single beginner developer
- **Guiding rule:** keep it simple — demo only. Build core features; defer everything else.

---

## 1. Summary

Teams make dozens of decisions and commitments in meetings. The **decision itself, the
rationale, who owns it, and the follow-through** typically live in scattered notes, chat
threads, or nowhere at all. Weeks later nobody remembers *why* a decision was made, and
informal commitments quietly go overdue.

The **Meeting Decision & Commitment Tracker** is a lightweight solution that turns a meeting
into three durable records: the **meeting**, the **decisions** made, and the
**commitments** taken on. It adds a **Follow-up Radar** that surfaces commitments that are
overdue, ownerless, or repeatedly postponed, and a **Decision timeline** that shows what
was decided, reviewed, or reversed over time.

It ships as **two apps sharing one Dataverse**: a **model-driven app** for fast data
entry/admin (built first as a safety net) and a **canvas app** as the demo showpiece
(dashboard, Follow-up Radar, timeline).

## 1a. Demo scope — core vs. deferred (⭐ number-one rule: keep it simple)

**Core (build this phase):**
- 4 lean Dataverse tables (Team Member, Meeting, Decision, Commitment) — core columns only. Team Member holds fictional people (incl. a fictional/dummy Email); Decision Maker & Owner are lookups to it.
- Model-driven app: forms + core views (Overdue, Ownerless, Slipping, Due-for-review, Reversed / Superseded).
- Canvas app: Home dashboard (KPIs), Meetings, Decisions (+ Reversed filter/timeline), Commitments, Follow-up Radar, Postpone.
- **Daily overdue email reminder (FR-10)** — a scheduled Power Automate flow that emails each Owner their overdue commitments via Office 365 Outlook, using the fictional/dummy Email on their Team Member record.
- Sample data to make every state visible.

**Deferred (NOT this phase):**
- AI note summarizer (US-13) — Microsoft AI, revisit only if client validates.
- Extra fields: Priority, Confidence, Impact Area, Commitment Type, Notes, Organizer, Meeting Status.
- Approvals, Teams/Outlook sync, role-based views, analytics.

> User stories/requirements below tagged **(DEFERRED)** are documented for context but are
> out of scope for the demo build.

## 2. Problem statement


| Pain                                    | Today                              | Cost                                           |
| --------------------------------------- | ---------------------------------- | ---------------------------------------------- |
| Decisions lose their rationale          | Buried in notes / memory           | Re-litigating settled topics; repeated debates |
| No record of *reversed* decisions       | Not tracked at all                 | Teams silently contradict past decisions       |
| Action items die in notes               | Pasted into a doc, never revisited | Missed deadlines, dropped balls                |
| Informal ("I'll handle it") commitments | Never captured                     | Ownerless work; blame at review time           |
| No review of past decisions             | No trigger to revisit              | Stale decisions never re-examined              |


These are **rarely solved by an internal tool** — most teams rely on meeting minutes that
are written once and never read again. That novelty is the demo's selling point.

## 3. Goals & non-goals

### Goals

- G1 — Capture a meeting's decisions and commitments in under 2 minutes.
- G2 — Make it obvious which commitments are **overdue, ownerless, or slipping**.
- G3 — Preserve **decision rationale** and show a **decision history/timeline**, including reversals.
- G4 — Provide a manager-friendly dashboard of open items and decisions due for review.
- G5 — Stay fully within AYA "Team / Single department" scope (see 06-AYA-ASSESSMENT.md).

### Non-goals (out of scope for the demo)

- N1 — Not a full project/task management replacement (no Gantt, sprints, dependencies engine).
- N2 — No integration with Client systems, external SQL, HR, or calendar sync (the daily Outlook reminder flow is the one integration in scope this phase).
- N3 — No PII, financial, or confidential data. People live in a **Team Member** table with **fictional** name + role only (no email/ID); Attendees are free-text labels. Not linked to real M365 users. Kept Internal.
- N4 — No enterprise-wide rollout, multi-department roles, or SSO customization.
- N5 — No approvals workflow (decisions are recorded, not routed for sign-off).

## 4. Personas


| Persona                            | Role                    | Needs                                                      |
| ---------------------------------- | ----------------------- | ---------------------------------------------------------- |
| **Maya — Team Lead / Facilitator** | Runs recurring meetings | Fast capture of decisions & actions during/after a meeting |
| **Dev — Team Member / Owner**      | Takes on commitments    | A clear view of "what did I commit to and when is it due"  |
| **Sam — Department Manager**       | Oversees several teams  | Dashboard of overdue items and decisions due for review    |


## 5. User stories

### Meetings

- US-01: As Maya, I can create a meeting record (name, date, type, attendees, notes).
- US-02: As Maya, from a meeting I can add one or more decisions and commitments.
- US-03: As anyone, I can open a meeting and see all its decisions and commitments together.

### Decisions

- US-04: As Maya, I can record a decision with context, options considered, chosen option, rationale, decision maker, and decision date.
- US-05: As Maya, I can set a decision **status** (Proposed, Decided, Reviewed, Reversed / Superseded) and a **review date**.
- US-06: As Sam, I can see a **decision timeline** and filter to **reversed/superseded** decisions.
- US-07: As Sam, I can see decisions **due for review** (review date ≤ today).

### Commitments / follow-ups

- US-08: As Maya, I can add a commitment with owner, description, type, due date, priority, and status.
- US-09: As Dev, I can filter to **"My commitments"** by picking myself from a Team Member dropdown.
- US-10: As anyone, the **Follow-up Radar** shows commitments that are **overdue**, **ownerless** (no owner), or **repeatedly postponed** (postponed ≥ 2 times).
- US-11: As Dev, when I push a due date out, the app increments a **"times postponed"** counter and keeps the **original due date**.

### Dashboard

- US-12: As Sam, the Home screen shows KPI tiles: Open commitments, Overdue, Decisions this month, Decisions due for review, Reversed / Superseded decisions.

### Reminders

- US-14: As Dev, I get a daily email listing my overdue commitments, so I don't have to open the app to know what I'm behind on.

### Optional AI (Microsoft-provided only — AYA score 2) — **(DEFERRED)**

- US-13 **(DEFERRED)**: As Maya, I can paste raw meeting notes and have Copilot/AI Builder **suggest** candidate decisions and action items, which I confirm before saving.

## 6. Functional requirements

- FR-01 — Four related tables: **Team Member** (fictional people), **Meeting**, **Decision**, **Commitment** (see 02-DATA-MODEL.md). Decision Maker and Owner are **lookups** to Team Member; Attendees stays free-text.
- FR-02 — A Meeting has many Decisions and many Commitments. A Decision optionally has many Commitments.
- FR-03 — Commitment must compute **Is Overdue** = (Status not in {Done, Cancelled}) AND (Due Date < today).
- FR-04 — Commitment must flag **Is Ownerless** = Owner is blank.
- FR-05 — Commitment must flag **Is Slipping** = Times Postponed ≥ 2.
- FR-06 — Decision must flag **Due For Review** = Review Date ≤ today AND Status = Decided.
- FR-07 — All list screens support text search and at least one choice-based filter.
- FR-08 — Dashboard KPIs recompute from live data (no hard-coded totals).
- FR-09 — Postpone action on a Commitment: sets a new Due Date, keeps Original Due Date, increments Times Postponed.
- FR-10 — A daily Power Automate flow queries Commitments for **Is Overdue** records and emails each **Owner** one overdue item via the Office 365 Outlook connector, using the Owner's (fictional/dummy) Email on their Team Member record and naming the originating **Meeting** for context. Ownerless commitments are skipped (no recipient). Intentionally minimal — a meeting-context nudge, not a task-management surface (see **N1**): no snooze, reassignment, or priority actions.

## 7. Non-functional requirements

- NFR-01 — Buildable by a Power Platform beginner in ≤ 1 week.
- NFR-02 — Dependency-light: Dataverse + the standard Office 365 Outlook connector (for FR-10); no external services.
- NFR-03 — Data volume: demo < 200 records (AYA Complexity = 1).
- NFR-04 — Availability: non-critical; downtime is insignificant (AYA Availability = 1).
- NFR-05 — Accessible labels and tab order on forms (basic Power Apps accessibility defaults).

## 8. The two apps + one flow

### 8a. Model-driven app (build first — safety net, fast admin)
- Sitemap with the three tables (Meetings, Decisions, Commitments).
- Default forms with the core columns.
- Core views reproducing the derived flags: **Overdue**, **Ownerless**, **Slipping**,
  **Decisions due for review**, **Reversed / Superseded**.

### 8b. Canvas app (demo showpiece) — screens
1. **Home / Dashboard** — KPI tiles + quick links to each area.
2. **Meetings** — searchable gallery; "New meeting"; filter by type.
3. **Meeting detail** — meeting fields + related Decisions gallery + related Commitments gallery.
4. **Decisions** — gallery + filter by status (incl. **Reversed / Superseded**) + search; "Timeline" toggle sorted by decision date.
5. **Decision detail / edit** — full decision form; quick-add linked commitment.
6. **Commitments** — gallery with tabs/filters: All · My commitments · Open · Overdue.
7. **Commitment detail / edit** — full form + "Postpone" button (FR-09).
8. **Follow-up Radar** — three grouped lists: Overdue · Ownerless · Slipping (postponed ≥ 2).

### 8c. Reminder flow (Power Automate)
- Scheduled (daily) recurrence trigger.
- Lists Commitments matching **Is Overdue**, drops ownerless ones.
- Sends one email per overdue commitment (Office 365 Outlook connector), naming the
  originating Meeting plus the commitment and its due date; skips ownerless commitments.
  Deliberately minimal — a nudge back to the meeting, not a task-management inbox.

(All three share the same Dataverse tables — see 03-BUILD-GUIDE.md for build order.)

## 9. Success metrics (for the demo conversation)

- Time to capture a full meeting (1 decision + 2 commitments) < 2 minutes.
- Follow-up Radar correctly surfaces every overdue/ownerless/slipping seeded record.
- Stakeholder can answer "why was decision X made?" and "what's overdue?" in one click each.

## 10. Roadmap (post-demo, if client validates)

- Phase 2: Outlook/Teams meeting sync; Teams tab embedding.
- Phase 3: Role-based views; light approval on high-impact decisions.
- Phase 4: Trend analytics (decision reversal rate, average commitment slippage).

> Note: Phases 2–4 would likely raise AYA dimensions (integration, users, growth) and must be re-assessed before build.

## 11. Open questions for the client

- OQ-1 — **Resolved:** owner/decision-maker use a **fictional Team Member lookup** (keeps Internal). Linking to real M365 users is a Phase-2 decision that would raise Data classification to PII.
- OQ-2 — **Resolved:** the daily Outlook reminder flow (FR-10) is **in scope** for this phase, using fictional/dummy Team Member emails (see guardrail in 06-AYA-ASSESSMENT.md) so it stays Internal, not PII.
- OQ-3 — Include the optional AI note-summarization feature, or keep AI at score 1 (none)?

