---
name: budget-forecast-model
description: Build a spreadsheet forecast model that projects clicks, leads or sales, cost, and revenue from budget, cost per click, conversion rates, and seasonality, with scenario cases, what-if sensitivity, and a comparison of forecast versus actuals with variance explanations. Use whenever the user asks what a budget will deliver, how much to spend to hit a lead or revenue target, to forecast paid media results, to model budget scenarios, to update a forecast with actuals, or to explain why results differ from the forecast, even if they only say what will an extra 5k get us.
---

# Budget Forecast Model

Clients ask two questions all the time: what will this budget produce, and what would more budget produce. A forecast answers both honestly only if it exposes its assumptions, uses ranges, and reflects diminishing returns, since extra spend rarely buys results at the average rate.

## Principle: transparent assumptions, scenarios, live formulas
Every output traces to an input cell the user can change. The workbook uses formulas, not pasted values, so it can be updated.

## Inputs
- Historical data by campaign and month (spend, impressions, clicks, conversions, revenue) when available
- Targets and allowable CPA
- Seasonality indicators (prior-year monthly index, search volume trends)
- Proposed budget scenarios and constraints (impression share ceilings, capacity limits)
- `clients/<slug>/context.md`

## Process
1. **Establish baselines in code** from history: cost per click, click-through rate, conversion rate, average value, by campaign type. Use trailing 90 days with outliers noted; with under 30 conversions, widen the ranges and flag low confidence.
2. **Model the funnel:** budget / CPC = clicks; clicks x conversion rate = conversions; conversions x value = revenue; cost per conversion and ROAS or return on spend follow.
3. **Apply seasonality** with a monthly index so the plan does not assume flat demand.
4. **Account for diminishing returns:** model incremental spend at a rising marginal CPC or a falling conversion rate, bounded by lost impression share to budget. State the curve assumption and, when impression share data exists, cap volume at the available demand.
5. **Build three scenarios** (conservative, base, stretch) by shifting CPC, conversion rate, and volume assumptions, and one what-if table of budget versus results at several spend levels.
6. **Forecast versus actuals:** for months that have passed, compare forecast to actual, and decompose variance into volume (clicks), efficiency (CPC), and conversion rate effects. Re-forecast the remaining months from the actuals.
7. **Check the sanity of results** against allowable CPA and capacity; flag scenarios that exceed available impression share or breach targets.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/budget-forecast.xlsx` with tabs: Inputs, Baselines, Forecast (by month and scenario), What-If, Actuals vs Forecast, Notes. Include a short markdown summary.
```
Bottom line (2 sentences): what the budget is expected to produce, as a range.
Key assumptions and their sources.
Scenario table.
Marginal return view: what the next dollar buys.
Variance explanation when actuals exist.
```

## Rules
- Present ranges; never a single point as a promise.
- Mark every assumption cell visibly and keep inputs separate from calculations.
- Do not extrapolate linearly beyond the demand the account can reach.
- Recalculate formulas and verify there are no errors before delivering.
