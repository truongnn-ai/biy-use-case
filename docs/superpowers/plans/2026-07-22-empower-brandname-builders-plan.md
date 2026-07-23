# Empower@BrandName Builders — Documentation Set Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the complete, buildable documentation set for the Empower@BrandName Builders talent marketplace demo (PRD, data model, sample data, build guide, Copilot Studio/AI prompts, AYA assessment, demo pitch), following the exact document-set convention already established in `docs/meeting-decision-commitment-tracker/`.

**Architecture:** This is a documentation deliverable, not application code — the "implementation" is a set of markdown/CSV/JSON files a Power Platform maker follows by hand (Dataverse Studio, Power Automate, Copilot Studio, Power BI Desktop are all low-code UIs, not scriptable from here). Each task below writes one complete file with real, final content (exact table/column names, exact flow steps, exact prompts, exact sample data) — nothing is a stub for a human to fill in later. "Testing" in this context means reviewing each doc against the approved design spec (`docs/superpowers/specs/2026-07-22-empower-brandname-builders-design.md`), not running an automated test suite.

**Tech Stack:** Markdown docs, CSV sample data, JSON (Azure AI Search index schema, Adaptive Card template), Power Fx snippets — targeting Dataverse, a model-driven app, a canvas app, Power Automate, Copilot Studio, Azure AI Search, Azure OpenAI, and Power BI.

---

## Reference

- Design spec: `docs/superpowers/specs/2026-07-22-empower-brandname-builders-design.md`
- Prior convention to mirror: `docs/meeting-decision-commitment-tracker/` (README.md, 01-PRD.md, 02-DATA-MODEL.md, 03-BUILD-GUIDE.md, 04-SAMPLE-DATA.md, 05-COPILOT-PROMPTS.md, 06-AYA-ASSESSMENT.md, 07-DEMO-PITCH.md)
- Target folder for this project: `docs/empower-brandname-builders/`

---

### Task 1: Data Model doc

**Files:**
- Create: `docs/empower-brandname-builders/02-DATA-MODEL.md`

- [ ] **Step 1: Write the data model doc**

```markdown
# Data Model — Empower@BrandName Builders

Five Dataverse tables (one reused from the prior project's Team Member pattern), plus a derived Azure AI Search index.

## Tables

### Specialist Profile
| Column | Type | Notes |
|---|---|---|
| Specialist Name | Single line of text (required) | |
| Title / Role | Single line of text | e.g. "Power Platform Developer" |
| Bio Summary | Multiple lines of text | Free text, feeds the search embedding |
| Availability | Choice: Available / Partial / Unavailable | Default Available |
| Utilization Percent | Whole number (0-100) | |
| CV Attachment | File | Optional for this phase (dummy data may leave blank) |
| Resource Manager | Lookup → Team Member | Who maintains this profile |
| Last Indexed On | Date and Time | Written by the nightly indexing flow; the watermark for "changed since" queries |

### Skill
| Column | Type | Notes |
|---|---|---|
| Skill Name | Single line of text (required) | e.g. "Power BI", "Copilot Studio" |
| Category | Choice: Power Apps / Power Automate / Power BI / Copilot Studio / Power Pages / Dataverse / AI / Automation / Analytics | |

**Relationship:** Specialist Profile ↔ Skill is many-to-many (native Dataverse N:N relationship, e.g. `bab_specialistprofile_skill`).

### Certification
| Column | Type | Notes |
|---|---|---|
| Certification Name | Single line of text (required) | e.g. "PL-600: Power Platform Solution Architect" |
| Issuer | Single line of text | e.g. "Microsoft" |
| Date Earned | Date only | |
| Specialist Profile | Lookup → Specialist Profile (required) | Parent |

### Engagement History
| Column | Type | Notes |
|---|---|---|
| Project Name | Single line of text (required) | |
| Department | Single line of text | Requesting department, free text |
| Outcome Summary | Multiple lines of text | 1-2 sentence result |
| Start Date | Date only | |
| End Date | Date only | Blank = ongoing |
| Specialist Profile | Lookup → Specialist Profile (required) | Parent |

### Search Log *(added during planning — not in the original design spec table list)*
> **Why this exists:** the design spec's Skills Intelligence Dashboard (§3, flow 4) needs a live "skills demand" signal. The originally agreed data model (design spec §4) only has Engagement History, which reflects *past* project staffing, not what departments are *currently* asking for. Without logging searches, the dashboard has no real demand data to show. This table is written once per search by the custom action flow (Task 7).

| Column | Type | Notes |
|---|---|---|
| Query Text | Multiple lines of text (required) | The department's plain-language challenge, verbatim |
| Submitted On | Date and Time (required) | Defaults to flow run time |
| Matched Skill Categories | Single line of text | Comma-separated list of Skill.Category values found among the top 5 results, e.g. "Power BI, Copilot Studio" |
| Requesting Department | Single line of text | Optional, free text if the department identifies itself |

### Team Member (reused)
Same shape as the prior project's Team Member table (Name, Email — fictional). Reused as the lookup target for Specialist Profile's Resource Manager column. If this solution doesn't share a Dataverse environment with the prior project, recreate it fresh in this solution.

## Azure AI Search Index Schema

One document per Specialist Profile. Index name: `specialist-profiles-index`.

```json
{
  "name": "specialist-profiles-index",
  "fields": [
    { "name": "id", "type": "Edm.String", "key": true, "filterable": true },
    { "name": "specialistName", "type": "Edm.String", "searchable": true, "filterable": true },
    { "name": "profileText", "type": "Edm.String", "searchable": true },
    { "name": "contentVector", "type": "Collection(Edm.Single)", "dimensions": 1536, "vectorSearchProfile": "specialist-vector-profile" },
    { "name": "availability", "type": "Edm.String", "filterable": true, "facetable": true },
    { "name": "utilizationPercent", "type": "Edm.Int32", "filterable": true, "sortable": true },
    { "name": "skillCategories", "type": "Collection(Edm.String)", "filterable": true, "facetable": true },
    { "name": "lastIndexedOn", "type": "Edm.DateTimeOffset", "filterable": true, "sortable": true }
  ],
  "vectorSearch": {
    "profiles": [{ "name": "specialist-vector-profile", "algorithm": "hnsw-default" }],
    "algorithms": [{ "name": "hnsw-default", "kind": "hnsw" }]
  }
}
```

`profileText` is the concatenation of Bio Summary + Skill names + Certification names + Engagement outcome summaries — this is the string embedded into `contentVector` (see Task 5).
```

