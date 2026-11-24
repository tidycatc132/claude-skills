---
name: allowable-cpa-calculator
description: Calculate the allowable cost per lead, cost per acquisition, and target ROAS for a client from average order or case value, margin, close rate, lead-to-customer funnel rates, repeat purchase or lifetime value, and desired profit, with a break-even and target CPA range, sensitivity table, and the assumptions flagged for client confirmation, computed in code. Use whenever the user asks what CPA or CPL a client can afford, what target ROAS to set, whether a campaign is profitable, how to set bid targets, or needs unit economics before building a media plan, even if they only say what should our target be.
---

# Allowable CPA Calculator

A bid target with no economics behind it is a guess. Allowable CPA is the most the business can pay to acquire a customer and still meet its profit goal. Everything downstream (bid targets, budgets, forecasts, what counts as a bad keyword) depends on this number.

## Principle: work backward from the business, and show every assumption
Start from what a customer is worth and what the client needs to keep, then step back through the funnel to the lead and click. Every input is either confirmed by the client or marked as an assumption with its source.

## Inputs
- Average revenue per sale or case; gross margin or contribution margin
- Funnel rates: lead to qualified, qualified to appointment, appointment to sale (or close rate)
- Repeat purchases or lifetime value and the time horizon the client accepts
- Desired profit margin or maximum acceptable cost of acquisition as a share of revenue
- Existing data: CRM close rates, average ticket, past cost per lead
- `clients/<slug>/context.md` for known figures

## Process
1. **Collect and label inputs** as confirmed, estimated from data, or assumed. Ask for missing confirmable inputs; otherwise use a clearly labeled assumption.
2. **Compute in code:**
   - Gross profit per customer = value per customer x margin (use contribution margin when variable costs are known)
   - Break-even CPA = gross profit per customer (first-order or lifetime, as agreed)
   - Target CPA = break-even x (1 - required profit share)
   - Allowable CPL = target CPA x lead-to-customer rate
   - Target ROAS = revenue per customer / target CPA (for ecommerce, value divided by cost with margin applied)
3. **Show first-order and lifetime views** separately; state which one bids should use and why (cash constraints and payback period).
4. **Sensitivity table:** vary close rate, ticket size, and margin by plus or minus 20% to show how the allowable CPL moves and which input matters most.
5. **Compare with reality:** current cost per lead and per customer from the account and CRM; state whether the account is under or over the target and by how much.
6. **Translate into platform settings:** a starting tCPA or tROAS, the conversion volume check from the bid strategy rules, and the segments (service lines, geos) that should have different targets.
7. **Note risks:** lead quality drift, seasonality, measurement gaps, long sales cycles.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/allowable-cpa.xlsx` with live formulas in an inputs tab, a calculation tab, and a sensitivity tab; and update the targets block in `clients/<slug>/context.md` after the user confirms.
```
Bottom line (2 sentences): the allowable CPL and CPA, and how current performance compares.
Inputs table with status (confirmed, estimated, assumed).
Calculation walk-through.
Sensitivity highlights.
Recommended targets by campaign type, and what must be confirmed.
```

## Rules
- Never present an assumed rate as a client fact.
- Do not set targets in the platform; recommend, and get approval.
- Flag when the lead-to-sale rate comes from fewer than about 30 outcomes; it is too noisy to lean on.
- Revisit when ticket size, margin, or close rate changes.
