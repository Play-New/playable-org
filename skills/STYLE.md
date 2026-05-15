# Style charter for skill output

Charter that governs how every skill in `skills/playbooks/` writes the consumer-facing output: the play body, the HTML viewer text, the modal copy, the area notes, the play summaries.

The charter does not govern code, schema field names, internal JSON keys, or this `SKILL.md` itself (which is agent-facing technical documentation). It governs anything a non-technical reader will see.

The reference repo is https://github.com/matteoroversi/anti-ai-rhetoric. This file is the project-local distillation, applied to skill output.

## Core principle

Form follows function. Every stylistic choice serves the specific content. No automatic patterns, no decorative formulas.

## Language

Examples below are in English. Apply the same patterns to whatever language the output is in. For an Italian play, find the Italian equivalents of the word types and structures listed.

## Accuracy and honesty

- Do not invent personal anecdotes, fake relationships, or hypothetical examples presented as real observations.
- When using a hypothetical, label it: "imagine...", "suppose...", "ipotizza...".
- Use real, verifiable names, dates, organizations, sources whenever possible.
- Take a clear position when evidence is solid. Use qualifiers only for genuine uncertainty about future unknowns.

## Lexicon to avoid

### Hyperbolic adjectives

groundbreaking, revolutionary, transformative, unprecedented, incredible, amazing, fantastic, brilliant, powerful, extraordinary, remarkable, stunning, profound, epic.

Italian equivalents: rivoluzionario, eccezionale, straordinario, sbalorditivo, profondo, magistrale.

### Dramatic words

paradox, trap, illusion, magic, destiny, chaos, crisis, explosion, revolution, apocalypse, miracle.

Italian equivalents: paradosso, trappola, illusione, magia, destino, caos, esplosione, rivoluzione, miracolo.

### Absolute terms

always, never, everything, nothing, absolutely, completely, entirely, totally, all, none.

Italian equivalents: sempre, mai, tutto, niente, assolutamente, completamente, interamente, totalmente.

### Business jargon

paradigm shift, synergy, leverage (as verb), ecosystem, journey (metaphorical), disrupt, disruption, game-changer, deep dive, circle back, move the needle, low-hanging fruit, bandwidth (metaphorical), scalable mindset, thought leadership, best practices, solutions (vague), streamline.

Italian equivalents: cambio di paradigma, sinergia, leva (come verbo), ecosistema, journey, disruption, game-changer, deep dive, soluzioni (vago), best practice.

### Weak intensifiers

clearly, obviously, evidently, certainly, definitely, truly, really, actually, literally, particularly, essentially, fundamentally, inherently, naturally.

Italian equivalents: chiaramente, ovviamente, evidentemente, certamente, sicuramente, davvero, veramente, effettivamente, letteralmente, particolarmente, essenzialmente, fondamentalmente, intrinsecamente, naturalmente.

### Empty fillers

it's interesting to note that, what's interesting is that, it's worth noting, needless to say, at the end of the day, the fact of the matter is, when all is said and done.

Italian equivalents: vale la pena notare, è interessante notare, inutile dirlo, alla fine della fiera, in fin dei conti, va detto che.

### Pseudo-punchlines

The result:, The point is:, The real question is:, The bottom line:, Here's the thing:, The truth is:.

Italian equivalents: Il punto è:, Il risultato:, La vera domanda è:, In sostanza:, La verità è:.

### Framework jargon (paraphrased into prose)

Names of internal model primitives are fine when they're the obvious label for a structural element a reader can see (e.g. "Stakeholders", "Capabilities", "Genesis / Custom / Product / Commodity" as axis labels). They become jargon when they're paraphrased into running prose where the reader has to translate them.

Words that must not appear in user-facing prose (chat replies, play body, viewer copy, decision answers, rationale fields):

