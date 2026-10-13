# PPC Formulas

Core formulas for [SKILL.md](../SKILL.md), folded in from the google-ads-math skill. Show inputs, formula, and result for any figure you compute.

## Core metrics

```
CPA  = Total Spend / Total Conversions
ROAS = Revenue (conversion value) / Spend          (3.0x = $3 revenue per $1 spent)
ROAS as percentage = (Revenue / Spend) × 100
CTR  = Clicks / Impressions
CPC  = Spend / Clicks
CVR  = Conversions / Clicks
```

## Period-over-period

```
% change = (current - previous) / previous × 100
```

Compute each period's CPA, CTR, and ROAS from that period's totals, then compare.

## Targets

```
CPA target:  Current CPA = Spend / Conversions; at target when Current CPA <= Target CPA
             Additional conversions needed = (Spend / Target CPA) - Current Conversions
ROAS target: Current ROAS = Revenue / Spend; at target when Current ROAS >= Target ROAS
             Gap = Target ROAS - Current ROAS; Revenue needed = Spend × Target ROAS
Break-even ROAS = 1 / Profit Margin        (30% margin → 3.33x)
```

## Impression share opportunity

```
Missed Impressions = Total Impressions × ((1 - IS) / IS)
Estimated Missed Clicks = Missed Impressions × CTR
Estimated Missed Conversions = Missed Clicks × CVR
Estimated Missed Revenue = Missed Conversions × Avg Conv Value
```

Label these as estimates; they assume CTR and CVR hold on the missed traffic.

## Projections

```
Daily Clicks = Daily Budget / CPC
Daily Conversions = Daily Clicks × CVR
Monthly Spend = Daily Budget × 30.4
Monthly Conversions = Daily Conversions × 30.4
Monthly CPA = Monthly Spend / Monthly Conversions
```

Use 30.4 days per month (365/12).

## Rounding and sanity checks

- Round currency to 2 decimal places and percentages to 1 decimal place.
- Flag unrealistic inputs (for example CTR > 20%, or CPA < $1 on non-brand terms).
- When useful, add one sensitivity line, for example "If CPC rises 20%, CPA becomes …".
