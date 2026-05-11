# Capabilities, what they are and how to expose them

Methodology document, applicable to any organization. Defines what a capability is in the operational sense, how it differs from things that are not capabilities, and what it takes to make a craft invocable from outside the person who runs it today.

References: Jack Dorsey + Roelof Botha, *From Hierarchy to Intelligence*, original at Block ([block.xyz/inside/from-hierarchy-to-intelligence](https://block.xyz/inside/from-hierarchy-to-intelligence)) and at Sequoia Capital ([sequoiacap.com/article/from-hierarchy-to-intelligence](https://sequoiacap.com/article/from-hierarchy-to-intelligence/)), March 2026; Sangeet Choudary, *Reshuffle* (2025). Concepts are distilled from the sources, not reproduced.

This document governs the methodology behind any skill that touches capability analysis (currently `world-model`, partially `reshuffle`). For the writing rules that govern consumer-facing output, see [STYLE.md](STYLE.md).

---

## The move

Today an organization already has interfaces, capabilities, and a world model. Interfaces deliver outputs but don't capture the signals that come back through them. Capabilities are crafts embedded in named people. The world model lives implicit in heads and in delivered files nobody can query.

The move described in the source is to insert intelligence, typically AI-mediated, that transforms each. Interfaces become signal collection points in addition to delivery. Capabilities become invocable systems: the person stays as DRI, a wrapper exposes them so anyone (or any agent) who knows the contract can call them. The world model becomes a system that auto-updates from the signals.

It runs as a closed loop:

1. A request arrives via an interface.
2. Intelligence reads the world model and decides how to respond.
3. If a capability matches, it is invoked, the response goes back via the interface, the outcome is captured into the world model.
4. If no capability matches, the unanswered request is itself captured into the world model. That captured signal is the future roadmap.
5. The organization reviews accumulated unanswered signals and decides which to turn into new capabilities. The new capability enters the loop.

## What's from the source vs operational extensions

The four-part frame (capabilities, world model, intelligence layer, interfaces), the role of intelligence as composer (not decomposer), the world-model split between operational and customer side, the failure-signal-as-roadmap claim, and the three roles (DRI, IC, player-coach) come directly from Dorsey/Botha. The term "failure signal" itself is the source's, used verbatim in the Block piece.

The before/after framing of the move (interfaces in delivery-only form vs as signal collection points, capabilities embedded in people vs invocable, world model implicit vs auto-updating) and the closed-loop formulation of the five steps above are an **operational synthesis** of source claims into an actionable view. The source describes the after state at Block; running the move on organizations that aren't Block requires naming the before state and the path between them.

The rest of this document is **operational tools developed for this template**: the five-property test, the four-question pragmatic test, the three-actors rule, the bidirectional users-and-contributors framing, the seven-step transition sequence, and the five wrapper criteria for making a capability invocable. Consistent with the source but not in it verbatim. Marked as such where they appear.

---

## Definition

A capability is an **invocable function** of the organization. Anyone, inside or outside, can call it and obtain an execution.

The source says capabilities are "atomic financial primitives... building blocks that are hard to acquire and maintain (some have network effects and regulatory permission). They have no UIs of their own. They have reliability, compliance, and performance targets." The five-property formalization below is **ours**: an operational unpacking that helps an analyst using this template recognize capabilities reliably. Individual properties (atomic, hard to acquire) are in the source verbatim; the structured five-item test is ours.

Five properties define it. All five must hold.

1. **Invocable.** A declared, repeatable way to activate it exists. Anyone who knows it exists can call it.
2. **Produces structured output.** Not an opinion or a conversation: a verifiable result.
3. **Atomic.** Does not decompose further into simpler functions that live elsewhere. Sits at the right granularity to be a building block.
4. **Hard to acquire.** Requires regulation, network effects, accumulated expertise, institutional trust, or some combination. Cannot be reproduced overnight.
5. **Composable.** Usable on its own or chained with other capabilities to build different flows. Has no UI of its own: a building block, not a product.

If one or more of these is missing, it is not a capability. It is an asset, a property, a governance organ, a compliance machinery, or a staff function. Useful things, of a different kind.

---

## The practical test

*Operational extension; the four-question test is a tool for analysts using this template, not in the source.*

For each capability candidate, four questions:

1. **Who can call it, from inside or outside?** If the answer is "the team that hosts it, through their internal procedures", it is not exposed as a capability.
2. **What does it return, in concrete terms?** If the answer is vague (support, oversight, management), the contract does not exist, it is not an exposed capability.
3. **What are the operational targets (time, quality, coverage)?** If none are declared, it functions as practice, not as capability.
4. **Can it be composed with another capability to produce a different flow?** If the same fixed sequence is required every time, it is not composable, it is a process.

Four concrete answers out of four equals an exposed capability. One vague answer equals a latent capability, not exposed. More than one vague answer means it is not a capability in the operational sense.

---

## What is not a capability

Working with large organizations, candidates that look like capabilities and are not surface often. Distinguishing them matters, because calling something a capability when it is not disorients the entire strategic conversation.

**Assets and properties.** Brand, accumulated trust, capillary territorial presence, years of history, recognized user base. These are things that capabilities *use* when activated. They are not invocable operations. A territorial network is not a capability, the capability is "mobilize-territorial-campaign" (which uses the network as an asset).

**Governance organs.** Boards, committees, statutory bodies. These are approval steps *inside* capabilities (for example: an approval committee is part of "decide-funding"). They are not capabilities on their own.

**Compliance machinery.** Risk management systems, codes of ethics, regulatory frameworks, audits. Necessary to operate, but they are constraints on all capabilities, not capabilities in themselves.

**Staff functions.** HR, IT, accounting, procurement. Capabilities sit inside them ("execute-payment", "onboard-new-colleague") and are usually commodity-grade, present in any organization. Necessary, not differentiating.

**Codified cross-team processes.** A dossier passed across three areas with structured documentation looks like a capability but is a process. The underlying capability ("evaluate-cross-team-request") exists but is not exposed, it is incarnated in the practice.

**Strategic aspirations.** "Innovation", "customer centricity", "organizational agility". Slogans, not capabilities. Without an invocable contract they are nothing.

---

## The three-actors rule

*Operational extension; this rule is ours, derived from but not stated in the source.*

Each capability must be callable by at least three different types of actor. If only one type uses it, it is probably too specific to that channel and should be decomposed or reformulated.

The three typical types:
- **External stakeholder** (user, customer, donor, supplier, regulator, partner)
- **Another capability of the organization** (composition)
- **Intelligence layer** (a system that recognizes a signal and composes a response)

If the capability is callable by all three, it is correctly exposed. If only one of the three calls it, it is a practice in disguise.

---

## The "users and contributors" rule

*Operational extension; the bidirectional contract framing is ours. The source mentions transaction data feeding the customer-side world model but does not state a general rule that every actor is both user and contributor.*

In the old framing, an organization has customers who receive and employees who produce. In the exposed organization, every actor is both: uses capabilities of the organization and contributes through others.

Example: in a payments system, the merchant who receives revenue is a user of payment-processing capabilities and a contributor through transactional data (which feeds the world model). The consumer who pays is a user of transfer capabilities and a contributor through spending signal.

The same pattern repeats across stakeholders in any organization when this approach is applied. A donor of a foundation invokes "designate-recipient" capabilities and contributes through donation history (signal that feeds the customer-side world model). A researcher invokes "request-grant" capabilities and contributes through scientific output (signal for new funding cycles). A volunteer invokes "join-campaign" capabilities and contributes through territorial work.

The consequence for capability design: the contract must be bidirectional by design. The capability does not only receive input from the actor and return output. It also returns signal to the world model of the organization, which feeds future compositions.

---

## Making capabilities invocable

*Operational extension. The source says capabilities have "reliability, compliance, and performance targets" but does not enumerate the five criteria below. They are a checklist for turning a craft embedded in a person into a capability the intelligence layer can compose.*

A craft becomes invocable when five things are in place. All five together.

### 1. Public contract

For each capability, an explicit declaration:

- **Input**, what it accepts as a request
- **Output**, what it returns
- **Operational targets (SLO)**, reliability, time, coverage, measured quality. Concrete numbers, not adjectives.
- **Regulatory constraints**, limits that cannot be relaxed. Which laws, codes, required approvals.
- **Invocation modality**, how to activate it (interface, channel, protocol).

Without a public contract the capability remains practice: anyone who wants to use it has to know who is on the team and talk to them case by case. Unfit for composition.

A useful consequence: writing the contract forces honesty about maturity. If the operational targets cannot be declared, it is because they have never been measured, and the capability is less mature than assumed.

### 2. Team ownership, not hierarchical ownership

A capability needs a dedicated team that owns it across time. Three distinct roles, not interchangeable:

- **DRI** (*Directly Responsible Individual*, Dorsey's term, popularized at Apple/Square). The single person accountable for the capability's outcome. One per capability — no committees, no shared accountability. The DRI is the throat-to-choke when something breaks: they answer for it, they can be removed for it. They do not have to do the work themselves; they can delegate freely to the ICs. What they cannot delegate is accountability. The DRI's job is to keep the capability shipping its contract over time, decide trade-offs in the moment, and make the calls that don't fit a rule.

- **Individual contributors (ICs)**: deep specialists in the domain. They build and operate the capability day-to-day. The DRI directs; the ICs execute. There can be many ICs per capability; there is exactly one DRI.

- **Player-coach**: a hybrid role on capabilities large enough to need both ongoing building and people development. Combines hands-on work with developing the ICs. Not a middle manager — does not spend the day on reporting and alignment. Still writes code, designs flows, ships work, and develops the team in addition. On smaller capabilities the DRI plays this role themselves; on larger ones a player-coach is named distinct from the DRI to free the DRI for outcome-level decisions.

Important: the capability is not owned by the area or division that hosts it today. A capability that crosses multiple areas is detached from all of them and given to a team — with its own DRI — that owns it end to end. Areas continue to exist as containers of the capabilities they host, but they are no longer the unit of ownership. The accountability sits on a person (the DRI), not on a unit.

Consequence: the organizational transition is not trivial. Capabilities already contained in a single area can be exposed quickly. Capabilities that cross two or three areas require deeper redesign.

### 3. Discoverability

Anyone who wants to compose two capabilities must be able to find them. Three concrete forms:

- **Internal registry** of capabilities with their contracts, accessible to all.
- **Composition examples** documented: who used it, in which context, with what outcome.
- **Visibility on current invocations** when relevant: who is using what, now.

Without discoverability, capabilities are reinvented every time they are needed. A team needs to publish an informational report and rebuilds the editorial flow from scratch, ignoring that a "publish-content" capability already owned by the editorial team exists.

### 4. Programmatically invocable

For software-mediable capabilities (example: process-payment, disburse-funds, publish-content), the call is an API. Standard, versioned, documented.

For inherently human-mediated capabilities (example: cultivate-major-relationship, execute-testamentary-succession, structure-institutional-partnership), the call is a **structured request channel**: an endpoint that receives the request, a human workflow that takes it on, a structured return. Not a spontaneous meeting, a discoverable protocol.

The crucial point: human capabilities are also exposed as functions. The difference between an exposed capability and a practice is that the first can be invoked by the intelligence layer when the world model detects a signal, while the second requires a human to notice and activate the human cycle.

### 5. Captured signals

Every invocation produces a signal that goes back into the world model. Two cases:

- **The capability fulfils the request.** The outcome is captured: what was asked, what was returned, against which SLO, with what side-effects. That captured outcome enriches the operational and per-caller world model. Every future invocation reads from a denser memory.
- **The capability cannot fulfil the request.** Could be because a sub-piece is missing, a regulatory constraint prevents it, or the world model does not have enough data to respond. The unanswered request is itself captured: what was asked, what would have been needed.

The accumulation of unanswered requests is the **future roadmap**. Dorsey's wording in the source: *"When the intelligence layer tries to compose a solution and can't because the capability doesn't exist, that failure signal is the future roadmap."* The roadmap is not the three-year plan that top management decides at a table. It surfaces from running the loop.

Example: the `execute-testamentary-succession` capability receives a request to handle a complex asset (real estate with condominium difficulties, anomalous lease). The capability today does not have the sub-capability `transform-complex-real-estate-asset` and falls back on quick sale below value. The signal captured: "real-estate transformation request, no capability matched". That signal is the first specification of the future capability `transform-complex-real-estate-asset`. The org reviews accumulated signals like this one and decides which to invest in.

Without signal capture, the roadmap comes from whoever has more authority in the planning process, not from whoever is closest to the signal.

---

## The three roles that emerge

*From the source verbatim. Dorsey introduces these three roles in the Block piece.*

Once capabilities are exposed, the organization no longer needs a permanent middle-management layer. The structure reduces to three roles:

- **Individual Contributor (IC)** builds and operates a capability layer (or the world model, or the intelligence layer, or the interfaces). Deep specialist. The world model provides the context that a manager used to provide, so the IC can decide without waiting for instructions.

- **Directly Responsible Individual (DRI)** owns a problem or an opportunity that crosses capabilities for a defined period (typically 90 days). Has authority to pull resources from the teams of the relevant capabilities. When the outcome is reached or the period ends, the DRI moves to another problem.

- **Player-coach** still builds (code, flows, content) and develops the people of the team. Replaces the traditional manager whose primary job was information routing.

What the middle manager did, coordinating, aligning, reporting, the system handles via the world model. Strategy and priorities are decided by the DRI structure for outcomes.

Important: this transition is slow. For organizations with heavy compliance, stakeholder networks built over decades, consolidated area-lead structures, it is a transition of years, not months. The value of this approach in the short term is as a thinking tool, not as immediate restructuring.

---

## Two common errors to avoid

### Error 1: AI as accelerator without exposing capabilities

The most frequent mistake is deploying AI to accelerate single work inside a unit, without first exposing the capabilities that cross multiple units.

Result: the AI-equipped unit runs faster, the others remain unchanged. The asymmetric speed worsens the coordination problem, because the fast unit produces output the others cannot digest. The total cost of keeping the organization aligned **increases** instead of decreasing. Choudary calls this the "coordination paradox".

The fix is to expose capabilities before accelerating them. An exposed capability can be called symmetrically by all units, the speed is distributed, not concentrated.

### Error 2: Confusing capabilities with governance organs

Treating a committee (ethics, scientific, oversight) as a capability is wrong.

A committee is an approval step that lives *inside* a capability. The "decide-funding" capability can contain "approve-by-scientific-committee" as an internal step. The committee is not callable as an autonomous capability by third parties.

The distinction matters because the committee as an organ has a different nature: non-composable by design, fixed calendar, decisions are governance acts not responses to requests. Treating it as a capability makes compositions fail because the committee calendar constrains the calendar of all capabilities that include it.

The fix: in the capability registry, declare explicitly which capabilities include governance-organ steps, and declare the organ calendar as a constraint of the capability SLO. Not as a separate capability.

---

## The transition, sequenced

*Operational extension. The Block piece "does not specify an implementation sequence" (per its own text). The seven-step ordering below is ours, derived from running the move on real organizations.*

For an organization starting from zero or near zero, the practical sequence:

1. **Identify capabilities.** Apply the test (five properties, four questions). Distinguish from assets, properties, governance organs, infrastructure, staff functions. Expect to find between 5 and 15 in a medium organization. If you find 50, you are calling capabilities things that are not capabilities.

2. **Write the contracts.** For each: input, output, SLO, constraints, invocation modality. This forces honesty about maturity. The capabilities that struggle to write the contract are the ones least mature.

3. **Assign ownership.** One team per capability, even if this means detaching it from the area that hosts it today. Capabilities crossing multiple areas require the deepest change.

4. **Make them discoverable.** Internal registry with composition examples and current invocations.

5. **Make them invocable.** API for software-mediable ones, structured request channel for human-mediated ones.

6. **Log composition failures.** Start measuring what the organization cannot compose. That log becomes the roadmap.

7. **Build the intelligence layer** (long term). A system that, given a world-model signal, composes capabilities automatically. This is the AI-heavy piece. Steps before this cannot be skipped.

The first six are organizational. Possible in 12 to 24 months for a medium-sized organization without large technological investments. The seventh is of a different order of complexity.

---

## When the framework applies and when it does not

**Applies well** when:
- The organization has multiple functional areas with stakeholders that cross boundaries.
- A variety of stakeholders potentially can invoke the same capabilities in different ways.
- The aspiration is to use AI strategically, not as a marginal productivity tool.
- There is willingness to question the existing organizational structure.

**Does not apply well** when:
- The organization does one thing with one stakeholder type. The framework is overkill.
- Stakeholder signals are too thin to feed meaningful compositions.
- Regulatory boundaries make capability decoupling from areas impossible.
- The organization is not ready for the structural conversation and would treat the approach as a theoretical exercise.

---

## The honest test before starting

Before applying the framework to an organization, a calibration question:

> What can any stakeholder invoke today, by name, and receive a structured response from?

If the answer is "depends on who you ask, depends on which area you reach", capabilities exist as practices, not as exposed functions. The framework applies and has value.

If the answer is "this, this and this, each with a known contract, accessible to anyone who knows how to call it", the organization has already done the exposing work. The framework applies as a tool of maintenance and discovery of missing capabilities, not as structural reform.

## Side note: are playable-org's skills "capabilities" by this framework?

Partially. They meet four of the five properties (invocable, structured output, atomic, composable) and split the fifth (the file is easy to acquire; the practice around it isn't). They miss the ownership layer entirely — there is no DRI for `value-map` in the public template, only a maintainer of the codification.

A separate note works through the distinction in detail: see [`docs/skills-as-capabilities.md`](../docs/skills-as-capabilities.md). The short answer is: **skills are the codified part of a capability, not a complete capability**. A complete capability is the skill + a named DRI + ICs + verified output + operating cadence. Playable Org ships the first ingredient; the org instantiating it adds the rest.