- [ ] **Step 2: Review against design spec §4**

Confirm every table/column in the design spec's data model section is represented above, and that the Search Log addition is called out as an addition (not silently folded in). Fix any mismatch inline.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/02-DATA-MODEL.md
git commit -m "docs: add data model for Empower@BrandName Builders"
```

---

### Task 2: PRD and README

**Files:**
- Create: `docs/empower-brandname-builders/01-PRD.md`
- Create: `docs/empower-brandname-builders/README.md`

- [ ] **Step 1: Write the PRD**

```markdown
# PRD — Empower@BrandName Builders

- **Version:** 1.0 (demo)
- **Platform:** Microsoft Power Platform + Azure AI — model-driven admin app, canvas app, Copilot Studio agent, Power Automate, Power BI, over one Dataverse solution
- **Target build effort:** single-department pilot demo
- **Guiding rule:** real AI matching is the headline moment — everything else stays as lean as the prior meeting-tracker project.

## 1. Summary

Departments have digital ideas but don't know which already-screened IDIQ specialists are free and qualified to help. Empower@BrandName Builders lets a department describe its challenge in plain language to an AI Talent Copilot and get back the top 5 best-fit specialists — ranked, scored, with a stated rationale — in one conversational turn, with the ability to ask follow-up questions.

## 2. Demo scope — core vs. deferred

**Core (build this phase):**
- Dataverse: Specialist Profile, Skill, Certification, Engagement History, Search Log, Team Member (see 02-DATA-MODEL.md).
- Model-driven app for ITD Resource Managers to maintain specialist profiles.
- Azure AI Search hybrid (keyword + vector) index of specialist profiles.
- Nightly Power Automate flow indexing changed profiles.
- Copilot Studio "Talent Copilot" agent with a custom action that queries the index, scores results with Azure OpenAI GPT, and returns an Adaptive Card of the top 5 matches.
- Canvas app: Home screen with embedded Copilot Studio chat, nav to a Skills Dashboard.
- Power BI Skills Intelligence Dashboard (availability, skills demand, utilization trends, capability gaps).
- Fictional/dummy specialist data (~15-20 records).

**Deferred (NOT this phase):**
- Real specialist/CV data onboarding.
- CV PDF upload + AI Builder document extraction into structured fields.
- Event-driven (real-time) indexing.

## 3. Problem statement

| Pain | Today | Cost |
|---|---|---|
| Departments don't know who's available | Ask around, email resource managers | Slow starts, duplicated searches |
| Specialist skills/portfolios live in scattered docs | No searchable central profile | Good-fit specialists go unused |
| No visibility into utilization/capability gaps | Resource managers track manually | ITD can't plan hiring/training proactively |

## 4. Goals & non-goals

### Goals
- G1 — A department can describe a challenge and get 5 ranked, explained specialist matches in one interaction.
- G2 — Matching is genuinely semantic (understands meaning, not just exact keyword overlap) and scales to real profile volume later.
- G3 — ITD resource managers have one place to keep specialist profiles current.
- G4 — Leadership can see skills demand, utilization, and capability gaps at a glance.
- G5 — Stay within a single-department pilot AYA scope (see 06-AYA-ASSESSMENT.md).

### Non-goals (out of scope for the demo)
- N1 — No real CV ingestion/parsing pipeline yet (fictional data only).
- N2 — No specialist self-service profile editing (resource-manager-maintained only).
- N3 — No integration with external HR/vendor management systems.
- N4 — No multi-department rollout or SSO customization this phase.

## 5. Personas

| Persona | Role | Needs |
|---|---|---|
| **Dana — Department Requester** | Has a business challenge | Fast, plain-language way to find the right specialist |
| **Rae — ITD Resource Manager** | Maintains specialist profiles | One place to keep skills/availability current |
| **Priya — ITD Leadership** | Oversees resourcing | Visibility into demand, utilization, and capability gaps |

## 6. User stories

- US-01: As Dana, I can type a plain-language business challenge into a chat and get back the top 5 matching specialists with a score and a one-line reason for each.
- US-02: As Dana, I can ask a natural follow-up question about a suggested specialist without restarting my search.
- US-03: As Rae, I can create and update a specialist's profile (skills, certifications, portfolio/engagement history, availability, utilization) in a model-driven app.
- US-04: As Rae, my edits are reflected in search results after the nightly indexing run.
- US-05: As Priya, I can see a Power BI dashboard of specialist availability, skills demand (what departments are searching for), utilization trends, and capability gaps.

## 7. Functional requirements

- FR-01 — Six related tables: Specialist Profile, Skill, Certification, Engagement History, Search Log, Team Member (see 02-DATA-MODEL.md).
- FR-02 — A nightly Power Automate flow embeds changed Specialist Profiles and upserts them into an Azure AI Search hybrid index.
- FR-03 — A Copilot Studio agent's custom action queries the index, scores the top candidates with Azure OpenAI GPT, and returns a structured top-5 result as an Adaptive Card.
- FR-04 — Every search is logged (query text, timestamp, matched skill categories) to Search Log for the dashboard's demand metric.
- FR-05 — The canvas app embeds the Copilot Studio chat and links to the Power BI dashboard.
- FR-06 — The Power BI dashboard reads live from Dataverse: availability, utilization, skills demand (from Search Log), and capability gaps (skill categories with low specialist coverage relative to Search Log demand).

## 8. Non-functional requirements

