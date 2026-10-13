# CORE-EEAT Scoring Rules (hand-scoring contract)

These rules replace the original deterministic scorer. Apply them exactly and show the arithmetic. Scores are advisory quality-control summaries for one declared artifact, profile, and observation date. They are not ranking, traffic, or citation predictions and are never compared across profiles.

Version identity to record in every report: **CORE-EEAT catalog 20.1.0, runbook 3.0.0, schema 3.0**.

## 1. Run identity (declare before scoring)

| Field | Rule |
|---|---|
| `target` | Exactly one URL, draft, or stable artifact identifier |
| `profile` | Exactly one of the nine profiles in §4 (= `content_type`) |
| `market` | Jurisdiction/audience used for disclosure and risk checks (e.g. `US`, `UK`, `DE`) |
| `publication_state` | `draft`, `staged`, or `live` |
| `observed_at` | The evidence freeze date (ISO). Evidence dated after it is invalid |

`content_type`, `market`, and `publication_state` are the required context. Changing target, profile, material context, observation date, or catalog version makes it a different run; never overwrite an earlier run, and only compare runs whose framework, profile, catalog version, target definition, context, and evidence window match.

## 2. Item states

| State | Meaning | Points | Needs |
|---|---|---:|---|
| `pass` | Criterion satisfied | 10 | Evidence |
| `partial` | Materially but incompletely satisfied | 5 | Evidence |
| `fail` | Not satisfied | 0 | Evidence |
| `unknown` | Applies, but sufficient evidence was not observed | none | Gap reason + what would resolve it |
| `na` | Genuinely inapplicable under one of the 18 conditional policies | excluded | Reason tied to the condition |

- An omitted item is `unknown`, never `partial` or `fail`.
- `na` is rejected for the 62 unconditional items. Never use `na` as a convenience for missing data.
- A failed veto item is still a `fail` (0 points) inside its dimension; veto policy applies after item scoring.
- Never redistribute weight around `unknown` items and never renormalize for missingness.

## 3. Evidence record (every pass/partial/fail)

Each observed item cites: **source** (URL/section/export), **source date**, **evidence type**, **confidence**.

| Evidence type | Use | Weight |
|---|---|---:|
| `measured` | Direct observation of the target or a first-party system of record | 1.0 |
| `user-provided` | A supplied record you could not independently verify | 0.8 |
| `calculated` | Reproducible transformation of cited inputs (e.g. citations per 500 words) | 0.8 |
| `estimated` | Stated assumption or model-based estimate | 0.5 |
| `proxy` | Adjacent signal standing in for the desired observation | 0.4 |

| Confidence | Meaning | Factor |
|---|---|---:|
| `high` | Evidence directly and reliably shows the item state | 1.0 |
| `medium` | Evidence is indirect or partly visible | 0.75 |
| `low` | Evidence is weak or ambiguous | 0.5 |

Confidence describes the reliability of the evidence for that item, not enthusiasm. An input export does not make a derived number `measured`; label it `calculated`.

## 4. Profile weights (dimension weight per profile; each column sums to 1.00)

| Dim | product-review | how-to-guide | comparison | landing-page | blog-post | faq-page | alternative | best-of | testimonial |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| C | 0.10 | 0.20 | 0.10 | 0.20 | 0.25 | 0.25 | 0.10 | 0.10 | 0.10 |
| O | 0.10 | 0.20 | 0.20 | 0.10 | 0.10 | 0.25 | 0.15 | 0.25 | 0.05 |
| R | 0.15 | 0.10 | 0.25 | 0.05 | 0.10 | 0.15 | 0.25 | 0.20 | 0.15 |
| E | 0.20 | 0.05 | 0.10 | 0.05 | 0.20 | 0.05 | 0.05 | 0.15 | 0.10 |
| Exp | 0.20 | 0.05 | 0.05 | 0.05 | 0.10 | 0.05 | 0.15 | 0.05 | 0.30 |
| Ept | 0.05 | 0.20 | 0.15 | 0.05 | 0.10 | 0.10 | 0.05 | 0.10 | 0.05 |
| A | 0.05 | 0.05 | 0.05 | 0.25 | 0.05 | 0.05 | 0.05 | 0.05 | 0.05 |
| T | 0.15 | 0.15 | 0.10 | 0.25 | 0.10 | 0.10 | 0.20 | 0.10 | 0.20 |

Choose the profile from what the artifact is, never from which profile scores best. If it cannot be inferred safely, ask one blocking question.

## 5. Coverage

`applicable items` = 80 minus items marked `na`.
`coverage %` = observed (pass + partial + fail) / applicable items x 100.

A comparable total requires **100% coverage**. Below 100%, report per-dimension coverage, the score interval (§8), and every `unknown` item; emit no raw or final score.

## 6. Arithmetic for a complete run (coverage = 100%)

1. **Dimension score** = (sum of item points in the dimension) / (number of applicable items in the dimension) x 10. Range 0-100. `na` items drop out of the numerator and denominator. Keep the exact value (fraction or 4+ decimals); do not round it.
2. **Weighted contribution** = dimension score x profile weight.
3. **Raw overall** = floor(sum of the 8 weighted contributions). Floor exactly once, at this final step. Never feed a rounded dimension value back into the total.
4. **Band** (label only, not an outcome probability): Excellent 90-100 · Good 75-89 · Medium 60-74 · Low 40-59 · Poor 0-39.
5. **Diagnostics (not totals):** GEO view = (C + O + R + E) / 4; SEO view = (Exp + Ept + A + T) / 4, each computed only when its four dimensions are complete. Label them diagnostics; never present either as an independent overall score and never use the old unweighted GEO/SEO average as a profile-independent total.

