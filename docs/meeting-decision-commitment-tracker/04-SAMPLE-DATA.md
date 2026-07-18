# Sample Data — Meeting Decision & Commitment Tracker

All records are **fictional and PII-free** (people are made-up names + roles). Columns
match the **lean core model** in 02-DATA-MODEL.md. Dates are relative to a **demo date of
2026-07-15** so the Radar and "due for review" states are populated. Same data feeds
**both** apps.

> Load order: **Team Members → Meetings → Decisions → Commitments**.

## Team Members (fictional — no PII; Email is a dummy address for the reminder flow only)

| Team Member Name | Role | Email |
|---|---|---|
| Maya | Team Lead | maya.demo@example.com |
| Dev | Engineer | dev.demo@example.com |
| Priya | Engineer | priya.demo@example.com |
| Leo | Analyst | leo.demo@example.com |
| Sam | Manager | sam.demo@example.com |

## Meetings

| Meeting Name | Meeting Date | Meeting Type | Attendees (free text) | Notes / Summary |
|---|---|---|---|---|
| M1 — Weekly Team Sync — 2026-07-10 | 2026-07-10 | Standup | Maya, Dev, Priya, Leo | Discussed sprint cadence, onboarding gaps, and the flaky test suite. |
| M2 — Q3 Planning — 2026-06-25 | 2026-06-25 | Planning | Sam, Maya, Dev, Priya | Set Q3 priorities; debated tooling; agreed to revisit vendor in July. |
| M3 — Process Review — 2026-05-20 | 2026-05-20 | Review | Maya, Dev, Leo | Reviewed handover process; decided on backup owners for key tasks. |
| M4 — Steering Check-in — 2026-07-14 | 2026-07-14 | Steering | Sam, Maya | Reversed the earlier "single tooling vendor" call after cost concerns. |

## Decisions  (Decision Maker = lookup to Team Member)

| Decision Title | Meeting | Context / Problem | Options Considered | Chosen Option | Rationale | Decision Maker | Decision Date | Decision Status | Review Date |
|---|---|---|---|---|---|---|---|---|---|
| Adopt 2-week sprint cadence | M1 | Delivery felt unpredictable | 1-week / 2-week / no sprints | 2-week sprints | Balances planning overhead with responsiveness | Maya | 2026-07-10 | Decided | 2026-08-10 |
| Standardize on single tooling vendor | M2 | Tool sprawl across team | Single vendor / best-of-breed / status quo | Single vendor | Simpler admin, volume discount | Sam | 2026-06-25 | Reversed / Superseded | 2026-07-15 |
| Assign backup owners for key tasks | M3 | Bus-factor risk on handovers | Backups / documentation only / do nothing | Named backup owners | Reduces single-point-of-failure risk | Maya | 2026-05-20 | Decided | 2026-07-01 |
| Revert to best-of-breed tooling | M4 | Single-vendor cost exceeded budget | Keep single vendor / revert | Revert to best-of-breed | Cost outweighed admin savings; supersedes M2 decision | Sam | 2026-07-14 | Decided | 2026-09-14 |

> "Standardize on single tooling vendor" (M2) is **Reversed / Superseded** by "Revert to
> best-of-breed tooling" (M4) — material for the timeline/reversal demo. Its Review Date has
> also passed, but it does **not** appear under "Due for review" — that view requires
> **Status = Decided**, and this one no longer is. Only "Assign backup owners for key tasks"
> (still Decided, Review Date 2026-07-01) appears there.

## Commitments  (Owner = lookup to Team Member; blank = ownerless)

| Commitment Title | Meeting | Related Decision | Description | Owner | Due Date | Original Due Date | Times Postponed | Commitment Status |
|---|---|---|---|---|---|---|---|---|
| Draft onboarding checklist | M1 | Assign backup owners for key tasks | New-hire ramp doc | Dev | 2026-07-08 | 2026-07-01 | 1 | In Progress |
| Fix flaky test suite | M1 |  | Stabilize CI | (blank) | 2026-07-05 | 2026-07-05 | 0 | Not Started |
| Set up 2-week sprint board | M1 | Adopt 2-week sprint cadence | Configure board | Priya | 2026-07-20 | 2026-07-20 | 0 | In Progress |
| Compare tooling vendor quotes | M2 | Standardize on single tooling vendor | Collect 3 quotes | Dev | 2026-07-02 | 2026-06-20 | 3 | Blocked |
| Document handover steps | M3 | Assign backup owners for key tasks | Write handover guide | Leo | 2026-07-12 | 2026-07-12 | 0 | Not Started |
| Announce tooling reversal | M4 | Revert to best-of-breed tooling | Email the team | Maya | 2026-07-18 | 2026-07-18 | 0 | Not Started |
| Archive single-vendor contract notes | M4 | Revert to best-of-breed tooling | Tidy shared folder | (blank) |  |  | 0 | Not Started |

### What the sample data demonstrates (against demo date 2026-07-15)

- **Overdue:** "Fix flaky test suite", "Compare tooling vendor quotes", "Document handover steps".
- **Ownerless:** "Fix flaky test suite", "Archive single-vendor contract notes".
- **Slipping (Times Postponed ≥ 2):** "Compare tooling vendor quotes" (3).
- **Decisions due for review:** "Assign backup owners for key tasks" only ("Standardize on single tooling vendor" is excluded — its status is Reversed / Superseded, not Decided).
- **Reversed / superseded:** "Standardize on single tooling vendor" (Reversed / Superseded), superseded by "Revert to best-of-breed tooling".
- **"My commitments" demo:** pick **Dev** → 2 commitments (onboarding checklist, vendor quotes).
- **Daily reminder flow demo:** running the flow against this data should email `dev.demo@example.com` (2 overdue: onboarding checklist, vendor quotes) and `leo.demo@example.com` (1 overdue: handover steps). "Fix flaky test suite" is overdue but ownerless, so it's skipped by the flow (still visible on the canvas Follow-up Radar).
