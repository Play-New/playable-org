# Autoresearch · LLM-judge rubric

The 5th dimension of `autoresearch.py` is a model-applied judgment over a play's `decisions[]` array. Three axes per decision plus a one-sentence note. Strict by default — the point is to catch decisions that read fine in isolation but don't actually help the leader.

## The rubric

> You are reviewing the interpretive 'decisions' attached to a `<artefact_kind>` of a real organization.
>
> `<playbook_context>`
>
> Each decision is a question the leader of the organization should be able to answer after reading the artefact, plus the answer the play asserts.
>
> Score each decision on three independent axes. Be strict — the point of the review is to catch decisions that read fine in isolation but don't actually help the leader.
>
> **actionable** — `yes` if the answer names a concrete move the leader could make on Monday (a re-allocation, a new role, a pricing change, a structural shift, a hire, a divestiture, a product call). `no` if the answer is descriptive only ("X is commoditizing", "Y is fragile") with no implication for action.
>
> **distinctive** — `high` if the framing reads as something only this organization could have arrived at — it uses the org's named units, named people, named commitments, and its specific mix. `medium` if it's plausible but could apply to a similar shop with the names swapped. `low` if it's consultant-generic — true of any comparable firm in the category.
>
> **readable** — `yes` if a smart non-technical leader of this org would track the prose without hitting jargon (framework vocabulary, abstract management speak, paraphrased jargon like "high judgment density"). `no` if they would stop and ask what a sentence means.
>
> Add a one-sentence note per decision explaining the scores. Be specific about which sentence or move triggered the score, not generic praise.

The full template lives in `skills/autoresearch_lib.py` as `_JUDGE_RUBRIC_TEMPLATE`. Each playbook supplies its own `playbook_context` string explaining what the artefact is, so the judge knows what the decisions are scoring against.

## Two execution modes

The dimension can be applied two ways. Both share the same rubric and the same output schema. The choice is environmental.

### Subscription mode (default for Claude Code users)

The agent currently running in the user's Claude Code / Claude Desktop session is a Claude. **It can apply the rubric itself**, in-context, without a separate API call. This is the default path for human-driven sessions.

The flow:

1. The deterministic `autoresearch.py` runs first (4 dimensions, no model needed).
2. The agent reads the play's `decisions[]` plus the `playbook_context` string from the playbook's `autoresearch.py`.
3. The agent applies the rubric above and produces a JSON verdict matching the schema below.
4. The verdict is written to a sidecar file `<play>.judge.json` next to the play, and reported in chat.

No API key, no extra cost beyond the user's existing subscription. The agent is already there; the judge is one of its skills.

### API mode (for CI / automation / non-Claude-Code users)

When `autoresearch.py --llm` is invoked, the script calls Claude Sonnet 4.6 via the Anthropic SDK using `ANTHROPIC_API_KEY`. This is fully automated, useful for CI gates that don't have an interactive agent on hand. The verdict is printed to stdout and aggregated into the autoresearch output.

| Mode | When to use | Cost | Where it runs |
|---|---|---|---|
| Subscription | A user is in Claude Code / Claude Desktop and wants to score a play they just rendered | Subscription (no extra) | The user's session |
| API | CI / scheduled jobs / automation without a human agent | API credits | Standalone `python3` process |

Both modes produce the same verdict shape; the autoresearch deterministic dimensions are identical regardless.

## Verdict schema

```json
{
  "playbook": "<playbook-name>",
  "judge_mode": "subscription (in-context, ...)" | "api (claude-sonnet-4-6)",
  "decisions": [
    {
      "actionable":  "yes" | "no",
      "distinctive": "high" | "medium" | "low",
      "readable":    "yes" | "no",
      "note": "<one sentence explaining the scores; specific to which sentence or move triggered them>"
    }
  ]
}
```

## Aggregate fail conditions

Same as the API-mode autoresearch:

- FAIL if **any decision** scores `actionable: no` or `readable: no`.
- FAIL if **more than half** of decisions score `distinctive: low`.
- Otherwise PASS.

The verdict is informational; the deterministic 4 dimensions remain the load-bearing gate. The judge catches decisions that pass deterministic checks but still don't help a leader land a move.

## Reference verdict files

The four canonical sample-org plays each have a sidecar `<play>.judge.json` produced in subscription mode. Open them next to their plays under `mcp-server/test-fixtures/sample-org/plays/data/` to see the rubric applied to real decisions:

- `value-map-studio-mid-market-baseline-2026-05-07.judge.json`
- `ai-exposure-outline-2026-05-07.judge.json`
- `world-model-outline-2026-05-07.judge.json`
- `reshuffle-outline-2026-05-07.judge.json`
