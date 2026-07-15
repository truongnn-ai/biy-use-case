# Demo Pitch & Talking Points — Meeting Decision & Commitment Tracker

*One-pager for the client demo session. ~5–7 minutes.*

---

## The hook (say this first — 20 seconds)

> "Every team makes decisions and commitments in meetings — and then loses them. The
> *reasoning* behind a decision evaporates, and 'I'll handle it' promises quietly go
> overdue. This app turns every meeting into three things you can actually find later:
> the **decisions**, the **commitments**, and a **radar** that flags what's slipping."

## The problem, in their words

- "Why did we decide that again?" — rationale lives in someone's memory.
- "Wait, didn't we already decide this?" — reversed decisions are never recorded.
- "Who was supposed to do that?" — action items die at the bottom of meeting notes.
- "That's been 'in progress' for a month." — no view of what's slipping.

**These are usually unsolved internally** — most teams rely on minutes written once and never re-read. That's the differentiator.

## What it does (one line each)

- **Captures** decisions with rationale, options considered, owner, and a review date.
- **Tracks** commitments/follow-ups with owner, due date, and status.
- **Surfaces** overdue, ownerless, and repeatedly-postponed items on a Follow-up Radar.
- **Remembers** reversed/superseded decisions on a timeline.

## Live demo flow (follow in order)

| # | Do this | Say this |
|---|---------|----------|
| 1 | Open **Home dashboard** | "At a glance: open commitments, what's overdue, and decisions due to be revisited." |
| 2 | Open a **meeting** | "One meeting → its decisions and commitments captured together, not scattered." |
| 3 | Open a **decision** | "Here's the *rationale* and the options we weighed — this is what usually gets lost." |
| 4 | Filter decisions to **Reversed** | "We even track when we change our mind — so nobody re-opens a settled call by accident." |
| 5 | Open **Follow-up Radar** | "Overdue, ownerless, and slipping — the stuff that normally hides in notes." |
| 6 | **Postpone** a commitment | "Watch the 'times postponed' counter tick up — it instantly appears under Slipping." |
| 7 | Switch to the **model-driven app** | "Same data, a second experience — a fast admin view. I'll add a record here and it shows up in the polished app instantly." |

## Why Power Platform / why now

- **Same data, two experiences:** one Dataverse, a **canvas app** for the team (polished) and a **model-driven app** for fast admin — built once, no duplication.
- Built in **under a week** by one developer, on **Dataverse only** — no external systems, no SQL, no Client integration.
- **AYA in-scope: Team / Single department.** No PII, no financial data, no enterprise dimensions, no AI in this phase.
- Deliberately kept **simple for the demo** — extras (AI note-capture, email reminders) are a validated Phase-2 conversation, not scope creep.

## Anticipated questions (have answers ready)

- **"Where do the numbers/impact come from?"** → Sample data is illustrative for the demo; live use populates from real meetings.
- **"Is this just another task tracker?"** → No — it captures *decisions + rationale + reversals*, which task tools don't. Commitments are the lightweight follow-through layer, not a full PM tool.
- **"What about our data / privacy?"** → Internal-only, no PII by design; owner names are free-text labels for the demo. See the AYA scorecard.
- **"Can it plug into Outlook/Teams?"** → Yes, as a Phase-2 option — deliberately left out of the demo to keep it zero-integration and in-scope.

## The ask (close with this)

> "If this maps to a real pain for one of your teams, we can pilot it with that team's
> actual meetings in a couple of weeks — and re-assess the AYA form before adding any
> Outlook/Teams integration."

## Do / Don't during the demo

- ✅ Lead with the **Follow-up Radar** and the **reversed-decision** view — they're the "aha."
- ✅ Keep it to one team's story; concrete beats abstract.
- ❌ Don't pitch it as enterprise-wide (moves it out of AYA scope).
- ❌ Don't promise live Outlook/Teams sync in the demo build.
