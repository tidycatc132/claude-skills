---
name: google-ads-account-audit
description: Run a structured audit of a Google Ads account covering conversion tracking, account and campaign structure, settings and targeting, bidding, budgets and impression share, keywords and match types, negatives and search terms, ad and asset quality, extensions, Performance Max and Demand Gen, audiences, geo and schedule, and change history, producing a scored scorecard, quantified wasted spend and missed opportunity, and a ranked fix list with owners. Use whenever the user asks to audit a Google Ads account, review an inherited account, do a health check on PPC, figure out what is wrong with a Google Ads account, or prepare a PPC audit for a prospect, even if they do not say Google Ads by name and mention only the paid search account.
---

# Google Ads Account Audit

An audit should end with a short list of changes ordered by money, not a wall of observations. Most accounts have dozens of imperfections and three or four problems that matter. This skill finds those few and proves them with data.

## Principle: tracking first, money second, polish last
Tracking errors invalidate every other finding, so check them first. Then rank issues by dollars at stake. Settings trivia only appears if it affects results.

## Inputs
- Read access to the account (API, connector, or exports): campaigns, ad groups, keywords, search terms, ads, assets, audiences, settings, change history, 90 days of performance (and 12 months for trend and seasonality when available)
- `clients/<slug>/context.md` for goals, targets, budget, geo, restrictions. For a prospect with no context file, record assumptions explicitly.

## Audit areas (work through in order)
1. **Conversion tracking.** Actions, primary vs secondary, counting, attribution, value, enhanced conversions, duplicates, and whether the numbers match GA4 and CRM within tolerance. If broken, flag at the top and label downstream conversion-based findings provisional. Hand deeper verification to the conversion tracking audit.
2. **Structure and segmentation.** Does structure follow intent and business priority? Brand vs non-brand split, service or product themes, geo structure, fragmentation that starves campaigns of data, and campaigns doing several jobs.
3. **Settings.** Network settings (search partners, display expansion), location targeting option (presence vs presence or interest), languages, devices, ad schedule, delivery method, and campaign experiments.
4. **Bidding and budgets.** Strategy vs conversion volume (flag tCPA or tROAS with under about 30 conversions per 30 days), target realism against history, learning status, budget-limited campaigns, and lost impression share to budget versus rank. Note frequency of strategy and target changes.
5. **Keywords and match types.** Match type mix, quality score distribution and drivers, keywords with spend and no results, missing high-intent terms, overlap and cannibalization between campaigns.
6. **Search terms and negatives.** Share of spend on irrelevant or low-intent queries, negative list coverage, brand leakage. Quantify wasted spend with the sample-size rule used in search term mining.
7. **Ads and assets.** RSA ad strength drivers, asset coverage and pinning, message match to keywords and pages, extensions or assets (sitelinks, callouts, structured snippets, calls, location, lead forms, images), and policy status.
8. **Performance Max and Demand Gen.** Asset group quality, audience signals, search themes, brand exclusions, URL expansion, final URL rules, and overlap with branded search. State what the interface does not let you see.
9. **Audiences and remarketing.** List sizes, usage, observation vs targeting, customer match freshness.
10. **Landing pages.** Spot-check the top pages for message match, speed, and form and call flow (detail goes to the landing page analysis).
11. **Change history and hygiene.** Frequent disruptive changes, naming, recent edits that coincide with performance shifts, stale experiments.

## Scoring
Score each area 0 to 5 with one sentence of evidence. Weight tracking, bidding, structure, and search terms highest. Report the overall score only alongside the area scores, since a single number hides what to fix.

## Quantifying impact
For the top findings, compute in code: wasted spend (cost with zero conversions beyond the sample-size threshold, plus irrelevant queries), recoverable budget, and opportunity (budget-limited campaigns beating target CPA, rank-lost impression share on efficient campaigns). Show ranges, not false precision, and state the date range used.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/google-ads-audit.md` with a supporting `.xlsx` of data tables.
```
Bottom line (3 sentences): account health and the biggest money issue.
Scorecard: area, score, evidence.
Top findings (max 10): evidence, dollar impact range, fix, owner (specialist), effort, [NEEDS APPROVAL] where live changes.
Quick wins (done this week) vs structural fixes (done this quarter).
What could not be audited and why.
```

## Rules
- Read-only. Do not change the account.
- Do not recommend rebuilding an account that works; recommend the smallest change that fixes the problem.
- For prospect audits, keep internal findings separate from anything client-facing, and do not present unverified numbers as fact.
- Cite the date range and source for every figure; compute in code.
