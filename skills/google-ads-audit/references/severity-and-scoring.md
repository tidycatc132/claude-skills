# Severity Defaults, Thresholds, and Scoring

Used by every dimension in [SKILL.md](../SKILL.md). Apply the default severity unless the account context clearly changes the impact; if you move a finding up or down, say why in its [Impact] text.

## Numeric thresholds

From the audit's Severity Framework and the companion analysis skill's anomaly thresholds:

| Check | Threshold | Severity |
|---|---|---|
| Conversion tracking missing | No enabled conversion action, or 0 conversions recorded across all actions while the account spends | Critical |
| Zero conversions with high spend | Any campaign with spend > $50 and 0 conversions in the window | Critical |
| Wasted spend share | Wasted spend > 20% of total spend | High |
| Budget-capped top performer | Average daily spend ≥ 95% of daily budget, on a campaign with above-account-average ROAS (or below-average CPA) | High |
| Budget-capped campaign (other) | Average daily spend ≥ 95% of daily budget | Medium |
| Impression share lost to budget | > 20% | High |
| Impression share lost to rank | > 30% | Medium |
| Very low Quality Score | QS 1–2 (QS < 3) on keywords with spend | High |
| Low Quality Score | QS 3–5 on keywords with > 100 impressions | Medium |
| CPA spike | CPA up > 20% vs previous 30 days | High |
| CTR drop | CTR down > 15% vs previous 30 days | Medium |

QS 3 is not covered by the original framework ("QS < 3" is High, "QS 4-5" is Medium); this skill rates QS 3 as Medium.

## Default severities for checks without a number

| Dimension | Finding | Default severity |
|---|---|---|
| 1 Structure | Biggest budgets going to the worst ROAS/CPA campaigns | High |
| 1 Structure | Ad groups with 20+ loosely themed keywords | Medium |
| 1 Structure | Inconsistent or non-descriptive naming | Low |
| 1 Structure | Many paused entities cluttering the account | Low |
| 2 Tracking | Lead actions counted "every" instead of "one" | High |
| 2 Tracking | Sales account with no conversion values, or default values only | High |
| 2 Tracking | Secondary/micro actions included in the Conversions column used for bidding | High |
| 2 Tracking | Last-click attribution where data-driven is available | Low |
| 3 Keywords | No negative keywords and no shared negative lists on Search campaigns | High |
| 3 Keywords | Broad match on Manual CPC without Smart Bidding | Medium |
| 3 Keywords | High-spend zero-conversion search terms not yet added as negatives | Medium (rolls up into the wasted-spend share) |
| 4 Creative | RSA ad strength Poor | Medium |
| 4 Creative | RSA ad strength Average | Low |
| 4 Creative | Search campaign missing sitelinks or callouts | Medium |
| 4 Creative | Missing structured snippets or call assets | Low |
| 4 Creative | Ad groups with a single enabled ad / no ad changes in 30 days | Low |
| 4 Creative | All ads point to the home page | Medium |
| 5 Bidding | Bid strategy that does not match the goal (for example Max Clicks on a conversion goal with 30+ conversions/month) | Medium |
| 5 Bidding | Shared budget where one campaign takes most of the spend and the others are starved | Medium |
| 5 Bidding | No device/location/schedule adjustments on Manual CPC campaigns with clear variance | Low |
| 6 Targeting | Mobile vs desktop CPA variance > 50% with no adjustment or split | Medium |
| 6 Targeting | Location option "presence or interest" on a local business | Medium |
| 6 Targeting | No remarketing or customer-match audiences in observation | Low |
| 6 Targeting | Display/Video with no placement exclusions | Medium |
| 7 Waste | Region with spend and 0 conversions, or CPA > 2× account CPA | Medium |
| 7 Waste | Placements with spend and 0 conversions (apps, parked domains, kids content) | Medium |

## Wasted spend calculation

```
Wasted spend (window) = spend on search terms with 0 conversions
                      + spend on Display/Video placements with 0 conversions
Wasted share          = Wasted spend ÷ total account spend × 100
Wasted spend / month  = Wasted spend (window) ÷ days in window × 30.4
```

- Do not add low-QS keyword spend or region spend on top; they overlap with search-term spend. Report them as separate lines, not in the total.
- Performance Max term-level waste is not measurable (no cost on search term insights). State it as excluded.
- If the search terms export is capped (for example top 1,000 rows), say the total is a floor.

## Scoring (Overall Score X/10)

The original skill asks for an Overall Score out of 10 without a formula. Use this rule so scores are comparable between audits:

1. Score each of the 7 dimensions out of 10. Start at 10 and deduct per finding: Critical −4, High −2, Medium −1, Low −0.5. Floor 0.
2. A dimension with no data is **Not assessed** and is left out of the average.
3. Overall Score = average of the assessed dimension scores, rounded to 1 decimal place.
4. Show the arithmetic in a small table (dimension, findings by severity, score).

## Quick wins

A quick win is a High or Medium finding the user can fix in under an hour without new creative or budget, for example adding negatives from the zero-conversion search terms, switching lead conversion counting to "one", adding sitelinks and callouts, excluding wasteful placements, or raising the budget on a capped top performer. Pick the 3 with the largest spend or conversion impact.
