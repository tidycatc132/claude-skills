---
name: "bid-strategy-decision"
description: "Recommend the right bid strategy and target for a campaign from conversion volume, data quality, and goals, with a safe transition plan. Use when choosing or changing bidding, setting tCPA/tROAS, or bids stop performing."
---

# Bid Strategy Decision

Automated bidding is powerful when it has plentiful, accurate conversion data and a realistic target, and destructive when it does not. Most bidding problems are data problems or target problems dressed up as strategy problems. This skill checks the preconditions before recommending a strategy, and plans the switch so the account is not whipsawed.

## Principle: preconditions first, target realism second, switch carefully
A strategy is only as good as the signal behind it. Verify the signal, set a target the account can reach based on its own history, and change one thing at a time with a defined evaluation period.

## Inputs
- Campaign performance for 90 days (conversions by day, CPA, ROAS, impression share, budget constraint status), and the current strategy and target, plus change history
- Conversion tracking status and which actions the strategy optimizes, including conversion values
- `clients/<slug>/context.md`: goals, allowable CPA and target ROAS, budget, qualified lead definition
- Platform, campaign type (Search, PMax, Demand Gen, Meta, LinkedIn), and whether the campaign shares a budget or portfolio strategy

## Decision process
1. **Check signal quality.** Is the optimized conversion the real outcome? Duplicates, junk leads counted as conversions, or low-value micro-conversions as primary will teach the system the wrong thing. If quality is questionable, recommend fixing tracking or switching the primary action first, before changing strategy.
2. **Check volume.** Count conversions per campaign over 30 days (and per ad set for social). Rule-of-thumb gates, stated as defaults:
   - Under about 15 conversions per month: manual CPC or maximize clicks with a bid cap, or maximize conversions without a target, with realistic expectations; consider consolidating campaigns to pool data.
   - About 15 to 30: maximize conversions or maximize conversion value without a target.
   - 30 or more with stable results: target CPA or target ROAS become reasonable.
   - Social ad sets: roughly 50 optimization events per week for stable learning; below that, move the optimization event up the funnel or consolidate.
3. **Check goal fit.** Lead generation with a consistent lead value fits CPA strategies; ecommerce or variable deal values fit value-based strategies with accurate values; brand protection may fit a target impression share or manual control; new campaigns with no history start with a volume strategy and add targets later.
4. **Check target realism.** Compute the account's actual CPA or ROAS for the last 30 and 90 days and its variability. Set any target within about 10 to 20 percent of recent actual performance rather than at the ideal number; tight or aspirational targets throttle delivery and starve volume. Move toward the allowable ceiling in steps.
5. **Check constraints.** Budget limited by a large margin, very tight budget relative to target CPA (the budget should usually cover at least several conversions per day-equivalent at target), seasonality or promotions, conversion lag (long lag means recent data undercounts, so do not judge early), and shared budgets.
6. **Choose and justify.** Recommend one strategy and target, and explain the alternative considered and why it lost.
7. **Plan the transition.** Change one campaign first when multiple are candidates; avoid changes during seasonal peaks or right after other large changes; set the evaluation window (typically two to four weeks, longer with conversion lag); define success and rollback criteria in advance (for example, CPA more than 25 percent above target after the learning period with stable volume triggers a rollback or retarget); note that budget changes during learning can reset it, so avoid them.
8. **Set expectations.** Short-term volatility is normal during learning; state the expected range and what is not normal.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/bid-strategy-<campaign>.md`.
```
Bottom line (2 sentences): recommended strategy and target, and confidence.
Precondition checks: signal, volume, goal fit, target realism, constraints, each pass or fail with numbers.
Recommendation and the alternative rejected.
Transition plan: sequence, evaluation window, success criteria, rollback criteria.
Risks and expected volatility.
[NEEDS APPROVAL] marker for the live change.
```

## Rules
- Do not recommend a target-based strategy when volume or signal quality does not support it, even if the client asks for one. Explain the risk and offer the stepping-stone path.
- Do not change the strategy and the target and the budget in the same week.
- Respect the 14-day cooldown between strategy or target changes.
- Platform thresholds change; verify current platform guidance if a recommendation hinges on a specific minimum.
- Read-only. Recommend; a human applies the change.