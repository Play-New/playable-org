---
name: interview-activity
description: "Fill the activity-density layer (trigger / quality_gates / decision_criteria / output_format / fallback / handoff) on a single activity, by interviewing the person who actually performs it. The transcript becomes a source. The activity gets the six fields it needs to be turned into a Claude skill (slash command) by compile-agent. One activity per session, one performer per session."
---

# Skill: interview-activity

The bridge between a structurally-described activity (the floor: who does what, with which inputs/outputs) and an activity that an agent can actually RUN as a skill (the ceiling: trigger, gates, decision criteria, output format, fallbacks, handoff). The bridge is interviewing the performer.

This skill produces no artefact other than:
- An updated `nodes/activities/<activity-id>.md` with the six density fields filled per `org/AGENTS.md`.
- A new source under `sources/<performer-id>-interview-<date>.md` containing the verbatim Q&A.
- A log entry naming what changed.

## Pre-conditions

- The activity already exists in `org/nodes/activities/<id>.md` with at least the structural frontmatter (description, performer, unit, inputs, outputs, frequency, sources). If those are missing, run `ingest` on a role-description document first to seed them.
- The performer is available for a 30-45 minute conversation. The interview is testimony; the performer is the source.
- The agent has read `org/AGENTS.md` (specifically the activity density layer schema) and `STYLE.md` (specifically the conditional-voice rule and the jargon avoid-list).

## What this skill does NOT do

- It does not infer the density fields from the description. The whole point is that the description is too thin; you have to ask the performer.
- It does not interview multiple performers in one session. One activity per session, one performer per session. If two people share an activity, two separate interviews; the schema accommodates both via additional source citations.
- It does not push the performer into language they wouldn't use. Their answers go in raw. The agent normalises into the schema after, citing the transcript.
- It does not skip cases where the performer says "it depends". `decision_criteria` should capture *what they look at* when making the call, not pretend the call is rule-based when it isn't.

## Workflow

### 1. Frame the interview

Before any question, the agent says:

> "I'm going to ask you six to eight questions about how you actually run `<activity-name>`. Your answers will be saved verbatim as a source document, and the structure I write — the trigger, the quality gates, the decision criteria, the output format, the fallbacks, the handoff — will cite that source. Treat this as testimony: whatever you say, I'll write down. If something is uncertain or context-dependent, say so explicitly; I'll write 'depends on X per <interview>' rather than pretend it's a rule."

### 2. The eight questions

Asked one at a time, in this order. The agent waits for an answer before moving on. Each maps to a specific density field.

| # | Question | Density field |
|---|---|---|
| 1 | "When does `<activity>` actually start in a real engagement / cycle / week? Not what's supposed to happen — what happens." | `trigger` |
| 2 | "What has to be true about the inputs for it to be worth starting? When do you delay or refuse to start?" | `quality_gates` |
| 3 | "Walk me through how you do it, end to end. Don't skip anything." | (sets up Q4-7) |
| 4 | "When you have multiple options inside the work, how do you pick? Three or four rules of thumb you use, in order of priority." | `decision_criteria` |
| 5 | "What does the output look like when you're done? Format, length, sections, examples of past good ones." | `output_format` |
| 6 | "What do you do when an input is missing, or two valid options can't be picked between, or the work hits a wall?" | `fallback` |
| 7 | "After you finish, what happens? Who picks it up, when, with what confirmation?" | `handoff` |
| 8 | "Anything else about how this actually runs that I haven't asked? A failure mode you've learned to avoid, a shortcut you take, a rule you broke once and learned not to break again." | (free-form, becomes notes in the transcript) |

The agent listens for specifics. Vague answers ("it depends on the context", "we play it by ear") get a follow-up: *"What specifically do you look at when context X comes up?"* until the answer is something you could write down.

### 3. Save the transcript

Verbatim, including the agent's questions, including any side-comments the performer made. Saved as:

```
sources/<performer-id>-interview-<YYYY-MM-DD>.md
```