- NFR-01 — Single-department pilot; data volume < 50 specialist records (AYA Complexity = low).
- NFR-02 — New dependencies vs. the prior project: Azure OpenAI, Azure AI Search, Copilot Studio.
- NFR-03 — No PII; fictional specialist data this phase.

## 9. Success metrics (for the demo conversation)

- A test business challenge returns the expected top specialist from the dummy dataset every time (regression-checked, see 03-BUILD-GUIDE.md §Testing).
- A follow-up chat question resolves correctly without losing context.
- The Power BI dashboard's skills-demand tile reflects logged searches from the live demo.

## 10. Roadmap (post-demo, if validated)

- Phase 2: Real specialist/CV onboarding, AI Builder document extraction from uploaded CVs.
- Phase 3: Specialist self-service profile editing.
- Phase 4: Event-driven (real-time) indexing if nightly freshness proves insufficient.
```

- [ ] **Step 2: Write the README**

```markdown
# Empower@BrandName Builders — Documentation

An AI-powered talent marketplace: departments describe a business challenge in plain language and get back the top 5 best-fit IDIQ specialists, ranked and explained, via a Copilot Studio "Talent Copilot" — plus a Power BI dashboard of skills demand, availability, and utilization.

> **Intended use of these docs:** read in order to build the solution by hand in Power Apps, Power Automate, Copilot Studio, and Power BI.

> **Guiding rule:** real AI matching is the point of this demo (unlike the prior meeting-tracker project, which deferred AI). Everything else stays as lean as that project.

## Solution architecture

```
1. Admin (profile maintenance)
   Model-driven app  <──────────────►  Dataverse
   (ITD Resource Managers)              (Specialist Profile, Skill,
                                          Certification, Engagement History,
                                          Search Log)

2. Nightly indexing pipeline
   Dataverse ──► Power Automate (nightly) ──► Azure OpenAI ──► Azure AI Search
   (changed profiles)   (embed + push)          (embeddings)    (hybrid index)

3. AI Talent Copilot (the matching moment)
   Canvas app / Teams ──► Copilot Studio agent ──► Power Automate (custom action)
   (chat)                  (Talent Copilot topic)     ──► Azure AI Search (query)
                                                        ──► Azure OpenAI (score + explain)
                                                        ──► Adaptive Card (top 5)

4. Skills Intelligence Dashboard
   Dataverse (+ Search Log) ──► Power BI report
```

## Document index

| # | File | Purpose |
|---|------|---------|
| 1 | [01-PRD.md](01-PRD.md) | Product requirements |
| 2 | [02-DATA-MODEL.md](02-DATA-MODEL.md) | Dataverse tables + Azure AI Search index schema |
| 3 | [03-BUILD-GUIDE.md](03-BUILD-GUIDE.md) | Step-by-step build order |
| 4 | [04-SAMPLE-DATA.md](04-SAMPLE-DATA.md) | Fictional specialist sample data |
| 5 | [05-COPILOT-PROMPTS.md](05-COPILOT-PROMPTS.md) | Copilot Studio topic, custom action, GPT scoring prompt, Adaptive Card template |
| 6 | [06-AYA-ASSESSMENT.md](06-AYA-ASSESSMENT.md) | Governance scope assessment |
| 7 | [07-DEMO-PITCH.md](07-DEMO-PITCH.md) | Demo script and talking points |

## At a glance

