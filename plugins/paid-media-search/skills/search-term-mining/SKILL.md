---
name: search-term-mining
description: Analyze Google Ads or Microsoft Ads search term reports to find wasted spend, irrelevant or wrong-intent queries, wrong-geo traffic, and converting queries missing from the keyword list, then produce layered negative keywords and keyword additions as an import-ready change sheet with rationale. Use whenever the user asks for a search term review, search query report analysis, negative keywords, why a campaign is getting junk traffic, cleaning up a search account, finding wasted spend in search, or new keyword ideas from existing data, even if they only say look at the search terms.
---

# Search Term Mining

The search term report is where the account shows what it is actually buying. Every week of neglect lets junk queries compound and teaches smart bidding the wrong patterns. This skill reviews it systematically and converts findings into clean, import-ready changes.

## Principle: decide on evidence, not on how a term looks
A term that looks irrelevant but converts is a signal, not a negative. A term that looks relevant but burns spend with no outcomes after enough clicks is waste. Make each decision from outcome data and sample size, and keep a human in the loop for anything borderline.

## Inputs
- Search term report, 30 to 90 days (CSV export or connector pull), with query, campaign, ad group, matched keyword and match type, impressions, clicks, cost, conversions, conversion value
- Current keyword and negative keyword lists
- `clients/<slug>/context.md` for services, geo, target CPA, qualified lead definition, restrictions
- Conversion tracking status. If tracking is unverified, mark all conversion-based decisions as provisional.

## Process
1. **Compute baselines in code:** account and campaign average CPC, CVR, and CPA, and the break-even click count: `clicks_needed = 1 / expected_CVR`. A term needs roughly `2 to 3 times` that many clicks with zero conversions before it is statistically fair to call it waste. Record the thresholds used.
2. **Classify every query with meaningful spend** (and a sample of low-spend ones) into:
   - **Converting and in the account:** leave, maybe raise priority
   - **Converting and not yet a keyword:** add as exact or phrase
   - **Relevant, not enough data:** leave and monitor
   - **Relevant, enough clicks, no conversions:** investigate landing page and intent before negating
   - **Irrelevant or wrong intent:** negative candidate (jobs, free, DIY, training, wrong service, competitor misspellings, informational)
   - **Wrong geo:** location negative or geo-setting fix
   - **Brand leakage:** terms that should be isolated into a brand campaign
3. **Choose the right negative scope and match type:**
   - Account-level lists for universal junk (careers, free, jobs)
   - Campaign or ad-group level to steer queries to the right group
   - Exact negatives for single bad queries, phrase for bad patterns
   - Avoid broad negatives that could block good traffic; test any single-word negative against the converting-query list and drop it if it would block a converter
4. **Cross-check for collisions.** Run every proposed negative against the converting queries and active keywords. Remove or narrow any that collide, and note the check was done.
5. **Quantify impact.** Estimated wasted spend recoverable (sum of cost on negative candidates) and the uncertainty around it.
6. **Find expansion keywords** from converting queries, with the suggested match type and ad group.
7. **Build the change sheet.**

## Output
Save to `clients/<slug>/outputs/YYYY-MM/search-term-changes.xlsx`:
- **Negatives:** level, campaign or list, keyword, match type, reason category, evidence (cost, clicks, conversions)
- **Additions:** campaign, ad group, keyword, match type, evidence
- **Investigate:** relevant terms with spend and no conversions, with the suspected cause
- **Summary:** wasted spend identified, thresholds used, collision check result

Return:
```
Bottom line (2 sentences): how much waste was found and how clean the account is.
Top findings with numbers.
Recommended changes [NEEDS APPROVAL] with the path to the sheet.
Assumptions and data gaps (date range, tracking caveats).
```

## Rules
- Never apply negatives or keyword changes to a live account. Produce the sheet; a human imports it.
- Do not negate on sample sizes too small to support it. Label as monitor instead.
- Watch for conversion value and call conversions: a query with calls but no form fills may still be valuable.
- Respect restricted terms for regulated industries; route flagged queries for compliance review.
- Note when a pattern points to a structural fix (for example, broad match leaking, or PMax search themes) so the lead can send it to the right specialist.