Item fix value (for the fix plan): raising one item from its current points `p` to 10 adds `(10 - p) x 10 / n_dim x weight` to the exact weighted total, where `n_dim` is the applicable item count of that dimension.

## 7. Vetoes, cap, verdict, status

Veto items: `CORE-EEAT-C01`, `CORE-EEAT-R10`, `CORE-EEAT-T04`. A veto counts only when the item is a **verified `fail`**. An `unknown` veto item never triggers the veto.

| Condition (evaluate top to bottom; first match wins) | Status | Verdict | Score state | Raw | Final | cap_applied |
|---|---|---|---|---|---|---|
| Execution stopped by a technical/security blocker (target unreachable, unsafe content, no artifact) | `BLOCKED` | `UNDECIDED` | `NOT_SCORED` | omitted | omitted | false |
| 2+ verified veto fails, coverage 100% | `DONE` | `BLOCK` | `SCORED` | shown | omitted | false |
| 2+ verified veto fails, other applicable items `unknown` | `DONE` | `BLOCK` | `NOT_SCORED` | omitted | omitted | false |
| Any applicable item `unknown` (fewer than 2 verified vetoes) | `NEEDS_INPUT` | `UNDECIDED` | `NOT_SCORED` | omitted | omitted | false |
| Complete, exactly 1 verified veto fail | `DONE_WITH_CONCERNS` | `FIX` | `SCORED` | shown | `min(raw, 59)` | true |
| Complete, 0 vetoes, raw >= 75 and no item is `fail` | `DONE` | `SHIP` | `SCORED` | shown | = raw | false |
| Complete, 0 vetoes, raw < 75 or any non-veto item is `fail` | `DONE_WITH_CONCERNS` | `FIX` | `SCORED` | shown | = raw | false |

Rules that go with the table:

- The 59 ceiling only lowers a score: raw 42 with one veto stays final 42.
- With 2+ vetoes no final score is emitted, because a capped number would imply comparability the gate does not support.
- `status` reports execution; `verdict` reports the gate. They are orthogonal. `DONE` does not imply `SHIP`; a business "no" is `BLOCK`, never `status: BLOCKED`.
- `NOT_SCORED` always pairs with `score_confidence: not_scored`.
- Partials do not block `SHIP`; only fails and vetoes do.
- Missing access to evidence never makes the artifact "failed"; it makes items `unknown`.

## 8. Score interval for incomplete runs

When any applicable item is `unknown`, compute and show (never as a total):

- **Lower bound** = floor of the weighted total with every `unknown` scored as `fail` (0).
- **Upper bound** = floor of the weighted total with every `unknown` scored as `pass` (10).

The interval is raw-score only. If a veto item is among the unknowns, say so: a verified fail would also apply the 59 cap or BLOCK.

## 9. Score confidence (complete runs only)

The original scorer's internal aggregation is not shipped; use this documented hand convention and show it:

1. For every observed item, reliability = evidence-type weight x confidence factor (e.g. measured/high = 1.0; user-provided/high = 0.8; estimated/medium = 0.375).
2. Mean reliability = sum of reliabilities / number of observed items.
3. `high` if mean >= 0.85; `medium` if 0.60 to < 0.85; `low` if < 0.60.
4. If any veto item's own evidence has reliability < 0.60, score confidence cannot exceed `low`.
5. Never round up and never upgrade a weak source because many weak observations agree.

A `SHIP` with `low` confidence carries a **confidence caveat**: the first line of the handoff summary leads with it, and the verdict is provisional until stronger evidence lands.

## 10. Report header (exact typed fields, before any prose)

```markdown
## CORE-EEAT Audit
**Status:** `DONE` | `DONE_WITH_CONCERNS` | `NEEDS_INPUT` | `BLOCKED`
**Verdict:** `SHIP` | `FIX` | `BLOCK` | `UNDECIDED`
**Score state:** `SCORED` | `NOT_SCORED`
**Profile / target / observed:** <profile> / <target> / <YYYY-MM-DD>
**Raw score:** <number> | omitted
**Final score:** <number> | omitted
**Confidence:** high | medium | low | not_scored
```

With any applicable `unknown`, add an **Unknown items** list before findings, one line per item with its qualified ID and the literal state: ``- `CORE-EEAT-T04`: `unknown` — affiliate status of outbound links not observable``. Phrases such as "evidence gap" or "needs evidence" never replace the typed state.

## 11. Advisory supporting checks

The humanizer/AI-slop pass and any visual or conversion review are advisory. They may inform non-veto items (typically O09, C07, Exp01, Exp08, Ept03) as evidence, but they never create a new veto and never change the veto set.

## 12. Change control

Never change item IDs, weights, conditional rules, vetoes, the 59 cap, the coverage rule, or the status/verdict table in a single audit. If the user wants a custom weighting, run it as a separately labeled, non-comparable diagnostic next to the standard profile result.
