---
name: wasted-spend-finder
description: Quantify wasted paid media spend across Google Ads, Microsoft Ads, Meta, and LinkedIn by finding spend on irrelevant or low-intent queries, zero-conversion keywords, campaigns, ad sets, and ads after enough data, wrong-geo and low-value segments, duplicate or overlapping targeting, fatigued creative, and spend on bad placements, using explicit sample-size rules and reporting recoverable dollars as a range. Use whenever the user asks where money is being wasted, how much spend is unproductive, for a savings estimate or waste figure for an audit, to justify an optimization project, or to find the leaks in an account, even if they only say what is burning budget.
---

# Wasted Spend Finder

The waste number is a persuasive figure in audits and a risky one if computed carelessly. Calling spend wasteful because it has not converted yet, over too short a window, destroys credibility. This skill defines waste with statistical honesty, so the figure survives scrutiny and the recommended cuts do not hurt good traffic.

## Principle: waste is spend with no reasonable path to return, proven with enough data
Separate three categories and never merge them into one scary total: **confirmed waste** (enough data, no return), **probable waste** (relevant-looking but underperforming; needs a fix, not a cut), and **unproven** (not enough data yet; monitor). Present recoverable dollars as a range.

## Inputs
- Performance data by campaign, ad group or ad set, keyword, search term, ad, placement, geo, device, daypart, and audience for 90 days (30 days for fast accounts), including cost, clicks, conversions, conversion value
- Baselines: account CVR, CPA, and click-to-lead rate; target CPA from `clients/<slug>/context.md`
- Tracking trust status. If conversions are suspect, mark every conversion-based number provisional and show the non-conversion waste (irrelevant queries, wrong geo) separately.

## Sample-size rule
A segment with expected conversion rate `p` needs about `3 / p` clicks (three expected conversions' worth) with zero conversions before zero is meaningful at moderate confidence; use `5 / p` for high confidence. Example: at a 5 percent conversion rate, about 60 clicks. Compute the threshold per segment in code and state the one used. Segments below it go to Unproven.

## Process
1. **Compute baselines and thresholds** in code.
2. **Search waste:** search terms and keywords with zero conversions past the threshold; clearly irrelevant intent (jobs, free, DIY, wrong service or product) regardless of volume; wrong-geo queries; brand terms leaking into non-brand campaigns where that distorts results.
3. **Structural waste:** duplicate keywords across campaigns bidding against each other, display or search partner network spend with no return, overlapping social audiences, campaigns above target CPA by a large margin with sufficient data.
4. **Creative waste (social):** ads past the fatigue thresholds, with CPA above target and sufficient data.
5. **Delivery waste:** poor placements, device or daypart segments with materially worse results after the threshold, and budget stranded in low-return campaigns while efficient campaigns are budget-limited (opportunity cost, reported separately).
6. **Overlap check.** Do not double count: the same dollars can appear in several cuts (a bad query inside a bad campaign). Deduplicate to a single total.
7. **Estimate recovery.** Not all wasted spend is recoverable as savings: some is reallocated into other traffic at average performance. Report both gross waste and a conservative net recoverable range, and explain the assumption.
8. **Check the cuts for collisions** against converting queries, assisted conversions, and calls before recommending negatives or pauses.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/wasted-spend.md` with an `.xlsx` of itemized segments.
```
Bottom line (2 sentences): total confirmed waste as a dollar range and percent of spend, with the main sources.
Table: category, segment, spend, clicks, conversions, threshold used, confidence (confirmed / probable / unproven).
Recoverable range and method.
Opportunity cost (budget-limited efficient campaigns), reported separately.
Ranked recovery actions with owners, [NEEDS APPROVAL] where live changes.
Data caveats.
```

## Rules
- Never present unproven spend as waste.
- State the date range, thresholds, and tracking caveats beside the headline number.
- Compute all figures in code and deduplicate overlaps.
- Read-only; recommend changes, do not apply them.