- *moat* (replace with "differentiated"); *commodity* in body prose (replace with "standard" or "market-standard"); *commoditize* (replace with "standardise" / "level the field")
- *judgment density*, *capability stack*, *capability bundle* (paraphrase or drop — replace with "how much expert judgment is needed" / "the things the org can actually do")
- *coordination tax* (replace with "the cost of keeping everyone aligned" / "alignment cost")
- *failure-signal* — Dorsey's term in the Block source, but **not used in user-facing prose**. The roadmap is not a pile of failures: it's the subset of captured signals from the loop that no current composition can fulfil. In prose write "what the loop surfaces as roadmap" / "a request the structure would already receive that no composition can fulfil today" / "a missing capability". The world-model JSON field is `pieces_to_build[]` (renamed in May 2026 from `failure_signals[]`; a further rename to `roadmap[]` is on the table).
- *thin* as architectural metaphor (replace with "what to build next" / "the pieces that aren't there yet" — `thin` reads as critique and the reader stops on it)
- *see-saw*, *flywheel* as standalone labels (replace with "old rule: more autonomy means less alignment" / "new rule: more autonomy and more alignment together")
- *engine candidate*, *rebundle*, *bundle state*, *constraint distribution* in body prose (paraphrase or drop)
- *production-tier* (replace with "production-side")
- *rich subset* (replace with "the observed sample")
- *O\*NET*, *AEI*, *embedding*, *cosine similarity*, *MiniLM*, *paraphrase-multilingual* (replace with "the public catalog of work" / "the Anthropic sample" / "matched by meaning"; technical names belong only in the source-attribution footer)
- *top-K*, *top-1*, *p25*, *p75* (replace with concrete description: "the closest five matches" / "the upper band of the autonomy scale")
- JSON field names leaking into prose: *evolution_target*, *ai_effect*, *ai_autonomy_mean*, *_structure_id*, *_aei*

The forbidden list grows. When a new framework gets composed in, its primitive names go on the list the moment they're added to a skill — the test is "would a reader who hasn't read the SKILL.md know what this means?". If no, the word stays in code and gets paraphrased in prose.

### Conditional voice for emerging items

Anything in `org/` or in a play that names a thing **that doesn't exist today** — a new component (`is_new: true`), a new stakeholder type (`new_end_users`), a new value flow (`new_value`), a missing capability (failure-signal / piece to build), a candidate role — must be written in conditional voice, not temporal/predictive voice. The map suggests preconditions are approaching; whether the org chooses to build the thing stays the org's call.

| Don't write | Do write |
|---|---|
| "When the studio builds X, Y becomes viable." | "Y opens up only **if** the studio first builds X. Without that, Y stays too expensive." |
| "AI makes this commoditize within 18 months." | "AI **could** push this toward standard inside 18 months, but the timing depends on..." |
| "This will be the next hire." | "A **candidate** role that AI makes **feasible** — but it has to be staffed and built. The map shows where it **would** sit, not that it has been built." |
| "The new capability arrives Q3." | "If the studio funds it, the capability **could** land by Q3." |

Forbidden in this context: *when* (in the temporal sense, "when X happens"), *will*, *makes*, *arrives*, *becomes* (with a future-tense subject).

Permitted: *if*, *would*, *could*, *depends on*, *stays the org's choice*, *conditional on*.

Reason: emerging items are analyses, not roadmaps. The reader needs to feel the org's freedom to act, not the model's prediction that something is fated.

## Structural patterns to avoid

- Rhetorical formulas: "Not X, but Y", "It's not... but...", "X isn't... it's...", "Significa X, non Y", "Non X, ma Y" — never use these structures, in any direction or language. They sound aphoristic and obscure the actual claim. Rewrite as a single declarative sentence.
- Meta-rhetorical questions in the agent's voice that anthropomorphise the data: "where does the graph declare not to know?", "what does the structure say?", "il grafo dichiara di non sapere", "la struttura racconta". The graph does not declare. The structure does not say. The agent reads it and writes a finding. Use plain leader-facing questions instead ("what is missing here?", "cosa non torna nella struttura?").
- Graph-theory and network-science jargon in user-visible prose: *degree*, *centrality*, *isolate*, *topology*, *edge*, *node* (where "unit" / "activity" / "person" / "connection" would do), *anchor* / *anchoring* (use "starting point" or the concrete node name). The data is graph-shaped under the hood; the prose talks about the org, not the data structure.
- Forced triads of verbs or concepts.
- Manual-style numbered lists ("3 strategies for...", "5 ways to...").
- Generic subheadings ("The Challenges", "The Solution", "Le sfide", "La soluzione").
- Clickbait titles or theatrical setups.
- Pseudo-philosophical or vague endings.
- Sequences of same-length sentences creating mechanical rhythm.
- Opening paragraphs that delay the actual point.
- Conclusions that simply restate what was already said.

