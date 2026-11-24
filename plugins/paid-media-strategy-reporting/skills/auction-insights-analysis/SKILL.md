---
name: auction-insights-analysis
description: Analyze Google Ads and Microsoft Advertising auction insights, impression share, and competitor overlap data to show who the client competes with, where they win and lose, whether lost share is due to budget or rank, and what to do about it, with a dated competitor snapshot for tracking change over time. Use whenever the user asks who the competitors are in paid search, why impression share is low, whether to raise budget or bids, how the client compares in the auction, what changed in the competitive landscape, or provides an auction insights export, even if they only say a competitor seems to be outbidding us.
---

# Auction Insights Analysis

Auction insights are the only first-party view of who else is in the auction. Read correctly, they separate three different problems that look alike in the account: not enough budget, not enough ad rank, and a new competitor taking share. Each has a different fix.

## Principle: diagnose the cause before recommending spend
Lost impression share to budget calls for budget or efficiency; lost to rank calls for relevance, bids, or landing page work; rising competitor overlap calls for strategy. Do not recommend raising budget just because share is low.

## Inputs
- Auction insights exports by campaign or ad group, current and prior periods (impression share, overlap rate, position above rate, top of page rate, absolute top of page rate, outranking share)
- Campaign impression share columns: search impression share, lost IS (budget), lost IS (rank), top and absolute top share
- Performance data: spend, conversions, CPA by campaign
- Prior snapshot from `clients/<slug>/outputs/` for trend
- `clients/<slug>/context.md`: priorities, brand terms, known competitors

## Process
1. **Load and clean** the exports; auction insights are shown as ranges for low values ("< 10%"); treat these conservatively and note them.
2. **Separate brand from non-brand** campaigns; competitor behavior on brand terms is a different issue (competitors bidding on the client's name) from non-brand.
3. **Compute our position** by campaign: impression share, lost to budget, lost to rank, top-of-page rate. Compare to profitability: share is only worth buying where CPA meets the allowable target.
4. **Profile the competitors:** for each, overlap rate, position above rate, outranking share; classify as direct competitor, aggregator, or occasional. Identify the one or two that matter.
5. **Compare to the prior snapshot:** new entrants, changes in aggressiveness, our share change, and what changed in the account in the same period (budgets, bids, ads) so the cause is not misattributed.
6. **Diagnose and recommend** per campaign:
   - Lost to budget, with good CPA: raise budget or reallocate from weaker campaigns
   - Lost to rank: improve ad relevance, landing page experience, expected CTR, or bid adjustments; check bid strategy targets that are too tight
   - Brand conquesting: defend with brand campaign and sharp ad copy, assess cost versus protection, report competitors' trademark use through the platform when it violates policy
   - Profitable segments with low share: prioritize them
7. **Estimate the opportunity** in code: conversions available at current CPA if lost-to-budget share were captured, flagged as an upper bound given diminishing returns.
8. **Save the snapshot** so the next run can show change.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/auction-insights.md` plus a CSV snapshot for trend tracking.
```
Bottom line (3 sentences): who we compete with, where we lose, and the cause.
Our position table by campaign.
Competitor table with classification.
Change since last snapshot.
Recommendations ranked by profit impact, each tagged [NEEDS APPROVAL] when it changes spend or bids.
Limits: ranges, brand versus non-brand mixing, data period.
```

## Rules
- Competitor metrics are estimates; never state competitor budgets or results as facts.
- Do not change bids or budgets directly; recommend with expected effect.
- Do not buy share where the account loses money at the allowable CPA.
- Use public ad libraries only for further creative research (hand off to the ad library swipe file).
