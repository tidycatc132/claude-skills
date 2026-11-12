---
name: ppc-weekly-optimization
description: Run the weekly optimization pass on a paid media account (Google Ads, Microsoft Ads, Meta, LinkedIn) and return a short, ranked list of the changes most likely to improve results, each with evidence, expected impact, risk, and the specialist who should execute it. Checks measurement trust first, then outcomes against target, week-over-week and year-over-year changes, waste, opportunity, and budget constraints. Use whenever the user asks for a weekly review, account optimization, what should we change this week, an optimization pass, an account health review, where is spend being wasted, or runs a recurring account cycle across clients, even if they do not say weekly.
---

# PPC Weekly Optimization

Optimization is easy to do constantly and hard to do well. The failure modes are changing things too often (resetting learning), reacting to noise, and fixing metrics that do not matter. This skill imposes a fixed routine that produces a short list of changes that deserve to happen, and an explicit "leave alone" list for things that do not.

## Principle: fewer, better changes, ranked by impact
Smart bidding needs stability, and small samples lie. The output is capped at the top ten actions, ranked by `impact x confidence / effort`, with the evidence for each. Doing nothing is a legitimate recommendation when the data does not support a change.

## Inputs
- Performance data by account, campaign, and relevant segments for the review window (default last 7 days vs prior 7 days, with 28 and 90 day context, and the same period last year for seasonality)
- `clients/<slug>/context.md`: targets (CPA, ROAS), budget, goals, restrictions, qualified lead definition
- Latest pacing report and tracking status, if they exist in `clients/<slug>/outputs/`
- Change history for the review window, to avoid double-adjusting and to attribute effects
- Search term report (search), creative and audience breakdowns (social)

## Routine
1. **Measurement gate.** Confirm tracking is trusted for the window: conversion volume plausible versus clicks and prior trends, platform versus GA4 and CRM within tolerance, no recent site or tag changes. If suspect, stop and recommend running the conversion tracking audit; analyze only non-conversion metrics, labeled as such.
2. **Outcomes against target.** Leads, CPA, ROAS, and revenue versus target and versus prior periods, at account and campaign level. Start here, because efficiency metrics matter only in service of these.
3. **Explain the movement.** If a key metric moved meaningfully, decompose into volume, efficiency, conversion rate, and mix using the anomaly triage method. Name the dominant driver.
4. **Respect learning and sample size.** Skip judging campaigns inside a learning period, or those changed within the last 14 days, or with under the minimum volume (default 30 conversions or 100 clicks for the metric in question). List them under Monitor with the date they become judgeable.
5. **Find waste.** Search: queries, match types, geo, device, and daypart with spend and no outcomes, after the sample-size rule. Social: fatigued ads, learning-limited fragmentation, poor placements. Both: budget parked in campaigns far above target CPA.
6. **Find opportunity.** Budget-limited campaigns beating target CPA; high impression share lost to rank on efficient campaigns; segments (device, geo, audience, time) converting well but underfunded; winning ads and keywords worth expanding.
7. **Check strategy fit.** Bid strategy versus conversion volume, targets versus achievable history, budgets versus demand, and anything at odds with the media plan.
8. **Draft the actions.** Each has: the action, evidence, expected impact (directional with a range if quantifiable), risk (including learning reset), owner (search specialist, social specialist, creative, tracking, landing page, or strategist), effort, and `[NEEDS APPROVAL]` if it touches a live account.
9. **Rank and cap at ten.** Merge actions that are the same fix. Move low-confidence items to Monitor.
10. **Define the leave-alone list.** Things that look off but should not be touched this week, and why (for example, in learning, recently changed, within normal variance).

## Output
Save to `clients/<slug>/outputs/YYYY-MM/weekly-optimization-YYYY-MM-DD.md` and a change list sheet when applicable.
```
Bottom line (2 sentences): status versus target and the most important change.
Measurement status: trusted / suspect.
Outcomes table: metric, this week, prior, target, status.
What changed and why.
Ranked actions (max 10): action, evidence, impact, risk, owner, effort, [NEEDS APPROVAL].
Monitor list: item, what to watch, date it becomes judgeable.
Leave-alone list.
Assumptions and data gaps.
```
If several accounts are reviewed, add a one-table portfolio summary that sorts accounts by urgency.

## Rules
- Read-only. Recommend; humans or the specialist apply approved changes.
- Never recommend changing a bid strategy or target more than once per 14 days, or while the campaign is in learning.
- Do not optimize to a platform metric that conflicts with the business outcome (for example, raising CTR while qualified leads fall).
- Cite date range and source for every figure; compute in code.
- When approved actions are executed, log them in the client's change log so next week's review can attribute results.
