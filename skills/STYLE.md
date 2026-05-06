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

## Structural patterns to avoid

- Rhetorical formulas: "Not X, but Y", "It's not... but...", "X isn't... it's..." — never use these structures.
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
- Shift between micro (individual) and macro (system) views.

### Conclusions

- Close with a concrete implication or next step.
- Avoid restating what was already clear.

### Voice

- Be direct when evidence is solid.
- State uncertainty explicitly when relevant.

## Self-check before finalizing output

Run this checklist before saving any consumer-facing text.

1. Sentence length: at least one 30+ word sentence and one 5–8 word sentence every 3–4 paragraphs?
2. Opening: could the first paragraph be deleted without losing essential content?
3. Banned words: scan for hyperbolic adjectives, weak intensifiers, business jargon. Cut them.
4. Rhetorical formulas: any "Not X, but Y" or "It's not... but..." structures? Eliminate.
5. Mechanical patterns: 3+ consecutive sentences structured the same way?
6. Formatting: bold and lists used only where they serve clarity?
7. Punctuation: any em dashes, multiple punctuation, emojis, hashtags? Remove.
8. Examples: specific (names, numbers, dates) or generic placeholders?
9. Closing: drifts into vague philosophy or ties to concrete next step?

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
