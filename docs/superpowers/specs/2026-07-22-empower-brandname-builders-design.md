# Empower@BrandName Builders — On-Demand Digital Talent Marketplace — Design

> Use Case 2 from `IDIQ_Summit_Empower Use Cases.md`. Companion to the prior
> `docs/meeting-decision-commitment-tracker/` project — same "buildable Power
> Platform demo" philosophy, but AI matching is a first-class, in-scope
> capability here (not deferred).

## 1. Problem & Goal

Departments have digital ideas but often lack visibility into which IDIQ
specialists/talents are already screened, available, and skilled enough to
help. This solution makes existing specialist capacity discoverable through
natural-language search, so a department can go from "I have a challenge" to
"here are 5 people who can help" in one interaction, instead of emailing
around or waiting on a resource manager to remember who's free.

**Goal for this phase:** a demoable, real (not mocked) AI-matching experience
over a small fictional specialist roster, built on an architecture that
scales to the real specialist data ITD will provide later.

## 2. Scope

- **Pilot scope:** single-department pilot (keeps this in the same
  "Team/Single department" AYA tier as the prior project).
- **Data:** fictional/dummy specialist profiles for this phase (~15–30
  records). Real CV/profile onboarding from ITD is a known **Phase 2**
  follow-on, not built now — the data model and indexing pipeline are
  designed so real data drops in without a redesign.
- **AI:** in scope this phase. This is the key difference from the prior
  project (which deferred AI entirely) — semantic + keyword matching is the
  headline demo moment here.

## 3. Architecture

Four flows over one shared Dataverse solution:

```
1. Admin (profile maintenance)
   Model-driven app  <──────────────►  Dataverse
   (ITD Resource Managers)              (Specialist Profile, Skill,
                                          Certification, Engagement History)

2. Nightly indexing pipeline
   Dataverse ──► Power Automate (nightly recurrence) ──► Azure OpenAI
   (profiles changed    (queries changed/new profiles,     (generate
    since last run)       loops them)                       embedding)
                                                                 │
                                                                 ▼
                                                          Azure AI Search
                                                     (hybrid keyword+vector
                                                      index, upsert/delete)

3. AI Talent Copilot (the matching moment)
   Canvas app / Teams ──► Copilot Studio agent ──► Power Automate
   (chat control,           (Talent Copilot            (custom action:
    plain-language            topic)                     query Azure AI
    challenge)                                            Search, then score
                                                           + explain via
                                                           Azure OpenAI GPT)
                                                                 │
                                                                 ▼
                                                          Adaptive Card
                                                    (top 5 specialists,
                                                     score + rationale;
                                                     supports in-context
                                                     follow-up questions)

4. Skills Intelligence Dashboard
   Dataverse ──► Power BI report
   (availability, utilization,   (availability, skills demand,
    skills, engagement history)   utilization trends, capability gaps)
```

### 3.1 Why this shape (approaches considered)

For the matching engine, four approaches were weighed:

| # | Approach | Verdict |
|---|---|---|
| A | Dataverse keyword pre-filter → AI Builder re-ranks shortlist | Rejected — recall capped by tag completeness |
| B | Single LLM call over the full dummy roster | Rejected — doesn't scale once real CVs load at volume |
| C | Hand-built Azure AI Search vector pipeline, no conversational layer | Rejected alone — right retrieval, wrong UX for "Copilot" branding |
| **D** | **Copilot Studio chat shell + custom action backed by Azure AI Search hybrid search** | **Selected** — real scalable semantic+keyword retrieval, conversational UX, follows the use-case doc's own naming of Copilot Studio |

For the indexing pipeline, two approaches were weighed:

| # | Approach | Verdict |
|---|---|---|
| 1 | Event-driven push (flow fires on every Dataverse create/update/delete) | Rejected for now — real-time freshness isn't needed; more flow runs than necessary |
| **2** | **Nightly scheduled push (Power Automate queries Dataverse for changes since last run, embeds, upserts to Azure AI Search)** | **Selected** — matches the prior project's "daily flow" precedent, no Blob/SQL staging layer needed, nightly freshness is acceptable for this pilot |

