---
name: ppc-anomaly-triage
description: Diagnose why paid media performance changed. Rules out tracking and measurement problems first, then decomposes the change into volume, efficiency, and conversion drivers, drills into the dominant segment, and returns a ranked cause list with next actions. Use whenever the user says CPA went up, leads dropped, conversions fell, ROAS tanked, spend spiked, impressions fell, performance changed, something is off in the account, or asks what happened or why in Google Ads, Microsoft Ads, Meta, or LinkedIn, even if they do not say anomaly or triage.
---

# PPC Anomaly Triage

When results move, the instinct is to start changing bids and budgets. That is usually the wrong first move: roughly half of sudden drops are measurement problems, and changing an account to fix a tracking break makes things worse. This skill enforces an order of investigation that finds the real cause fast.

## Step 0: Define the anomaly precisely
Write one sentence: metric, direction, magnitude, comparison period. For example, "Leads down 42% over the last 7 days vs the prior 7." Pick the comparison deliberately: prior period for sudden shifts, same period last year for seasonal ones, and check both when unsure. Note the exact date the change began, since the date is the strongest clue to the cause.

## Step 1: Rule out measurement (always first)
Check, in this order, and record each as cleared, suspect, or broken:
1. Did conversion volume change in every channel at once while clicks and spend stayed flat? That pattern points to tracking.
2. Compare platform conversions to GA4 and CRM/call data for the same dates. A sudden new gap points to tracking.
3. Look for site changes on or just before the start date: new form, plugin or theme update, tag container publish, checkout or thank-you page change, consent banner change.
4. Check conversion action settings and any recent change history.

If measurement is suspect or broken, stop the performance diagnosis and report that finding first. Recommend handing the verification to the tracking-measurement-engineer. Continue only on metrics that do not depend on conversions (spend, impressions, clicks, CTR, CPC), labeled as such.

## Step 2: Decompose the change
Use code to split the move into drivers. For a CPA or lead-volume change:
- **Volume:** impressions, impression share, lost IS to budget vs rank, clicks
- **Efficiency:** CTR, CPC, auction pressure
- **Conversion:** click-to-lead rate, by device and landing page
- **Mix:** share of spend moving between campaigns, networks, or audiences

Name the dominant driver, meaning the one that explains most of the change, and quantify its share. State the arithmetic so a reader can check it.

## Step 3: Drill into the dominant driver
Segment only along dimensions relevant to that driver, and stop when one segment explains most of the change:
- Volume or IS: campaign, budget-limited flags, rank loss, geo, daypart, device
- Efficiency: auction insights shifts (new competitor, higher overlap), match type expansion, search term mix, placement or audience drift
- Conversion: landing page, device, source, form or call flow, lead quality
- Mix: bid strategy or learning-phase change, PMax shifting to low-value traffic

Cross-check with the account change history and platform notifications: bid strategy edits, budget changes, new campaigns, disapprovals, policy limits, learning phase resets.

## Step 4: Check for external causes
Seasonality, holidays, weather for home services, competitor promotions, news, platform-wide issues or algorithm changes, client-side changes (pricing, offer, hours, capacity). Search the web for platform incident reports when the pattern is account-wide and sudden.

## Step 5: Return the diagnosis
```
Bottom line (2 sentences): what changed, and the most likely cause with confidence level (high / medium / low).

Measurement status: cleared / suspect / broken, with evidence.

Decomposition: table of drivers with each one's share of the change.

Ranked causes: each with evidence for, evidence against, and what would confirm it.

Actions, ranked by impact times confidence over effort: each with owner (which specialist) and [NEEDS APPROVAL] if it touches a live account.

What to watch and for how long before concluding.
```

## Rules
- Never recommend an account change before measurement is cleared or labeled unverifiable.
- Respect learning periods and sample size. If there is too little data to separate signal from noise, say so and give the date or volume at which the answer becomes reliable, rather than forcing a cause.
- Present competing explanations honestly. If two causes fit the evidence, say so and name the test that separates them.
- Cite source and date range for every figure. Compute in code.
- Read-only: recommend, do not apply.
