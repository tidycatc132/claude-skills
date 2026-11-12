---
name: pmax-audit
description: Audit Google Performance Max (and similar AI-driven campaign types) for asset group quality, audience signals, search themes, brand exclusions and brand cannibalization, URL expansion and final URL rules, channel and placement mix, conversion goal setup, lead quality, budget and bidding fit, and what the reporting does and does not reveal, producing a scored review and ranked fixes. Use whenever the user asks to audit, review, or troubleshoot Performance Max or PMax, asks whether PMax is cannibalizing brand search, why PMax leads are low quality, whether PMax is worth running, or how to structure asset groups, even if they only say the automated campaign is not working.
---

# PMax Audit

Performance Max hands most decisions to the platform, which makes the inputs you control matter more: conversion goals, assets, signals, exclusions, and budget. The campaign type also hides a lot, so this audit pairs the visible data with careful skepticism about what cannot be seen.

## Principle: judge by business outcome, not by the platform's own reporting
PMax will happily report strong conversions that are cheap branded searches, junk form fills, or remarketing to people already on the way to buying. Check where the conversions come from and what they are worth before praising or blaming the campaign.

## Inputs
- Read access (API, connector, or exports): campaign and asset group settings, asset performance labels, insights (search themes and categories), listing group or feed data for retail, channel breakdowns, geographic data, conversion actions, 90 days of results
- Branded search campaigns and their performance for the same period
- CRM or call data to judge lead quality
- `clients/<slug>/context.md`: goals, targets, budget, brand terms, restrictions

## Audit areas
1. **Conversion goals and value.** Which actions does the campaign optimize? Are junk, duplicate, or low-value actions primary? Is value set correctly? Is there a customer acquisition or new-customer setting appropriate to the goal? If signal is bad, label findings provisional and run the tracking audit.
2. **Brand cannibalization.** Compare PMax versus brand search: search category insights, brand terms in PMax queries, brand search impression share and CPC before and after PMax launched. Check whether brand exclusions are set. Quantify spend and conversions plausibly attributable to brand queries, with a range.
3. **Asset groups.** One asset group per theme (service, product category, intent or audience) rather than one for everything. Check asset counts and variety (text, images across ratios, video, logos), asset performance labels, relevance to the landing page, and whether the auto-generated video is replacing a real one.
4. **Signals and search themes.** Audience signals reflect actual customers and high-intent segments; custom segments and customer lists present and fresh; search themes cover the real services and locations. Remember signals guide rather than restrict.
5. **URL and final URL expansion.** Is expansion on or off, and is it appropriate? Check URL exclusions, page feeds, and whether traffic lands on irrelevant pages (blog, careers, contact) that convert poorly.
6. **Geo, schedule, and exclusions.** Location option, location exclusions, account-level negative keywords (now supported), brand exclusions, placement exclusions, and customer-list exclusions to avoid paying for existing customers.
7. **Channel mix.** Where available, review spend by channel (search, shopping, display, video, discover, maps) and whether a surprising share goes to low-intent inventory.
8. **Lead quality.** For lead generation, compare PMax leads against CRM outcomes and other campaigns: qualified rate, spam rate, call duration, and close rate. Recommend offline conversion feedback when quality is weak.
9. **Budget and bidding.** Volume versus bidding strategy, learning status, target realism, budget constraints, and any recent resets caused by edits.
10. **Experiments.** Where an experiment or holdout is feasible, recommend one to measure incrementality rather than relying on attribution.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/pmax-audit.md` with supporting tables in `.xlsx`.
```
Bottom line (3 sentences): whether PMax is earning its budget and the main issue.
Scorecard: area, score 0-5, evidence.
Brand cannibalization estimate with range and method.
Top findings (max 8): evidence, impact, fix, owner, [NEEDS APPROVAL] for live changes.
What cannot be seen in PMax reporting and how that limits confidence.
Test recommendations (experiment or holdout).
```

## Rules
- Read-only. Recommend; do not edit.
- State limits of PMax reporting openly; do not claim precision the data cannot give.
- Do not recommend turning PMax off based on attribution alone when quality data is missing; recommend the measurement that would settle it.
- Platform features change often; verify current availability of exclusions and reporting before recommending them.