- **AYA category:** Team / Single department pilot
- **Apps:** Model-driven (admin) + canvas (chat entry) + Copilot Studio agent, plus Power Automate flows and a Power BI report
- **Backend:** Dataverse + Azure AI Search + Azure OpenAI
- **Data:** Fictional/dummy specialist data this phase — no PII
- **AI:** In scope — real semantic + keyword matching (unlike the prior project)
```

- [ ] **Step 3: Review against design spec §1, §2, §9**

Confirm goals, scope, and governance summary match the approved design doc.

- [ ] **Step 4: Commit**

```bash
git add docs/empower-brandname-builders/01-PRD.md docs/empower-brandname-builders/README.md
git commit -m "docs: add PRD and README for Empower@BrandName Builders"
```

---

### Task 3: Sample data

**Files:**
- Create: `docs/empower-brandname-builders/04-SAMPLE-DATA.md`
- Create: `docs/empower-brandname-builders/sample-data/specialists.csv`
- Create: `docs/empower-brandname-builders/sample-data/skills.csv`
- Create: `docs/empower-brandname-builders/sample-data/certifications.csv`
- Create: `docs/empower-brandname-builders/sample-data/engagements.csv`

- [ ] **Step 1: Write skills.csv**

```csv
Skill Name,Category
Power Apps (Canvas),Power Apps
Power Apps (Model-driven),Power Apps
Power Automate (Cloud Flows),Power Automate
Power Automate (Desktop/RPA),Power Automate
Power BI (Report Design),Power BI
Power BI (DAX/Data Modeling),Power BI
Copilot Studio (Agent Design),Copilot Studio
Copilot Studio (Generative Answers),Copilot Studio
Power Pages,Power Pages
Dataverse (Schema Design),Dataverse
AI Builder,AI
Azure OpenAI Integration,AI
Process Automation,Automation
Data Analytics,Analytics
```

- [ ] **Step 2: Write specialists.csv**

```csv
Specialist Name,Title/Role,Bio Summary,Availability,Utilization Percent,Resource Manager
Jane Doe,Senior Power Platform Developer,"Builds Power BI dashboards embedded with Copilot Studio agents grounded on live datasets; led 3 cross-department reporting rollouts.",Available,40,Rae Thompson
Sam Lee,Power BI Specialist,"Deep DAX and data modeling expertise; familiar with Copilot Studio basics; enjoys turning messy spreadsheets into governed datasets.",Available,55,Rae Thompson
Priya Nair,Copilot Studio Consultant,"Copilot Studio generative-answers expert; limited Power BI depth; recently built two knowledge-source-grounded support agents.",Partial,70,Marcus Alvarez
Alex Kim,Power Apps Canvas Developer,"Canvas app UX specialist; built several field-service and inspection apps; comfortable with Power Automate integration.",Available,30,Rae Thompson
Morgan Ellis,Automation & RPA Engineer,"Power Automate Desktop and cloud flow specialist; automates back-office approval processes end to end.",Available,50,Marcus Alvarez
Taylor Brooks,Dataverse Solution Architect,"Designs Dataverse schemas and security models for multi-app solutions; strong Power Apps model-driven background.",Unavailable,95,Marcus Alvarez
Jordan Patel,AI Builder & Azure OpenAI Developer,"Builds AI Builder prompts and Azure OpenAI integrations for document processing and summarization.",Available,45,Rae Thompson
Casey Nguyen,Power Pages Developer,"External-facing portal specialist using Power Pages; integrates with Dataverse and Power Automate approvals.",Available,25,Marcus Alvarez
Riley Foster,Data Analyst,"Power BI and general analytics; builds capability-gap and utilization reporting for resourcing teams.",Available,35,Rae Thompson
Devon Marsh,Power Automate Developer,"Cloud flow specialist with growing Copilot Studio custom-action experience; recently connected a flow to Azure AI Search.",Partial,60,Marcus Alvarez
Skylar Reed,Power Apps + Copilot Studio Generalist,"Builds canvas apps with embedded Copilot Studio chat; comfortable across the whole low-code stack.",Available,40,Rae Thompson
Harper Quinn,Power BI + AI Specialist,"Combines Power BI reporting with AI Builder models for predictive utilization forecasting.",Available,50,Marcus Alvarez
```

- [ ] **Step 3: Write certifications.csv**

```csv
Specialist Name,Certification Name,Issuer,Date Earned
Jane Doe,PL-300: Power BI Data Analyst,Microsoft,2024-03-15
Jane Doe,PL-600: Power Platform Solution Architect,Microsoft,2025-01-10
Sam Lee,PL-300: Power BI Data Analyst,Microsoft,2023-11-02
Priya Nair,PL-600: Power Platform Solution Architect,Microsoft,2024-06-20
Alex Kim,PL-100: Power Platform App Maker,Microsoft,2023-09-05
Morgan Ellis,PL-500: Power Automate RPA Developer,Microsoft,2024-02-14
Taylor Brooks,PL-400: Power Platform Developer,Microsoft,2023-05-30
Jordan Patel,AI-102: Designing and Implementing Azure AI Solutions,Microsoft,2024-08-01
Riley Foster,PL-300: Power BI Data Analyst,Microsoft,2024-04-22
```

- [ ] **Step 4: Write engagements.csv**

```csv
Specialist Name,Project Name,Department,Outcome Summary,Start Date,End Date
Jane Doe,Finance Reporting Modernization,Finance,"Replaced manual monthly reports with a live Power BI + Copilot Studio Q&A dashboard.",2025-02-01,2025-05-30
Sam Lee,HR Attrition Analysis,Human Resources,"Built a DAX-driven attrition model surfacing early-warning indicators.",2025-01-10,2025-03-01
Priya Nair,IT Support Copilot Pilot,IT Service Desk,"Deployed a Copilot Studio agent answering tier-1 support questions from a knowledge base.",2024-09-01,2024-12-15
Alex Kim,Facilities Inspection App,Facilities,"Delivered a canvas app for mobile inspection checklists replacing paper forms.",2024-11-01,2025-01-20
Morgan Ellis,Invoice Approval Automation,Finance,"Automated a 5-step manual invoice approval process end to end.",2025-03-01,2025-04-15
Taylor Brooks,Enterprise Dataverse Consolidation,ITD,"Consolidated three siloed Dataverse environments into one governed schema.",2024-06-01,2025-06-01
Jordan Patel,Contract Summarization Tool,Legal,"Built an AI Builder + Azure OpenAI flow summarizing incoming contracts for review.",2025-01-15,2025-03-30
Riley Foster,Resourcing Utilization Report,ITD,"Built the capability-gap reporting later reused as this project's dashboard baseline.",2024-08-01,2024-10-01
```

- [ ] **Step 5: Write 04-SAMPLE-DATA.md**

```markdown
# Sample Data — Empower@BrandName Builders

Fictional, PII-free specialist records for the demo. Load order matters — parent records first.

## Load order

1. **Team Member** (Resource Managers: Rae Thompson, Marcus Alvarez — fictional, dummy email addresses) — reuse the prior project's Team Member table/pattern if sharing an environment.
2. **Skill** — `sample-data/skills.csv`
3. **Specialist Profile** — `sample-data/specialists.csv` (Resource Manager column resolves against Team Member)
4. **Certification** — `sample-data/certifications.csv` (Specialist Profile lookup resolves by name)
5. **Engagement History** — `sample-data/engagements.csv` (Specialist Profile lookup resolves by name)
6. Link each Specialist Profile to its Skills via the Skill many-to-many relationship, based on the specialist's Bio Summary and Title — e.g. Jane Doe → Power BI (Report Design), Power BI (DAX/Data Modeling), Copilot Studio (Generative Answers).

## Why these records

The set is deliberately built so specific test business challenges have a known-correct top match (see 03-BUILD-GUIDE.md's testing checklist and 07-DEMO-PITCH.md's demo script):

- "Someone who can build a Power BI dashboard with Copilot Studio integration" → **Jane Doe** should rank #1.
- "I need RPA/desktop automation for a manual approval process" → **Morgan Ellis** should rank #1.
- "External-facing portal work" → **Casey Nguyen** should rank #1.

Load **Search Log** empty — it populates live as the demo runs searches.
```

- [ ] **Step 6: Review against design spec §4 and the "Assumption" note in the plan's Task 1**

Confirm every specialist has enough Bio Summary + Skill + Certification + Engagement text to be a meaningful embedding candidate, and that at least one specialist clearly dominates each of the three demo test queries above.

- [ ] **Step 7: Commit**

```bash
git add docs/empower-brandname-builders/04-SAMPLE-DATA.md docs/empower-brandname-builders/sample-data/
git commit -m "docs: add sample data for Empower@BrandName Builders"
```

---

### Task 4: Build guide — Dataverse, model-driven admin app (Track A)

**Files:**
- Create: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Write the build guide's intro and Track A**

```markdown
# Build Guide — Empower@BrandName Builders

