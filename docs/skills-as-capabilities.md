# Skills are the codified part of a capability, not a complete capability

A note on what `playable-org/skills/*/SKILL.md` files are, in the Dorsey/Botha frame from *From Hierarchy to Intelligence* (Block, March 2026). Worth more reflection than this note carries; flagged here because the distinction surfaces every time someone asks what playable-org actually provides.

## The frame

Per `skills/CAPABILITIES.md`, a capability has **five properties** plus **team ownership**:

1. Invocable — declared way to activate it.
2. Produces structured output — verifiable result, not opinion.
3. Atomic — right granularity.
4. Hard to acquire — regulation, network effects, expertise, time.
5. Composable — with other capabilities, into different flows.

Plus: **DRI** (single accountable person) + **ICs** (executors) + **player-coach** on capabilities large enough to need both ongoing building and people development.

A capability is the union of those eight elements. Strip any of them and you have a fragment.

## How playable-org skills score

| Property | Skills (init / ingest / lint / value-map / reshuffle / world-model / ai-exposure / compile-agent / interview-activity / new-playbook) |
|---|---|
| **Invocable** | Yes. Each `SKILL.md` has a contract (frontmatter `name + description`) and a channel: for the four playbooks, `org_play_run(playbook=..., mode=...)`; for the others, `org_skill_read(name)` returns the recipe and the agent follows it. |
| **Produces structured output** | Yes. Each playbook produces JSON + HTML + SVG. `init` produces a populated `org/`. `compile-agent` produces a CLAUDE.md + manifest. `lint` produces a deterministic report. |
| **Atomic** | Yes. One skill, one job. Composition is explicit in `skills/ROADMAP.md` (ai-exposure → value-map → reshuffle → world-model), not implicit in the skills themselves. |
| **Composable** | Yes. The four playbooks compose. `world-model` consumes outputs of `value-map` and `reshuffle` when present. `compile-agent --with-skills` composes `compile-agent` with the activity density layer filled by `interview-activity`. |
| **Hard to acquire** | No, and yes. The skill-as-file is MIT-licensed, anyone clones. The skill-as-practice — the discipline of citing every claim, of conditional-voice on emerging items, of plain-language editorial, of knowing which skill to run on which slice and when — is what's actually hard to acquire. A person who downloads the files without internalising those produces output that fails autoresearch. The codification is cheap; the practice is expensive. |
| **DRI / IC / player-coach** | Missing in the public template. The skills are recipes that run against the agent. Nobody is named-accountable for "value-map is shipping its contract over time" in a deployed instance. In a real fork the org has to add the accountability layer. |

Four out of five properties yes. One property (hard to acquire) split between the file and the practice. The ownership row missing entirely.

## The thing they're missing

A capability has a person whose name is on the line. The skill doesn't. When `value-map` produces a play that ages badly, who owns that? In the public template: the maintainer (me, you, whoever forked). In a deployed instance: nobody, until someone is named.

This is not a defect of the skill. It is the difference between **codification** and **operation**. Skills codify how the work is done. They don't ship with operating discipline — that's not theirs to ship. Operating discipline lives where the work runs.

A useful test: can the skill survive being scaled to ten orgs without any of them naming a DRI for it? **Yes**, the procedure runs the same way. Can it survive ten orgs deploying it as a recurring quarterly capability? **No** — without a DRI per deployment, the playbook is run inconsistently, the autoresearch verdicts diverge, the artefacts drift, the practice degrades. The codification holds; the capability doesn't.

## What follows

**Skills are the codified part of a capability, not a complete capability.**

A complete capability is:
- skill (the procedure, codified)
- DRI (the named accountable person)
- ICs (executors — today the agent runs the procedure, tomorrow a hybrid of agent + human)
- structured output verified (autoresearch + audit gates)
- operating cadence (when it gets re-run, by whom, at what frequency)

What playable-org provides is the first ingredient (the codification) and one half of the third (the agent as IC). The remaining ingredients — DRI, cadence, operational ownership — are what the org instantiating playable-org adds on top.

This clarifies what's distributable vs what's local. The codification ships in the repo. The operational stack is per-fork, per-org, per-deployment. A fork that pretends the codification is enough is shipping a capability template, not a capability.

## Bridge to Cicero's frame

Cicero (*[Through The Boundary, May 2026](https://through-the-boundary.simonecicero.com/)*) frames this distinction at the agentic-pipeline scale: the **context bundle** is the distributable static artefact (data model + business logic + UX); the **running agent stack** is the live system with human accountability layered on. The two coexist; mistaking one for the other is the source of much confusion.

In that mapping:

| Cicero | Playable Org |
|---|---|
| Context bundle (static, distributable) | `org/` cited structure + `skills/` codified procedures + `mcp-server/` primitive surface |
| Running agent stack (live, owned) | A specific deployment of playable-org in a specific org, with named DRIs per skill + an operating cadence + the agent running the procedures |

The skill is a context-bundle ingredient. The capability is the running agent stack ingredient. Same procedure, different layer.

## Open questions worth more reflection

1. **Should the public template document a "deployment manifest" alongside each skill?** A standard place where a fork names the DRI, the cadence, the IC discipline. Today this isn't anywhere; each fork invents its own answer. A shared template would surface the operational layer as a first-class concern instead of an afterthought.

2. **Where does the agent itself sit in this frame?** The agent is the IC for most skills today. Is the agent a *replaceable* IC (any LLM that can read SKILL.md works) or a *specialised* IC (the autoresearch dimension uses Claude specifically; subscription-mode assumes Claude Code as the runtime)? The honest answer is: replaceable for the procedure, specialised for the editorial discipline that keeps the output clean. That's a distinction worth pinning down.

3. **What's the test that a skill has crossed from codification to operating capability?** Today autoresearch tests the artefact's quality (does the play hold up?). It does not test the operating cadence (is the play being re-run quarterly? Is the DRI named? Is the autoresearch verdict acted on?). The deployment-level test is missing. Whether to build it (a mcp tool that audits not just artefacts but operating discipline) is an open call.

4. **What's the equivalent question for `org/` itself, not just for skills?** The structure is also a codified context that needs operational ownership (who keeps it current as the org changes? who arbitrates contradictions between sources?). Skills make this question visible; the org structure has it too, less explicitly.

Worth an essay. This note is the placeholder.

---

*Written 2026-05-08, after a conversation with Matteo about whether the skills meet Dorsey's definition. Tagged for future expansion: this should grow into a piece on the codification-vs-operation seam in agentic systems, with playable-org as the example and Cicero's context-bundling thread as the parallel frame.*
