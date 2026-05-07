---
id: brand-positioning
type: activity
performer: marco-bellini
unit: strategy
description: "Author the positioning document for an engagement: how the client should be understood, against whom, with what proof points."
fte: 0.4
artifacts: ["positioning-brief"]
inputs: ["insights-document", "market-map"]
outputs: ["positioning-brief"]
stakeholders_touched: ["mid-market-clients", "enterprise-clients"]
frequency: "per engagement"
sources: [outline-roles-2025, outline-charter-2024, marco-interview-2026-05-07]

# Density layer — filled by interviewing Marco on 2026-05-07.
# Not derived from the description; testimony, transcript saved as marco-interview-2026-05-07.md.
trigger:
  - "After the kickoff workshop closes and audience-research synthesis lands. Typically week 2 of an engagement."
quality_gates:
  - "Audience-research synthesis includes ≥ 3 customer interviews + 1 stakeholder interview verbatim quotes; if missing, Marco delays positioning by a week and asks for a re-run."
  - "Competitive audit names ≥ 5 named competitors with their positioning verbatim from the competitor's own materials (not paraphrase)."
  - "The kickoff scope agreement explicitly names the audience the client wants to reach. If ambiguous (\"everybody\" / \"the market\"), Marco escalates to the founder before starting."
decision_criteria:
  - "Pick the positioning frame that creates the most narrow audience for which the client is unambiguously the right answer. Wider is not better."
  - "If two frames are plausible, the one with more cited proof points wins. Marco does not pick on aesthetics; he picks on what's defensible against a sceptical client review."
  - "Reject any frame that requires the client to credibly claim something they don't actually do today. Aspirational is allowed; not credible isn't."
  - "On enterprise engagements the founder reviews the positioning before it goes out. On mid-market the founder is informed; review is optional."
output_format:
  description: "8-12 page document, structured as: (1) audience definition (one paragraph + named demographics or firmographics); (2) the proposition (one sentence + three proof points each cited); (3) the against-whom (named competitors, what they say, what we say differently); (4) the why-now (cited market or behavioural shift); (5) the implication for identity (what tone, what vocabulary, what visual register the design lead should pick up)."
  example_artefact: "outline-roles-2025 references the 2024 'Vivaldi' engagement positioning brief as the canonical example (not committed to org/, lives in the studio's archive)"
fallback:
  - condition: "Audience-research synthesis is thin (< 3 interviews) and the client refuses to schedule more"
    action: "Marco writes a positioning brief that is explicitly conditional: 'This positioning is the best inference from limited testimony. Validate by month 6 with quarterly customer interviews; revisit if invalidated.' The conditional is named in the brief; the design lead is told to expect a possible revision."
  - condition: "Two competing positioning frames both pass the criteria above"
    action: "Marco presents both to the founder for arbitration. The founder chooses; Marco does not put it to a client vote."
handoff:
  - "Lena (design lead) reviews the positioning brief within 48 hours. The brief is not handed to identity-system-build until Lena signs off in writing — an email or a Slack thread, archived under the engagement folder."
  - "On enterprise engagements, after Lena signs off, the founder also signs off before identity work starts."
  - "If Lena flags an issue (e.g. the implication-for-identity section is too vague to design from), Marco rewrites the relevant section within 2 working days. No back-and-forth past two cycles — third cycle escalates to the founder."
---

# Brand positioning

The strategy lead writes the positioning document for every engagement. Inputs come from [audience research](audience-research.md) and the [competitive audit](competitive-audit.md); the output is a written brief that the [design lead](../people/lena-thorvaldsen.md) builds the identity system on top of (outline-roles-2025, outline-charter-2024 §1).

The artefact is owned by [Marco Bellini](../people/marco-bellini.md) and is not delegated — every positioning document goes out under his signature (outline-roles-2025).
