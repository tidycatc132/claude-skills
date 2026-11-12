---
name: ppc-keyword-research
description: Research keywords for paid search (Google Ads, Microsoft Ads) using SE Ranking volume, CPC, difficulty, related and question data, grouped by buyer intent tier, scored by commercial value against the client's economics, localized to the service area, and paired with a starter negative keyword list and recommended match types. Use whenever the user asks for PPC keyword research, a keyword list for a new campaign, keyword expansion, search demand sizing, estimated clicks or cost for a budget, which keywords to bid on, or keywords for a local service business, even if they only say find keywords for ads. For organic SEO keyword clustering use seo-keyword-cluster instead.
---

# PPC Keyword Research

Paid keywords are bought one click at a time, so the question differs from SEO: not "what can we rank for" but "which queries produce customers at a cost we can afford." This skill finds those queries and estimates what they cost.

## Principle: intent and economics beat volume
High-volume terms are often research queries that burn budget. A 40-search-per-month term like "emergency water heater repair near me" can outperform a 5,000-search informational term. Rank candidates by how close the searcher is to buying and by whether the CPC fits the client's allowable CPA.

## Inputs
- Client context file: services ranked by profit, geo, target CPA, restrictions, monthly budget
- Seed terms from the user. If none, derive them from the site's service pages and the client's current search term report.
- Existing account keywords and search terms, if available, to avoid duplicating and to learn what converts

## Process
1. **Seed.** Collect 5 to 20 seeds covering each service line and its modifiers (emergency, near me, cost, installation, repair, replacement, best, brand names).
2. **Expand.** Use the SE Ranking tools for related keywords, similar keywords, long-tail variations, and question keywords. Pull volume, CPC, and competition for the target country and, where supported, the target region. Add city and neighborhood variants for local businesses.
3. **Check competitors.** Pull the keywords competitors advertise on (domain ads by domain and by keyword) to find terms the client is missing.
4. **Classify by intent tier:**
   - Tier 1, ready to buy: service plus location or urgency, "near me," hire, quote, emergency, same day, brand plus service
   - Tier 2, comparing: best, top, reviews, cost, vs
   - Tier 3, researching: how to, what is, DIY, symptoms (usually exclude or isolate for low budgets)
   - Branded and competitor terms, separated because they behave differently
5. **Score each keyword** in code. Compute estimated monthly clicks at a realistic share of impressions, estimated cost from CPC, and a break-even check: `max_viable_CPC = target_CPA * expected_conversion_rate`. Use the client's historical conversion rate; if none exists, use a conservative stated assumption and label it. Flag keywords whose CPC exceeds the viable maximum.
6. **Group** into tight themes of closely related terms, because ad copy and landing pages must match each group. Suggest one landing page per group.
7. **Recommend match types.** Default to phrase and exact for Tier 1 and for accounts with limited conversion data; use broad only with smart bidding and strong conversion volume, and say why.
8. **Seed negatives.** Produce a starter list from known low-intent patterns: free, jobs, careers, salary, DIY, training, course, template, plus service-specific irrelevancies, with a reason for each category.
9. **Size the opportunity.** Show estimated clicks, spend, and leads per tier against the monthly budget, and say honestly if the budget cannot cover Tier 1 demand.

## Output
Save a workbook to `clients/<slug>/outputs/YYYY-MM/keyword-research.xlsx` with sheets: Keywords (term, intent tier, volume, CPC, viable CPC check, group, match type, landing page), Groups, Negatives, Budget sizing, and Assumptions. Return a short summary:
```
Bottom line (2 sentences): where the best paid opportunity is and what the budget can cover.
Top 10 recommended keywords with reasoning.
Warnings: terms priced above break-even, markets too small to test, restricted terms.
Assumptions and data gaps.
```

## Rules
- Volume and CPC from SE Ranking are estimates; label them as such and never present forecasted clicks or leads as promises.
- Respect industry restrictions in the context file. Flag terms that touch regulated or policy-restricted categories for compliance review.
- Compute all scoring and sizing in code and show the formulas on the Assumptions sheet.
- Read-only research. Do not build or edit campaigns; hand the keyword groups to the campaign build step.