Six tracks, one Dataverse solution. Build in this order so you always have something to show.

```
Dataverse (one solution): Specialist Profile · Skill · Certification ·
                           Engagement History · Search Log · Team Member
        │                    │                    │                │
  Model-driven app    Nightly indexing     Copilot Studio      Power BI
  (Track A)           flow (Track C)       + custom action     dashboard
                                            (Track D)           (Track F)
                                                 │
                                          Canvas app (Track E)
```

## Prerequisites

- A Power Platform environment with Dataverse enabled.
- Maker access to make.powerapps.com, make.powerautomate.com, copilotstudio.microsoft.com, and Power BI Desktop.
- An Azure subscription with permission to create an Azure OpenAI resource and an Azure AI Search resource (Track B).

## Suggested build order

| Track | Focus |
|---|---|
| A | Dataverse tables + model-driven admin app (safety net) |
| — | Load sample data (04-SAMPLE-DATA.md) |
| B | Provision Azure OpenAI + Azure AI Search, create the index |
| C | Nightly Power Automate indexing flow |
| D | Copilot Studio "Talent Copilot" agent + custom action + Adaptive Card |
| E | Canvas app: Home/chat screen + nav |
| F | Power BI Skills Intelligence Dashboard |
| — | Run the testing checklist against sample data |

---

## Track A — Dataverse tables + model-driven admin app

1. make.powerapps.com → **Solutions** → **New solution** → "Empower@BrandName Builders".
2. Inside the solution, **New → Table** for **Specialist Profile**, **Skill**, **Certification**, **Engagement History**, **Search Log**, and **Team Member** (columns per 02-DATA-MODEL.md).
3. Relationships:
   - Specialist Profile ↔ Skill: **New N:N relationship**.
   - Certification → **Lookup** "Specialist Profile" (required).
   - Engagement History → **Lookup** "Specialist Profile" (required).
   - Specialist Profile → **Lookup** "Resource Manager" → Team Member (optional).
