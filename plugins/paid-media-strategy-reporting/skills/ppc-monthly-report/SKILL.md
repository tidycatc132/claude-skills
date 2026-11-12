---
name: ppc-monthly-report
description: Produce a monthly paid media performance report for a client from platform and analytics exports, covering spend, results versus goals, month-over-month and year-over-year changes, what drove the movement, wins and problems, actions taken, and next month's plan, with every figure computed in code and reconciled before delivery. Use whenever the user asks for a monthly PPC report, paid media performance report, client report for Google Ads or Meta, a month-end recap, or to turn account exports into a report, even if they only say write up how the account did last month.
---

# PPC Monthly Report

A client report must answer four questions fast: did we hit the goal, why, what did we do about it, and what happens next. Numbers without explanation are a data dump; explanation without verified numbers is a risk to the relationship. This report does both and checks itself before it goes out.

## Principle: figures from code, story from evidence
Every number is computed by a script from the exports and reconciled to platform totals. Every claim about cause is tied to evidence in the data or to a change log entry, and uncertainty is stated.

## Inputs
- Platform exports for the month and comparison periods: campaign-level spend, impressions, clicks, conversions, conversion value, impression share
- GA4 or CRM data for outcomes (leads, qualified leads, revenue) when available
- Goals and targets, allowable CPA, from `clients/<slug>/context.md`
- Change log: edits made during the month (budgets, bids, ads, structure)
- Prior report for continuity of format and open items

## Process
1. **Load and validate data.** Check the date ranges, that campaign totals equal account totals, and that conversion definitions match the prior month. Note any tracking issue that affects comparability.
2. **Compute metrics in code:** spend, clicks, CTR, CPC, conversions, conversion rate, CPA or CPL, conversion value, ROAS, impression share. Compute month over month and year over year changes with the percentage and absolute difference, and pacing against the budget.
3. **Compare to goals:** each goal as met, close, or missed, with the gap.
4. **Explain the movement.** Decompose changes in CPA or conversions into volume, cost per click, and conversion rate effects. Tie causes to the change log, seasonality, competition (auction insights), tracking issues, or landing page changes. Where the cause is unknown, say so and say what will be checked.
5. **Select the story:** the two or three most important findings (a win, a problem, an opportunity), not every metric. Show the top and bottom campaigns by efficiency and the segments driving them.
6. **Report the work done:** actions taken and their measured effect where measurable, honestly labeled when too early to tell.
7. **Plan next month:** priorities, tests, budget recommendations, decisions needed from the client, and risks.
8. **Self-check before delivery:** recompute totals, confirm percentages, confirm every figure in the text matches the tables, check for spelling of the client's name and the date range, and confirm no claim exceeds the evidence. Record the checks.

## Output
Save the report to `clients/<slug>/outputs/YYYY-MM/monthly-report.md` plus `monthly-report-data.xlsx` with the supporting tables. When the client format is a branded deck or PDF, hand the content to the appropriate document or deck skill.
```
Headline (3 sentences): result versus goal, the main driver, and the next step.
Scorecard: goal metrics, this month, last month, change, status.
What happened and why.
Campaign and segment detail (top and bottom).
Work completed.
Next month's plan and decisions needed.
Appendix: definitions, data notes, reconciliation.
```

## Rules
- Do not round away a missed goal, and do not bury bad news below good.
- Distinguish platform-reported conversions from CRM-verified outcomes.
- Never attribute a result to an action done late in the month without evidence.
- Keep language plain; define any term the client has not used before.