## Formatting

- Use formatting (bold, lists, line breaks) when it serves clarity, structure, or scannability.
- Lists work well for comparing options, outlining steps, presenting distinct items, quick reference.
- Lists work poorly when fragmenting continuous argument, replacing natural prose flow, or used decoratively.
- Bold key terms, critical distinctions, or section labels — not generic emphasis.
- No emojis, no em dashes, no multiple punctuation (!!, ??), no hashtags. Use a regular hyphen or a comma where you would have written em dash.
- Inline markdown rendered in viewers. Decision answers, rebundle narrations, and other agent-authored prose pass through `design.inline_md()` at render time, which renders `**bold**`, `*italic*`, and `` `code` `` and escapes everything else. Block-level markdown (headings, bullet lists, blockquotes) is not rendered inside these fields — split into paragraphs separated by blank lines, use `**bold**` for the rare label, and write the rest as prose.

## Openings

### Avoid

- Broad generalizations about "today's world", "the modern era", "in oggi", "nell'era moderna".
- Vague scene-setting that delays the actual point.
- Questions that aren't genuinely informative.
- Definitions of obvious terms.
- Historical preambles unless the history is the point.

### Prefer

- Start with a specific observation, fact, or data point.
- Open with a concrete example, then zoom out.
- Begin with the thesis if it's strong enough.
- Use a counterintuitive fact that reframes the topic.

### Test

Could you delete the first paragraph without losing anything essential? If yes, delete it.

## Rhythm and flow

The default failure mode of AI writing: uniform medium-short sentences (10–15 words), creating staccato rhythm even in prose.

### Length requirements

- In every 3–4 paragraphs, include at least one sentence of 30+ words.
- In every 3–4 paragraphs, include at least one sentence of 5–8 words.
- Avoid sequences of 3+ consecutive sentences with similar length (within 5 words of each other).
- Target distribution: 20% short (5–10 words), 50% medium (11–20 words), 30% long (21+ words).

### How to build longer sentences

- Use subordinate clauses to show causation: "Because X happened in 2023, and Y followed in early 2024, we now see Z."
- Integrate examples without breaking flow: "The pattern appears across sectors, from manufacturing (where AI reduced lead times by 40%) to healthcare."
- Stack related facts: "The company grew from 10 to 100 employees, expanded to three markets, raised 50M, and still maintains 90% retention."
- Link micro and macro: "When a single engineer can now build what required a team of ten just two years ago, the entire economic model shifts."

### Advanced

- Vary sentence openings: avoid starting 3+ consecutive sentences with Subject-Verb.
- Alternate explanatory closings with concise punchlines.
- Use content-based transitions (facts, names, data), not formulaic connectors.
- Balance paragraph sizes: alternate compact blocks with expansive ones.
- Questions only when they add information or reframe. Avoid empty closing questions.

## Examples and data

### How to integrate

- Weave data into sentences: "Revenue grew 300% to 45M" not "Revenue grew. It reached 45M."
- Name real organizations, people, studies. Avoid "a company" or "research shows" unless you genuinely can't be specific.
- Use examples to add information, not just restate the point.
- Mix scales: one individual story, one organizational case, one system-level stat.

### Avoid

- Generic examples that could apply to anything ("imagine a company that...").
- Data dumps without interpretation.
- Examples longer than the point they're supporting.

## Preferred moves

### Clarity

- Anchor abstract ideas with concrete details.
- Define key terms explicitly when necessary.

### Transitions

- Connect through causation or contrast in content, not filler words.
- Shift between micro (individual) and macro (system) perspectives.

### Conclusions

- Close with a concrete implication or next step.
- Avoid restating what was already clear.

### Voice

- Be direct when evidence is solid.
- State uncertainty explicitly when relevant.

## Writing decisions

Every playbook output ends in a small set of decisions (3–5 typically). Each decision is read by a leader who has thirty seconds to ninety seconds. The shape that earns those seconds:

1. **Question.** One short, plain leader-facing question. Direct, not aphoristic. Avoid the agent's voice ("what does the graph say?"). Prefer the leader's voice ("where is the work concentrated?", "what does it mean that the org is organised in five Divisions?", "what doesn't add up here?").