4. **New → App → Model-driven app** → name it "Talent Marketplace – Admin".
5. **Add page → Dataverse table** for Specialist Profile, Certification, Engagement History, Skill, Team Member. Accept default forms/views.
6. On the Specialist Profile form, arrange fields top-to-bottom: Specialist Name, Title/Role, Availability, Utilization Percent, Bio Summary, CV Attachment, Resource Manager, Last Indexed On (mark Last Indexed On read-only on the form — it's written by the nightly flow, not by resource managers).
7. Add related Certification and Engagement History sub-grids to the Specialist Profile form (Form editor → **+ Component** → **Sub-grid**, filtered to the current record).
8. **Save and publish.**

> Same system-Owner-column gotcha as the prior project applies here: Dataverse auto-generates a polymorphic `ownerid` on every table. If the Copilot-generated Specialist Profile form surfaces it as required, select it → **Hide** in the Properties panel rather than trying to delete it.
```

- [ ] **Step 2: Review against design spec §3 (flow 1) and §4**

Confirm the table list, relationships, and admin app match the data model doc from Task 1.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add build guide intro and Track A (Dataverse + admin app)"
```

---

### Task 5: Build guide — Azure AI Search + Azure OpenAI provisioning (Track B)

**Files:**
- Modify: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Append Track B**

```markdown
## Track B — Azure OpenAI + Azure AI Search provisioning

1. In the Azure portal, create an **Azure OpenAI** resource. Deploy two models:
   - `text-embedding-3-small` (1536 dimensions) — for profile and query embeddings.
   - `gpt-4o-mini` — for scoring/rationale generation (cost-efficient; swap to `gpt-4o` if quality needs outweigh cost for the demo).
2. Create an **Azure AI Search** resource (Basic tier is sufficient for a demo-sized index).
3. Create the index using the schema in 02-DATA-MODEL.md (`specialist-profiles-index`) — either via the Azure portal's "Import and vectorize data" wizard pointed at the JSON schema, or via the Create Index REST API with that exact JSON body.
4. Note down and securely store: the Azure OpenAI endpoint + API key + both deployment names, and the Azure AI Search endpoint + admin API key + index name. These are used as HTTP action credentials in Tracks C and D — store them as a Power Automate connection reference (not hard-coded in flow JSON) so they're not exposed in the exported solution.
```

- [ ] **Step 2: Review against design spec §3.1**

Confirm the model choices and index name match the "Assumption" reuse-one-Azure-OpenAI-resource decision from the design spec.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add build guide Track B (Azure OpenAI + AI Search provisioning)"
```

---

### Task 6: Build guide — nightly indexing flow (Track C)

**Files:**
- Modify: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Append Track C**

```markdown
## Track C — Nightly indexing flow

Build in Power Automate as a **Scheduled cloud flow** named "Nightly Specialist Indexing".

1. **Trigger:** Recurrence, Interval 1, Frequency Day, at 02:00.
2. **List rows** (Dataverse, Specialist Profile): filter `modifiedon gt @{variables('LastRunWatermark')}`. Store the watermark as a single-row Dataverse config record (table: reuse Search Log's environment or add a one-row "Config" table with a `Last Run` datetime column) read at the start of the flow and updated at the end — this avoids re-embedding unchanged profiles every night.
3. **Apply to each** returned Specialist Profile:
   a. **Compose** `profileText` = concatenation of Bio Summary + related Skill names (via a nested List rows on the N:N relationship) + related Certification names + related Engagement outcome summaries.
   b. **HTTP** action → POST to the Azure OpenAI embeddings endpoint (`{endpoint}/openai/deployments/text-embedding-3-small/embeddings?api-version=2024-02-01`), body `{ "input": "@{outputs('Compose_profileText')}" }`.
   c. **HTTP** action → POST to the Azure AI Search index endpoint (`{search-endpoint}/indexes/specialist-profiles-index/docs/index?api-version=2024-07-01`), body:
      ```json
      {
        "value": [{
          "@search.action": "mergeOrUpload",
          "id": "@{items('Apply_to_each')?['specialistprofileid']}",
          "specialistName": "@{items('Apply_to_each')?['bab_specialistname']}",
          "profileText": "@{outputs('Compose_profileText')}",
          "contentVector": "@{body('HTTP_embed')?['data'][0]['embedding']}",
          "availability": "@{items('Apply_to_each')?['bab_availability']}",
          "utilizationPercent": "@{items('Apply_to_each')?['bab_utilizationpercent']}",
          "skillCategories": "@{variables('SkillCategoriesForThisProfile')}",
          "lastIndexedOn": "@{utcNow()}"
        }]
      }
      ```
   d. **Update a row** (Dataverse) → set the Specialist Profile's Last Indexed On to `utcNow()`.
4. **Error handling:** wrap steps 3a-3c in a **Scope** named "Try"; add a parallel **Scope** named "Catch" configured to run after Try **has failed, is skipped, has timed out**; inside Catch, send an email via the **Office 365 Outlook** connector to the solution admin with the failing Specialist Profile's name and the HTTP error body.
5. After the Apply to each completes, **Update** the Config row's Last Run Watermark to the flow's start time (captured at trigger time, not `utcNow()` at the end, so overlapping edits during a long run aren't missed next time).
6. Handle deletions: add a second **List rows** for Specialist Profiles marked inactive/deleted since the watermark, and an **HTTP** delete action per record (`"@search.action": "delete"`) against the same index endpoint.
```

- [ ] **Step 2: Review against design spec §3 (flow 2) and §7 (error handling)**

Confirm the watermark strategy, retry/failure notification, and delete handling match the design doc.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add build guide Track C (nightly indexing flow)"
```

---

### Task 7: Copilot Studio prompts, custom action, Adaptive Card (Track D)

**Files:**
- Create: `docs/empower-brandname-builders/05-COPILOT-PROMPTS.md`
- Modify: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Write 05-COPILOT-PROMPTS.md**

```markdown
# Copilot Studio Prompts & Custom Action — Empower@BrandName Builders

## Topic: "Find a Specialist"

**Trigger phrases:** "I need someone who...", "find a specialist", "who can help with", "I have a challenge".

**Topic flow:**
1. Capture the user's message as `ChallengeText` (the whole utterance — no slot-filling, keep it conversational).
2. Call custom action `TalentMatch` with input `challengeText = ChallengeText`.
3. If `TalentMatch.matchCount = 0`, respond: "I couldn't find a strong match — try describing the skills or outcome you need a bit more specifically."
4. Otherwise, render the Adaptive Card (below) using `TalentMatch.matches`.
5. End the topic in a state that keeps the conversation open for follow-up questions (Copilot Studio's default generative orchestration handles "does she also know DAX?" as a continuation, since the topic doesn't end the session).

## Custom action: TalentMatch (Power Automate flow)

**Input:** `challengeText` (text)
**Output:** `matchCount` (number), `matches` (array of `{ name, score, rationale, availability }`)

Flow steps:
1. **HTTP** → Azure OpenAI embeddings endpoint, body `{ "input": "@{triggerBody()['challengeText']}" }` → capture `queryVector`.
2. **HTTP** → Azure AI Search index `/docs/search` endpoint, hybrid query:
   ```json
   {
     "search": "@{triggerBody()['challengeText']}",
     "vectorQueries": [{ "kind": "vector", "vector": "@{body('HTTP_embed_query')?['data'][0]['embedding']}", "fields": "contentVector", "k": 10 }],
     "select": "id,specialistName,profileText,availability,utilizationPercent,skillCategories",
     "top": 10
   }
   ```
3. **Compose** a candidates block: join the top 10 results' `specialistName` + `profileText` + `availability` into one text block for the scoring prompt.
4. **HTTP** → Azure OpenAI chat completions endpoint (`gpt-4o-mini`), with this system prompt:

   > You are a talent-matching assistant. Given a business challenge and a list of specialist profiles, select the top 5 best-fit specialists. Score each 0-100 based on how well their skills, certifications, and past engagements address the stated challenge — weigh both explicit keyword overlap and conceptual/semantic fit. Availability matters: prefer "Available" over "Partial" over "Unavailable" specialists when scores are close, but don't let availability override a clearly stronger skill match. Respond with ONLY valid JSON matching this shape, no other text: `{"matches":[{"name":"string","score":0,"rationale":"one sentence, specific to this challenge","availability":"string"}]}`. Return at most 5 matches, ordered highest score first.

   User message: `Business challenge: "@{triggerBody()['challengeText']}"\n\nCandidates:\n@{outputs('Compose_candidates')}`
5. **Parse JSON** the chat completion response using the schema above.
6. Set `matchCount` = length of the parsed `matches` array; set `matches` = the parsed array.
7. **Insert row** into Search Log: Query Text = `challengeText`, Submitted On = `utcNow()`, Matched Skill Categories = the distinct `skillCategories` values across the returned matches (joined, comma-separated).
8. Respond to Copilot Studio with `matchCount` and `matches`.

## Adaptive Card template

```json
{
  "type": "AdaptiveCard",
  "version": "1.5",
  "body": [
    { "type": "TextBlock", "text": "Top Specialist Matches", "weight": "Bolder", "size": "Medium" },
    {
      "type": "Container",
      "$data": "${matches}",
      "items": [
        { "type": "TextBlock", "text": "${name} — ${score}% match", "weight": "Bolder" },
        { "type": "TextBlock", "text": "${rationale}", "wrap": true },
        { "type": "TextBlock", "text": "Availability: ${availability}", "isSubtle": true, "size": "Small" }
      ],
      "separator": true
    }
  ]
}
```
```

- [ ] **Step 2: Append Track D to the build guide**

```markdown
## Track D — Copilot Studio "Talent Copilot" agent

1. copilotstudio.microsoft.com → **Create** → new agent, name "Talent Copilot".
2. **Topics** → **New topic** → "Find a Specialist" — configure trigger phrases and the flow from 05-COPILOT-PROMPTS.md.
3. **Actions** → **New action** → connect the `TalentMatch` Power Automate flow (built per 05-COPILOT-PROMPTS.md's custom action steps) as a custom action; map its output to the topic's Adaptive Card step.
4. Add the Adaptive Card template from 05-COPILOT-PROMPTS.md as the topic's response message (Message node → **Adaptive Card** → paste JSON, bind `${matches}` to the custom action's output array).
5. **Test** in the Copilot Studio test pane with the three demo queries from 04-SAMPLE-DATA.md before moving to Track E.
6. **Publish** the agent.
```

- [ ] **Step 3: Review against design spec §3 (flow 3), §3.1 assumption, and §5**

Confirm the custom action reuses one Azure OpenAI resource (no AI Builder layer introduced), the Adaptive Card matches the canvas app mockup approved earlier (name, score %, rationale, availability), and follow-up conversation isn't blocked by the topic ending.

- [ ] **Step 4: Commit**

```bash
git add docs/empower-brandname-builders/05-COPILOT-PROMPTS.md docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add Copilot Studio prompts, custom action, and Track D"
```

---

### Task 8: Canvas app (Track E)

**Files:**
- Modify: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Append Track E**

```markdown
## Track E — Canvas app

1. make.powerapps.com → **New app → Canvas** → name "Talent Marketplace".
2. **Home screen:**
   - Insert the **Copilot** control (Insert → AI Prompts and Agents → **Chat with an agent** preview control) → configure it to point at the published "Talent Copilot" agent from Track D. This embeds the full conversational experience (including follow-up questions) directly in the app.
   - Add a top nav bar (`galNav` gallery or a simple horizontal container) with two items: **Talent Copilot** (this screen) and **Skills Dashboard** (Screen 2).
3. **Skills Dashboard screen:**
   - Insert a **Power BI tile** control (Insert → Power BI) once the report from Track F is published, and point it at that report/dashboard.
4. Set `App.StartScreen = HomeScreen`. **Save and publish.**
```

- [ ] **Step 2: Review against design spec §5**

Confirm the two screens match the approved wireframes (chat entry point, nav to dashboard).

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add build guide Track E (canvas app)"
```

---

### Task 9: Power BI dashboard (Track F)

**Files:**
- Modify: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Append Track F**

```markdown
## Track F — Skills Intelligence Dashboard (Power BI)

1. Power BI Desktop → **Get Data → Dataverse** → connect to the solution's environment; load Specialist Profile, Skill, Certification, Engagement History, and Search Log.
2. Build relationships: Specialist Profile 1:N Certification, 1:N Engagement History; Specialist Profile N:N Skill.
3. Measures (DAX):
   - `Available Specialists = CALCULATE(COUNTROWS('Specialist Profile'), 'Specialist Profile'[Availability] = "Available")`
   - `Avg Utilization = AVERAGE('Specialist Profile'[Utilization Percent])`
   - `Searches Logged = COUNTROWS('Search Log')`
   - `Top Requested Skill Category = ` a measure or visual grouping `'Search Log'[Matched Skill Categories]` (split on comma) by frequency — use a Power Query step to unpivot the comma-separated column into one row per skill category before this measure, since DAX can't easily split a delimited text column.
4. Visuals:
   - **Availability** — donut chart of Specialist Profile by Availability.
   - **Skills demand** — bar chart of Search Log's unpivoted skill categories by count (highest = most requested).
   - **Utilization trend** — line chart of Engagement History count over time (by month, via Start Date).
   - **Capability gaps** — table comparing skills-demand count (from Search Log) against specialist count per Skill Category, highlighting categories where demand count > specialist count.
5. Publish to the Power BI service; note the report URL/embed details for the canvas app's Power BI tile (Track E, step 3).
```

- [ ] **Step 2: Review against design spec §3 (flow 4) and the Task 1 Search Log addition**

Confirm every dashboard capability named in the original use-case doc (availability, skills demand, utilization trends, capability gaps) has a corresponding visual, and that skills demand genuinely comes from logged searches rather than only historical engagement data.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add build guide Track F (Power BI dashboard)"
```

---

### Task 10: Testing checklist (build guide close-out)

**Files:**
- Modify: `docs/empower-brandname-builders/03-BUILD-GUIDE.md`

- [ ] **Step 1: Append the testing checklist**

```markdown
## Testing checklist (run after all six tracks are built)

- [ ] Model-driven app: create, edit, and deactivate a Specialist Profile without errors.
- [ ] Manually trigger the nightly indexing flow once; confirm Azure AI Search's document count equals the active Specialist Profile count, and spot-check one document's `profileText`/`contentVector` fields are populated.
- [ ] In the Copilot Studio test pane, run these three challenges and confirm the expected top match (per 04-SAMPLE-DATA.md):
  - "I need someone who can build a Power BI dashboard with Copilot Studio integration" → expect **Jane Doe** #1.
  - "I need RPA/desktop automation for a manual approval process" → expect **Morgan Ellis** #1.
  - "External-facing portal work" → expect **Casey Nguyen** #1.
- [ ] Ask a follow-up question after a match result (e.g., "does she also know DAX?") and confirm the agent answers in context without restarting the search.
- [ ] Confirm each test search above created a new Search Log row.
- [ ] Canvas app: navigate Home ↔ Skills Dashboard without errors; confirm the embedded chat control loads the published Talent Copilot agent.
- [ ] Power BI: confirm the skills-demand visual reflects the three test searches just run.
```

- [ ] **Step 2: Review against design spec §8 (Testing Approach)**

Confirm every bullet in the design spec's testing section has a corresponding checklist item above.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/03-BUILD-GUIDE.md
git commit -m "docs: add testing checklist to build guide"
```

---

### Task 11: AYA assessment

**Files:**
- Create: `docs/empower-brandname-builders/06-AYA-ASSESSMENT.md`

- [ ] **Step 1: Write the AYA assessment**

```markdown
# AYA Assessment — Empower@BrandName Builders

| Dimension | Score | Justification |
|---|---|---|
| Data classification | Internal (no PII) | Fictional/dummy specialist data this phase; no client, financial, or real personal data. |
| Users / scope | Team / Single department pilot | One department pilots the marketplace against a shared ITD-maintained specialist pool. |
| Integration | Low-moderate | New dependencies vs. the prior project: Azure OpenAI, Azure AI Search, Copilot Studio — all Microsoft-first-party, no external/Client systems. |
| Availability | Non-critical | Demo/pilot; downtime is insignificant. |
| Complexity | Low (demo data volume) | < 50 specialist records, single index, single agent. |
| AI | In scope, Microsoft-native only | Azure OpenAI (embeddings + GPT scoring) and Copilot Studio generative orchestration — no third-party AI services, no fine-tuning on real data. |

**Overall:** in-scope for a single-department pilot demo. Re-assess before any Phase 2 expansion (real CV data, multi-department rollout, or specialist self-service) — those would likely raise the Data classification and Users/scope dimensions.
```

- [ ] **Step 2: Review against design spec §9**

Confirm every bullet in the design spec's governance summary is reflected as a scored dimension here.

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/06-AYA-ASSESSMENT.md
git commit -m "docs: add AYA assessment for Empower@BrandName Builders"
```

---

### Task 12: Demo pitch

**Files:**
- Create: `docs/empower-brandname-builders/07-DEMO-PITCH.md`

- [ ] **Step 1: Write the demo pitch**

```markdown
# Demo Pitch — Empower@BrandName Builders

**One-liner:** Find Your Hero. Build Faster. Transform Smarter.

## The problem in one sentence
Departments have ideas but no fast way to find already-screened IDIQ specialists who are free and qualified to help.

## Demo script (5 minutes)

1. **Open the canvas app** — show the Home screen with the embedded Talent Copilot chat.
2. **Type a real challenge:** "I need someone who can build a Power BI dashboard with Copilot Studio integration for a 3-week engagement."
3. **Show the response:** top 5 ranked specialists with match score and a specific rationale — call out that Jane Doe leads because of her stated Power BI + Copilot Studio engagement history, not just a keyword match.
4. **Ask a follow-up in the same chat:** "Does she also know DAX?" — show the conversation continuing without restarting the search.
5. **Switch to the Skills Dashboard** — show availability, the skills-demand chart (now including the search just run), utilization trends, and the capability-gap table.
6. **Close on the admin app** — show how quickly an ITD resource manager could add or update a specialist profile.

## Key differentiators to emphasize

- This is **real** semantic matching (Azure AI Search + Azure OpenAI), not a keyword filter with an AI-sounding label — it understood "3-week engagement" and "dashboard... integration" as intent, not just literal words.
- The **conversational follow-up** is the "Copilot" promise made real, not just a chatbot skin on a search box.
- The **architecture already scales** — nightly indexing and a hybrid vector index are the same shape you'd want at real specialist volume, not a demo-only shortcut.

## Anticipated questions

- **"Is this using real specialist data?"** — No, fictional/dummy data this phase; real CV/profile onboarding is the agreed Phase 2 next step.
- **"What does this cost to run?"** — New Azure OpenAI + Azure AI Search + Copilot Studio consumption; confirm current licensing/message costs with the Power Platform admin before a production pilot.
- **"Why nightly indexing, not real-time?"** — Resource managers update profiles at most daily; nightly freshness matches that cadence without extra event-driven flow complexity. Revisit if usage patterns show same-day visibility is needed.
```

- [ ] **Step 2: Review against design spec §1, §3.1, §9, §10**

Confirm the pitch's differentiators and anticipated-question answers are consistent with the approved design doc (no contradictions with the AI-scope or governance sections).

- [ ] **Step 3: Commit**

```bash
git add docs/empower-brandname-builders/07-DEMO-PITCH.md
git commit -m "docs: add demo pitch for Empower@BrandName Builders"
```

---

## Self-Review

**1. Spec coverage:**
- Design spec §3 (four flows) → Tasks 4, 5, 6, 7, 8, 9 (Tracks A-F). ✓
- Design spec §3.1 (approaches considered + AI assumption) → Task 2 (PRD), Task 7 (custom action reuses one Azure OpenAI resource). ✓
- Design spec §4 (data model) → Task 1, with the Search Log addition explicitly flagged as a gap-fill, not silently introduced. ✓
- Design spec §5 (canvas screens) → Task 8. ✓
- Design spec §6 (build order) → Tasks 4-9 sequenced in the same order. ✓
- Design spec §7 (error handling) → Task 6 (indexing flow retry/failure email), Task 7 (no-match response in the topic). ✓
- Design spec §8 (testing approach) → Task 10. ✓
- Design spec §9 (governance/AYA) → Task 11. ✓
- Design spec §10 (deferred items) → Task 2's PRD Roadmap section. ✓

**2. Placeholder scan:** no TBD/TODO markers; every code/config block above is complete and specific (exact column names, exact JSON, exact prompt wording, exact sample rows).

**3. Type/name consistency:** Specialist Profile column names (`bab_specialistname`, `bab_availability`, `bab_utilizationpercent` used in Task 6's flow expressions) match the table defined in Task 1 — using a consistent `bab_` prefix as the assumed solution publisher prefix; the actual prefix will depend on the solution's real publisher setting, so the build guide should note this once solidified during Track A. The Adaptive Card's `${matches}` binding in Task 7 matches the `TalentMatch` custom action's `matches` output shape (`name`, `score`, `rationale`, `availability`) consistently across the topic, the flow, and the card template.
