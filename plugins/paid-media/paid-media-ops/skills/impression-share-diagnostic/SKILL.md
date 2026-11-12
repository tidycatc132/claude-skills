---
name: impression-share-diagnostic
description: Diagnose impression share on Google Ads and Microsoft Ads search and shopping campaigns by separating impression share lost to budget from lost to rank, checking quality and bid drivers, auction insights competitor movement, and efficiency at the margin, then recommend whether to raise budget, raise bids or targets, improve ad and page quality, narrow targeting, or leave things alone. Use whenever the user asks why impression share dropped, whether to increase budget, whether a campaign can scale, what is limiting a campaign, whether a competitor is outbidding us, why impressions fell, or how much more volume is available, even if they never say impression share.
---

# Impression Share Diagnostic

Impression share (IS) answers a business question: how much of the available demand are we capturing, and what is stopping the rest? The fix depends entirely on the reason. Budget-lost share needs money only if the marginal clicks are profitable; rank-lost share needs better bids, quality, or relevance, not more budget. Mixing those up wastes money in both directions.

## Principle: scale only what is efficient at the margin
High lost IS is an opportunity only if the extra clicks would clear the CPA target. Average CPA hides that the marginal click is more expensive than the average click. Check before recommending more budget.

## Inputs
- Campaign (and ad group where useful) metrics for 30 to 90 days with daily or weekly granularity: impressions, clicks, cost, conversions, search impression share, lost IS to budget, lost IS to rank, top and absolute top impression share, average CPC, quality score components
- Auction insights (overlap rate, position above rate, outranking share, top-of-page rate) for the same periods
- Budget and bid strategy history; change history
- `clients/<slug>/context.md`: target CPA or ROAS, budget limits, goals, geo

## Process
1. **Establish the trend and the split.** Chart total IS, lost to budget, and lost to rank over time. Note when changes began and compare to change history, seasonality, and competitor activity.
2. **Separate branded and non-branded campaigns.** Brand IS should usually be very high; a drop matters for a different reason (competitors bidding on the brand) than non-brand losses.
3. **If lost to budget is high:** check whether the campaign hit its budget early in the day (delivery by hour), whether it is efficient (CPA at or below target on a sufficient sample), whether segments (geo, device, hour, audience) are carrying inefficient spend that should be trimmed to free room, and what the incremental cost would be. Estimate the volume and CPA at higher spend using the observed relationship between spend and conversions across recent budget levels, with a range and explicit assumptions. Recommend a budget change only where marginal performance holds up.
4. **If lost to rank is high:** diagnose drivers: expected click-through rate, ad relevance, landing page experience, bid or target too low, ad strength and asset coverage, match type or targeting mismatches, and quality score trends by keyword. Use auction insights for competitor entries or aggression: overlap and position-above rates moving up signal pressure; a flat competitor set with falling IS points to your own quality or bid changes. Quantify potential gain from fixes before recommending bid increases.
5. **Check bid strategy effects.** Target CPA or ROAS set too tight causes rank loss because the system declines auctions it cannot win at the target; relaxing the target is a rank fix, with a cost.
6. **Account for conversion lag and seasonality** before concluding a drop is real.
7. **Decide.** One recommended path per campaign: raise budget by X, relax target to Y, fix quality via specific changes, trim inefficient segments and reallocate, or no action. Include the expected volume and CPA effect with a range, the risk, and the evaluation window.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/impression-share-<campaign>.md`.
```
Bottom line (2 sentences): what is limiting the campaign and the recommended move.
IS split table: campaign, IS, lost to budget, lost to rank, CPA vs target, verdict.
Competitor movement (auction insights) summary.
Marginal efficiency estimate with range and assumptions.
Ranked actions with owner, impact range, risk, [NEEDS APPROVAL] for live changes.
What to monitor and when to judge.
```

## Rules
- Do not recommend more budget for campaigns above target CPA, even if lost IS to budget is high.
- Do not treat auction insights as complete: they show competitors in shared auctions only, and shares are estimates.
- Respect learning periods and the 14-day cooldown on strategy or target changes.
- Compute in code; cite date ranges and sources. Read-only; recommend, do not apply.
