---
name: budget-pacing-report
description: Check ad spend pacing across one or many client accounts, forecast month-end spend, and flag overspend, underspend, budget-capped campaigns, zero-spend campaigns, payment failures, and disapproval spikes. Use whenever the user asks about pacing, budget status, overspending, underspending, whether accounts will hit budget this month, month-end spend forecasts, or runs a daily or weekly paid media check across clients, even if they do not say pacing. Produces a portfolio table sorted worst first plus exact recommended fixes.
---

# Budget Pacing Report

Money problems are the fastest way to lose a client's trust and the cheapest ones to catch. This skill makes the pacing check fast, consistent, and portfolio-wide.

## Inputs
- Planned monthly budget per client and platform (from `clients/<slug>/context.md`, Budget section)
- Month-to-date spend per account and per campaign, daily granularity if available (platform API, connector, or export)
- Account status data: billing/payment state, disapproved ad counts, account suspensions
- If a client has no planned budget on file, mark it `NO PLAN` in the table and skip variance. Do not guess a budget.

State the data timestamp at the top of every report. Stale data labeled as stale is useful; stale data presented as current is dangerous.

## Calculations (do these in code, never in your head)
1. `expected_to_date = planned_budget * (days_elapsed / days_in_month)` by default. Use the client's seasonal or flighted curve instead if one is in the context file.
2. `forecast_month_end = MTD_spend + (trailing_7_day_average_daily_spend * days_remaining)`. Use the trailing 7 days rather than the MTD average because recent behavior predicts the rest of the month better, unless the account changed budgets mid-month, in which case use days since the change.
3. `variance_pct = (forecast_month_end - planned_budget) / planned_budget`.
4. In the first 3 days of a month, mark forecasts `LOW CONFIDENCE` and avoid escalating on variance alone.

## Status thresholds (shared defaults; a client file may override)
- **On track:** forecast within 10% of plan
- **Watch:** 10 to 20% off plan
- **Escalate:** more than 20% off plan, or any of the hard triggers below

Hard triggers that force Escalate regardless of variance: payment failed or account balance exhausted, account suspended, runaway spend (single-day spend above 2.5x the daily budget on a platform that should cap near 2x), zero spend on a campaign that should be live, or a large disapproval spike.

## Platform behavior to respect (so normal variance is not flagged as a problem)
- Google Ads may spend up to about 2x the daily budget on a given day but averages to the monthly cap. One high day is not overspend.
- Meta daily and lifetime budgets pace differently. Lifetime budgets front- or back-load by design, so check against the flight dates.
- Shared budgets and PMax can shift spend between campaigns. Evaluate at the account level first.
- Budget-limited status with strong CPA is an opportunity to flag, not only a risk.

## Report format
```
Pacing report | Data as of: <timestamp> | Accounts checked: N of M
Summary: X on track, Y watch, Z escalate, W could not be checked

| Client | Platform | Plan | MTD | Forecast | Variance | Status | Reason |
(sorted: Escalate, Watch, On track; worst variance first within each)

## Escalations
For each: what is wrong, evidence, exact recommended fix (for example, raise Campaign X daily budget from $A to $B, shift $C from Campaign Y, fix payment method), and the owner. Mark [NEEDS APPROVAL].

## Opportunities
Budget-limited campaigns beating target CPA.

## Could not be checked
Account, reason (no access, no plan on file, API error).
```
Put the status summary line first so a reader who stops after one line still gets the answer.

## Rules
- Read-only. Never change budgets or billing. Recommend and mark `[NEEDS APPROVAL]`.
- Report accounts you could not check explicitly. Silence on an account looks like health.
- Save the table as CSV or XLSX alongside the markdown so it can be filtered and so day-over-day changes can be diffed.
