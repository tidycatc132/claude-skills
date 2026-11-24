---
name: media-plan-builder
description: Build a paid media plan for a client from goals, budget, allowable CPA, audience, and market, covering platform and campaign-type selection, budget split with rationale, geo and audience targeting, funnel structure, expected volume and cost ranges, measurement plan, testing roadmap, risks, and a month-by-month calendar. Use whenever the user asks for a media plan, paid media strategy, channel mix, budget allocation across platforms, a proposal for new ad spend, a quarterly plan, or how to spend a given budget, even if they only say how should we spend the budget.
---

# Media Plan Builder

A media plan turns a goal and a budget into decisions the team can execute and the client can approve: where the money goes, what it should produce, how it will be measured, and what happens if it does not. It should survive being read in five minutes and checked in an hour.

## Principle: choose fewer channels, fund them enough to learn
A budget spread over too many channels produces data nowhere. Allocate to the channels with the clearest demand and economics first, size each so it can reach conversion volume the bidding needs, and reserve a slice for testing.

## Inputs
- Goal (leads, sales, calls, revenue, awareness), time frame, and total budget
- Allowable CPA or CPL and target ROAS (from the allowable CPA calculator)
- Audience, services or products, geography, seasonality, constraints, competitors
- Demand data: keyword volume and cost estimates, current account performance if any
- `clients/<slug>/context.md`: brand, restrictions matrix, past results

## Process
1. **Restate the objective** as measurable: outcome, number, date, and the economic limit.
2. **Size the opportunity:** search demand and cost-per-click ranges for the core themes; check whether the budget can reach the volume needed for target-based bidding (about 30 conversions per month per campaign). Compute implied clicks, conversions, and CPA at assumed conversion rates in code, as a low, base, and high range.
3. **Select channels** using demand and intent: search for existing demand, then local services or maps where relevant, then paid social for demand creation and remarketing, then display or video only if the funnel is mature. Give a reason for every channel and for every channel left out.
4. **Split the budget** with rationale, as a table by channel, campaign type, and month, plus a testing reserve (typically 10 to 15%) and a contingency for budget shifts. Show the split under a conservative and a stretch scenario.
5. **Structure the funnel:** prospecting, consideration, conversion, remarketing; what each campaign type is for and the primary metric for each.
6. **Targeting plan:** geos, audiences, exclusions, devices, and schedule, aligned with the restrictions matrix.
7. **Measurement plan:** conversion definitions, tracking requirements, attribution approach, the reporting cadence, and the KPI tree from spend to profit.
8. **Testing roadmap:** the first three tests in priority order with hypotheses.
9. **Timeline:** build, launch gates, learning-phase expectations, first optimization date, and review points. Include ramp-up: the first month is learning.
10. **Risks and dependencies:** tracking readiness, creative availability, approvals, seasonality, budget sufficiency. Include what would make the plan change.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/media-plan.md` and a budget workbook `media-plan.xlsx` (budget by channel and month, volume and cost scenarios with formulas).
```
Bottom line (3 sentences): the recommended mix, the expected outcome range, and the main risk.
Objective and economics.
Channel and budget table with rationale.
Expected results: low, base, high, with assumptions.
Structure, targeting, measurement, testing.
Timeline and launch gates.
Risks, dependencies, decisions needed from the client.
```

## Rules
- Expected results are ranges built from stated assumptions, never promises.
- Do not set budgets or create campaigns in any account.
- When data is missing, state the assumption and what would replace it.
- Align every number with the allowable CPA; if the plan cannot meet it at the budget, say so plainly and show the options.
