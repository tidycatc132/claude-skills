# Measurement Protocol (inlined)

The rules for answering "did this change work?" when reading off-site and AI-traffic movement. Use it before crediting any change in AI referrals, AI citations, mentions, or links to a cause.

## The problem

SEO/GEO outcomes are **delayed** (a change surfaces in an AI answer or a ranking only after the engine re-crawls and re-indexes) and **confounded** (the number also moves because the engine changed, a competitor changed, or the category shifted). A raw before/after on the final outcome is rarely attributable. Separate the fast proxy from the slow outcome, label which is which, and attribute slow outcomes against a control.

## Latency layers that apply here

| Layer | What it measures | Latency | Proxy or outcome |
|---|---|---|---|
| 1. Crawler access | Can AI/search bots fetch and parse the page? | Instant | Precondition |
| 3. Surfacing | Does an engine cite you for a bare query, unprompted? | Days-weeks | Outcome (GEO) |
| 4. Rankings / clicks / referrals | Position, impressions, CTR, referral sessions | Weeks-months | Outcome (SEO) |

- Never read a missing citation as "the content is bad" until access is confirmed (bot gets a 200 with content in raw HTML). "Not crawled yet" and "crawled but not chosen" look identical and have different fixes.
- The WebSearch spot-check is a surfacing read through one search layer: an outcome for that layer, a **proxy** for other AI engines.
- AI-referral sessions are a layer-4 style outcome: slow, confounded, and needing a control.

## Attribution requires a control (non-negotiable for surfacing and traffic)

Measure a **holdout in parallel**: the organic channel for the same window, an unchanged page or sibling URL, or a competitor in the same query panel. **Report delta-vs-control, not raw delta.** A raw "+15% AI sessions" means nothing if total traffic or the whole category rose 15%.

Fix the measurement window **before** you start (for surfacing, typically 2-6 weeks) and do not react to day-to-day noise inside it.

## The loop

1. **Baseline**: write a snapshot of the signal before the change.
2. **One attributable change**: a single change, or a clearly labeled batch. Two changes at once destroy attribution.
3. **Wait the readback window** (below). Re-snapshot.
4. **Diff against the control**, not against zero (hand arithmetic, shown).
5. **Label every number**: Measured / User-provided / Calculated / Estimated / Proxy-for-<outcome>. Never render a proxy as if it were the outcome.

## Readback windows

Set before the change; do not react inside the window.

| Change type | Readbacks |
|---|---|
| Content refresh (existing page) | 7 / 14 / 28 / 56 days |
| New content / new asset | 14 / 28 / 56 / 90 days |
| Technical fix | daily ×7, then 28 |
| AEO/GEO surfacing | weekly |
| Influencer activation | per post + 7 / 30 days |
| Paid campaign change | exit learning phase first, then 7 / 14 days |

**Readback fields to record**: change ID · owner · target/population · control and candidate windows · sample/exclusions · sources and provenance · primary metric and guardrails · attribution/lag · effect and uncertainty · method · data-quality incidents · decision · rationale · next action · next readback date.

## Register before exposure

Before the change, record: unit of analysis, population and exclusions, control and candidate, primary metric and guardrails, metric direction, outcome truth source, attribution rule, conversion lag, hypothesis, minimum practically important effect, sample plan, start/stop/read dates, and decision owner. A plan written after looking at outcomes is **exploratory**, not confirmatory.

## Method-appropriate evidence (compute by hand, show arithmetic)

- **Binary rates** (conversion rate, cited-rate): compare two proportions with a pre-specified method and report the absolute lift and its uncertainty. For a two-proportion z-test: pooled p = (x1 + x2) ÷ (n1 + n2); SE = √(p(1−p)(1/n1 + 1/n2)); z = (p1 − p2) ÷ SE. Label outputs Calculated.
- **Continuous or skewed metrics**: report sample sizes and robust summaries (median); do not describe a rank test as a test of mean difference.
- **Time series or non-randomized changes** (most AI-traffic reads): use a matched control, interrupted series, or difference-in-differences. A generic A/B p-value does not repair confounding.
- **Small or dependent samples**: stay exploratory.

Defaults when no better policy exists, declared before exposure: alpha = 0.05, power = 0.80, and a **15% relative practical-lift** reference. For a zero control rate, relative lift is undefined; use a pre-registered absolute effect.

## Verdicts

- **Promote**: only when the pre-committed primary evidence and practical-effect bar are met, guardrails are acceptable, attribution and data quality are intact, and the decision owner accepts the tradeoff.
- **Keep-testing**: only under a registered continuation rule (the window is not over, or a pre-planned extension).
- **Rollback**: may be immediate for a safety, legal, reliability, or material business guardrail, even before efficacy is resolved.
- **Unproven**: everything else. Absence of significance is not proof of equivalence.

**Do not promote** when sample/precision is inadequate, attribution is dirty, exclusions changed after the fact, seasonality or interference explains the move, collection failed mid-window, repeated peeking is unhandled, or only a proxy improved while the declared outcome did not.

The decision belongs to the named owner (the user). The skill supplies the evidence and the proposed label.

## What this protocol does not give you

- **No certainty.** A proxy can improve while the outcome does not, and vice versa.
- **No fast surfacing.** AI surfacing and traffic stay slow. Any claim of a minute-level "will I be cited" loop is false.
- **No attribution without a control.** A raw before/after on a confounded outcome is a story, not evidence.
- **Single runs are noise.** AI output is stochastic; sample and report rates.
- **Collection is semi-manual.** Snapshots structure the data; they do not automate asking the AI engines.