Frontmatter:
```yaml
---
id: <performer-id>-interview-<YYYY-MM-DD>
type: source
title: "Interview with <Performer Name> on the <activity-id> activity"
date_recorded: <YYYY-MM-DD>
recorded_by: agent
purpose: "Fill the activity-density layer for nodes/activities/<activity-id>.md per the org/AGENTS.md schema. The transcript is the source citation for the trigger / quality_gates / decision_criteria / output_format / fallback / handoff fields."
---
```

If the same performer already has an interview source for the same activity (e.g. an annual refresh), the new transcript is a separate source — the old one stays. Cite both.

### 4. Extract the six density fields

Re-read the transcript and structure-extract into the activity's frontmatter, following the `org/AGENTS.md` schema. The agent does this section by section:

- `trigger` — list of strings, each a concrete moment ("after the kickoff workshop closes and audience-research synthesis lands", not "weekly")
- `quality_gates` — list of strings, each a check on inputs ("≥ 3 customer interviews", not "good audience research")
- `decision_criteria` — list of strings, each a rule of thumb in priority order ("pick the narrowest audience for which the client is unambiguously the right answer")
- `output_format` — object with `description` (the shape) and `example_artefact` (path or named reference to a real prior output, even if not committed to org/)
- `fallback` — list of `{condition, action}` pairs, each a named situation and what the performer does
- `handoff` — list of strings, each a downstream step with named owner and timing

Every field cites the transcript via its source id (added to the activity's `sources:` array if not already present).

### 5. Show the diff and confirm

Before writing the activity node, show the user the proposed frontmatter additions side by side with what's there. The user confirms; the agent writes. Then the agent appends a log line.

### 6. Append to the log

Per `log.md` convention (prepend-only, most recent on top):

> `<YYYY-MM-DD> — interview-activity on <activity-id> — performer <performer-id>; transcript saved as sources/<performer-id>-interview-<date>.md, density layer filled (six fields), activity now skill-compilable via compile-agent --with-skills.`

### 7. Verify

Run `org_lint_run` (Tier 1) to catch frontmatter issues. The new fields are optional in the schema; lint should pass.

## What's now possible

After this skill runs on an activity, that activity is **skill-compilable**. Specifically:

- `compile-agent --scope person:<performer-id> --with-skills` will export the activity as a Claude skill (slash command) bundled with the person's `CLAUDE.md`. The skill, when invoked, walks the agent through the activity's trigger / gates / criteria / format / fallback / handoff using the verbatim phrasing from the transcript.
- The activity becomes the basis for a Gherkin scenario (Given/When/Then), bridging to Cicero's context-bundle layer when the org goes there.

## Cost vs gain

Filling the density layer for one activity takes 30-45 minutes of the performer's time, plus 15-20 minutes of the agent's structuring time. The gain: that activity moves from "described" to "executable as a skill". The org doesn't need to do this for every activity — just the ones it wants to deploy as agent skills.

A reasonable first pass: fill density on the 3-5 most-frequently-run activities for any unit considering Level 2 deployment. The studio's mid-market engagement, for example, would prioritise: `kickoff-workshop`, `brand-positioning`, `weekly-check-in`, `asset-handover`. Four interviews, ~3 hours of total performer time, four activities turned into skills.

## When NOT to use this skill

- The activity is rare (less than monthly) and the variability is high. The density layer is for activities that benefit from being run consistently. Rare ad-hoc work is better captured as a play.
- The performer's view of the work is itself in flux. If the activity is being redesigned, freezing testimony now produces a stale source. Wait until the redesign is settled.
- The activity is regulated and the rules already live in a codified document (a regulator's manual, an internal SOP). In that case the source is the document, not the interview; use `ingest` on the document instead.

## Reference example

The sample-org has two activities with the density layer filled, produced by this skill on 2026-05-07:

- `nodes/activities/brand-positioning.md` — performer Marco Bellini, judgment-heavy / scarcity-bound. Source: `sources/marco-interview-2026-05-07.md`.
- `nodes/activities/kickoff-workshop.md` — performer Tomás Reis, coordination-heavy / alignment-bound. Source: `sources/tomas-interview-2026-05-07.md`.

The other 12 activities in sample-org are at structural-only level (the floor), demonstrating that the density layer is opt-in per activity and that the two states coexist cleanly in the same `org/`.
