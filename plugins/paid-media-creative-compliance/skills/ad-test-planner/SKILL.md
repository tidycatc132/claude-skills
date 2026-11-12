---
name: ad-test-planner
description: Design a statistically sound paid media test plan for ad copy, creative, landing pages, audiences, or bidding, with one hypothesis per test, a single changed variable, primary and guardrail metrics, required sample size and run time computed in code, a decision rule written before launch, and a test log. Use whenever the user asks to plan an A/B test, ad test, creative test, experiment, split test, what to test next, whether a result is significant, or how long a test should run, even if they only say we want to test new headlines.
---

# Ad Test Planner

Most ad tests fail before launch: several variables change at once, the metric is clicks instead of the business outcome, or the winner is called after two days. This skill fixes the design so the result can be trusted and acted on.

## Principle: decide before you launch
Write the hypothesis, metric, sample size, and decision rule before any data exists. A rule written after seeing results is a rationalization.

## Inputs
- What is being tested and why (a problem observed in the data, not a hunch)
- Current baseline: impressions, clicks, conversions, conversion rate, spend per day, from the account or an export
- `clients/<slug>/context.md`: conversion definitions, volume constraints, approval requirements
- Platform test tools available (Google Ads experiments, Meta A/B test, ad variations)

## Process
1. **State the hypothesis** in the form: "Changing X to Y will change metric M for audience A because R." If no reason R exists, the test is a guess; say so.
2. **Change one variable.** If two things must change together, call it a bundle test and accept that the cause is unknown.
3. **Choose the metric hierarchy:** one primary metric tied to the business outcome (conversion rate, cost per qualified lead), CTR only as a diagnostic, and guardrails (cost per conversion, lead quality, bounce rate) that must not degrade.
4. **Compute sample size in code.** Use a two-proportion test with the baseline rate, the minimum detectable lift worth acting on, 80% power, and 95% confidence. Report required conversions or clicks per arm and the days needed at current volume. If the days exceed a practical window (about 4 to 6 weeks), tell the user the test is underpowered and propose a bolder change, a larger audience, a higher-funnel proxy metric, or no test.
5. **Control the environment.** Split traffic evenly and randomly using the platform's experiment tool when possible; run arms simultaneously; avoid launching during seasonality, promotions, or other changes; freeze other edits to the tested entities.
6. **Pre-write the decision rule:** the metric and threshold that declares a winner, the minimum run time (at least one full weekly cycle), what happens on an inconclusive result (keep the control, document, move on), and who decides.
7. **Prioritize the backlog** when several ideas exist: score by expected impact, confidence from evidence, and effort, and sequence so tests do not interfere.
8. **Log it.** Create the test record: ID, dates, hypothesis, variants, metrics, sample target, decision rule, and later the result and the learning.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/test-plan-<name>.md` and append a row to `clients/<slug>/test-log.csv`.
```
Bottom line (2 sentences): the test, expected duration, and whether it is feasible.
Hypothesis and design table.
Sample size calculation with inputs shown.
Decision rule.
Risks and interference to avoid.
Prioritized backlog of next tests.
```
A result review reuses the same plan: compute the lift with a confidence interval in code, check guardrails, apply the pre-written rule, and record the learning.

## Rules
- Never declare a winner from an interim peek unless the plan uses a sequential method.
- Do not run more variants than the volume supports; each arm needs its own sample.
- Report effect size and interval, not only "significant."
- Do not launch or change experiments in a live account; deliver the plan for approval.
