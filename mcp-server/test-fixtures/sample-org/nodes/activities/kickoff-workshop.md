---
id: kickoff-workshop
type: activity
performer: tomas-reis
unit: client-services
description: "Run the kickoff workshop for every engagement: scope agreement, calendar, weekly cadence, single point of contact on client side."
fte: 0.1
artifacts: ["engagement-scope-doc"]
inputs: []
outputs: ["engagement-scope"]
stakeholders_touched: ["mid-market-clients", "enterprise-clients"]
frequency: "per engagement, at start"
sources: [outline-roles-2025, outline-charter-2024, tomas-interview-2026-05-07]

# Density layer — filled by interviewing Tomás on 2026-05-07.
# Coordination-bound activity; the cost is alignment across four discipline leads on day one.
trigger:
  - "Within 5 working days of contract signature. Tomás schedules from the calendar of the four discipline leads (Marco, Lena, the product lead, himself); the workshop is a 4-hour block."
quality_gates:
  - "All four discipline leads are present for the full 4 hours. If one is unavailable on every available date in the next 5 days, Tomás escalates to the founder before booking."
  - "The client side has named a single point of contact (one human, one email, one phone number) who has authority to approve scope and calendar. If the client offers \"a team\" or \"a few of us\", Tomás pushes back and waits for one name."
  - "On enterprise engagements, the founder also attends. Tomás confirms the founder's calendar before booking."
decision_criteria:
  - "Scope agreement reached at the workshop is binding on the studio's price. If the client introduces work outside the named scope at week 2+, that's a scope change conversation (escalates to the founder per charter §12), not a quiet expansion."
  - "Calendar cadence is non-negotiable: weekly check-in at a fixed day/time agreed in the workshop. Reschedules are allowed; deletions are not."
  - "Single-point-of-contact discipline: the client side names one human. If they want \"the marketing team\" to be the contact, Tomás declines; multiple contacts dilute scope drift detection."
output_format:
  description: "An engagement-scope document, 3-4 pages, structured as: (1) named deliverables (positioning, identity system, brand book, UI screens, design system documentation, asset handover — checked off per engagement), (2) calendar (week-by-week, naming who's responsible per week), (3) single point of contact (client-side and studio-side), (4) fixed-price quote tied to the named deliverables, (5) the change-of-scope clause referencing charter §12."
  example_artefact: "Each year's engagement-scope-docs are filed under the studio's project archive; the 2025 cohort produced 14 of them, all following the same template."
fallback:
  - condition: "Client refuses to name a single point of contact"
    action: "Tomás escalates to the founder. The founder either negotiates the SPOC (typical) or declines the engagement (rare, has happened twice in 2024-2025). The studio does not start work without a named SPOC."
  - condition: "One discipline lead can't make the kickoff and the other three can"
    action: "Reschedule. The studio does not run a kickoff with 3 of 4 leads present — the 4th will need a re-run within a week regardless, and that's a coordination tax the engagement can't afford."
  - condition: "Client wants to skip the workshop and 'just start'"
    action: "Tomás declines politely, explains the scope-change consequence, offers a 90-min compressed version. Skipping entirely is refused."
handoff:
  - "Within 24 hours of the workshop, Tomás writes the engagement-scope document and circulates it to the four leads + the client SPOC. Confirmation in writing required from all five within 48 hours."
  - "First weekly check-in is scheduled at the workshop, lands within 7 days. Tomás runs it; if Tomás is unavailable, an account manager runs it with the engagement-scope document open."
  - "The discipline lead present at the workshop owns the relationship with their counterparts on the client side from week 2 onwards. Tomás is the orchestrator, not the work-doer."
---

# Kickoff workshop

The client services lead runs the kickoff workshop for every engagement: scoping, calendar, weekly cadence agreement, single point of contact on the client side. The output is the engagement-scope document that anchors weekly check-ins, asset handovers, and the fixed-price agreement (outline-roles-2025, outline-charter-2024 §4, §12).

The relevant discipline lead sits at the kickoff alongside [Tomás Reis](../people/tomas-reis.md). Enterprise kickoffs additionally include the founder (outline-roles-2025).