**Assumption (flag for review):** GPT-based scoring/rationale generation in
the custom action calls the **same Azure OpenAI resource** used for
embeddings directly (via HTTP/connector action in the flow), rather than
introducing AI Builder as a separate layer — this avoids provisioning/
licensing two AI surfaces for one capability. If AI Builder is preferred for
governance or credit-pooling reasons, this is a drop-in swap in the custom
action flow only.

## 4. Data Model

| Table | Key fields | Notes |
|---|---|---|
| **Specialist Profile** | Name, Title/Role, Bio summary, Availability (choice: Available / Partial / Unavailable), Utilization %, CV attachment (file), Resource Manager (lookup to Team Member), Search Index Status / Last Indexed (watermark for the nightly flow) | One row per specialist |
| **Skill** | Skill name, Category (Power Apps, Power Automate, Power BI, Copilot Studio, Power Pages, Dataverse, AI, Automation, Analytics) | Many-to-many to Specialist Profile; reusable taxonomy |
| **Certification** | Name, Issuer, Date earned | Child table to Specialist Profile |
| **Engagement History** | Project name, Department, Outcome/summary, Date range | Child table to Specialist Profile; feeds both "previous engagements" and Power BI utilization trends |
| **Team Member** | Name, Email | Reused pattern from the prior project; Resource Manager lookup target |

**Azure AI Search index** (derived): one document per Specialist Profile,
combining Bio + Skills + Certifications + Engagement summaries into the text
used for the embedding, plus structured fields (Availability, Utilization,
Skill Category tags) for keyword/filter precision in the hybrid query.

## 5. Canvas App Screens

- **Home / Talent Copilot chat:** embedded Copilot Studio chat control;
  department types a plain-language challenge; nav to Search Specialists and
  Skills Dashboard.
- **Top 5 Matches:** the Adaptive Card rendering of the custom action's
  result — ranked specialist cards with match %, one-line rationale, and
  support for in-context follow-up questions (e.g., "does Jane also know
  DAX?") without leaving the conversation.

## 6. Build Order

1. Dataverse tables + relationships
2. Model-driven app (ITD resource manager CRUD — safety net, build first)
3. Sample/dummy data load (~15–30 fictional specialists)
4. Azure AI Search index + Azure OpenAI resource provisioning
5. Nightly Power Automate indexing flow
6. Copilot Studio agent (Talent Copilot topic + custom action)
7. Canvas app (chat entry screen + nav shell)
8. Power BI Skills Intelligence Dashboard
9. *(Deferred — Phase 2)* CV PDF upload + AI Builder document extraction into
   structured profile fields, for onboarding real specialist data

## 7. Error Handling

- **Nightly indexing flow:** retry policy on Azure OpenAI/Azure AI Search
  calls; a separate "last successful run" watermark (distinct from "last
  attempted") so a transient failure doesn't silently skip records; failure
  notification email to the solution admin via the Office 365 Outlook
  connector.
- **Custom action (live chat query):** graceful no-match response ("no
  strong matches — try rephrasing") instead of an empty Adaptive Card;
  timeout fallback message if Azure AI Search/Azure OpenAI responds slowly.
- **Data integrity:** cascade/restrict delete so a removed Specialist Profile
  doesn't orphan Skill/Certification/Engagement History child records.

## 8. Testing Approach (demo scope — no formal automation)

- Manual CRUD test of the model-driven app.
- Manually trigger the nightly indexing flow once; verify Azure AI Search
  document count/content matches Dataverse.
- A small fixed set of test business challenges with known expected top
  matches in the dummy dataset, as a regression check against AI drift.
- Canvas app navigation walkthrough.
- Power BI dashboard filter sanity check.

## 9. Governance / AYA Scope Summary

- **Scope:** single-department pilot.
- **Data:** internal only; fictional/dummy specialist data this phase — no
  PII, no client data.
- **AI:** in scope this phase — real semantic matching via Azure OpenAI +
  Azure AI Search, plus Copilot Studio as the conversational layer.
- **New dependencies vs. the prior project:** Azure OpenAI resource, Azure AI
  Search resource, Copilot Studio (confirm licensing/message-consumption
  costs with the Power Platform admin).

## 10. Deferred (Phase 2+)

- Real specialist/CV data onboarding.
- CV PDF upload + AI Builder document extraction (auto-populate structured
  fields — skills, certs, years of experience — from an uploaded CV).
- Event-driven (real-time) indexing, if nightly freshness proves
  insufficient once real usage patterns are observed.