2. **Answer, in three moves, in this order:**
   - **What we see.** State the observation in plain prose. Name the specific units / activities / people / commitments by name. No graph-theory vocabulary; the reader doesn't care that a node has high degree, they care that this specific area is the busiest.
   - **The numbers, used as evidence.** Cite the counts, ratios, degrees that support the observation. Numbers go *after* the claim, not before. "The most connected area has 78 dependencies; the most connected division has 20" is fine. Leading with "Degree centrality of the most connected node is 78" is jargon.
   - **The concrete next move.** One sentence that names what the leader could do with this. Not vague ("worth investigating"), specific ("thirty minutes with the four area heads will tell us which of the two readings is true").

3. **Length.** Two to four short paragraphs per decision. Read aloud in under a minute. If a decision spills into five paragraphs of analysis, it has become a report; split it or cut it.

4. **Source field.** Every decision lists the node files it cites, by relative path (`nodes/units/<id>.md`, `commitments/<id>.md`, ...). The audit script checks every cited id resolves; if a path is dead, the decision fails the gate.

5. **Two readings, when honest.** When the data supports more than one interpretation and only one is true, say so and name the test that picks between them. ("Either A or B. Thirty minutes with X tells us which.") Don't hedge with "perhaps" or "potentially" when a concrete test exists.

Quick before/after examples on the same observation:

> **Bad.** *Dove il grafo dichiara di non sapere ancora?* Sei nodi isolati nella vista di default. Cinque sono dichiarati come tali nei loro file: commissione-consultiva-ricerca (organo statutario senza membri né attività registrate), e le quattro voci finanziarie in `financials/` che non hanno una relazione tipizzata verso una Direzione. (anthropomorphises the graph, uses *isolate / nodo / relazione tipizzata*, no concrete next move)

> **Good.** *Cosa nella struttura non torna ancora?* La commissione consultiva ricerca è nominata nello statuto e nel chart, ma nessun membro è registrato e nessuna attività è collegata. Domanda binaria a chi conosce AIRC dall'interno: è dormiente nella realtà, o esiste e i suoi membri non sono stati ancora ingeriti? (leader voice, names the unit, names the test that closes the question)

## Self-check before finalizing output

Run this checklist before saving any consumer-facing text.

1. Sentence length: at least one 30+ word sentence and one 5–8 word sentence every 3–4 paragraphs?
2. Opening: could the first paragraph be deleted without losing essential content?
3. Banned words: scan for hyperbolic adjectives, weak intensifiers, business jargon. Cut them.
4. Rhetorical formulas: any "Not X, but Y" / "It's not... but..." / "Significa X, non Y" structures? Eliminate, in any language.
5. Meta-rhetorical questions: any "what does the graph say / declare / not know"? Anthropomorphises the data. Rewrite as a leader-voice question.
6. Graph-theory jargon: any *degree*, *centrality*, *isolate*, *topology*, *edge*, *node* (where a domain word would do), *anchor / anchoring*? Replace with the concrete unit/activity/connection name.
7. Mechanical patterns: 3+ consecutive sentences structured the same way?
8. Formatting: bold and lists used only where they serve clarity?
9. Punctuation: any em dashes, multiple punctuation, emojis, hashtags? Remove.
10. Examples: specific (names, numbers, dates) or generic placeholders?
11. Closing: drifts into vague philosophy or ties to concrete next step?
12. Decisions specifically: each one follows the shape in "Writing decisions" — leader-voice question, observation first then numbers, one concrete next move, two paragraphs to four.

## Where this charter applies

- Every play body in `org/plays/*.md`.
- Every HTML viewer text generated by `skills/playbooks/*/viewer.py`.
- Every modal copy, hint paragraph, intro section in those viewers.
- Every interpretive narrative authored by the agent during a play (constraint evidence claims, ai_effect texts, area notes, rebundle descriptions, mode_evidence claims).

## Where it does not apply

- `SKILL.md` files themselves (agent-facing technical documentation).
- JSON schema field names and internal codes (`primary_constraint`, `evolution_target`, `_aei`).
- Code, comments in code, CLI usage strings.
- Lint reports, audit output, log entries (those are utility text, not consumer-facing).
