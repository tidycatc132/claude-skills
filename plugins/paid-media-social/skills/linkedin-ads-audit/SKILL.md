---
name: linkedin-ads-audit
description: Audit a LinkedIn Ads account covering Insight Tag and Conversions API setup, objectives and conversion definitions, audience targeting and size, matched audiences and account lists, ad formats and creative performance, lead gen form setup and lead quality, bidding and budget efficiency, frequency and audience fatigue, delivery by placement, company and job-level reporting, and fit with the B2B sales cycle, producing a scored review with a ranked fix list. Use whenever the user asks to audit or review a LinkedIn ads account, asks why LinkedIn is expensive or leads are poor, wants a B2B paid social health check, or inherits a LinkedIn account, even if they just say look at our LinkedIn campaigns.
---

# LinkedIn Ads Audit

LinkedIn costs several times more per click than other platforms because it sells professional targeting. The account therefore needs to earn that premium: tight audiences of the right size, offers matched to the buying stage, and lead quality measured past the form fill. The common failures are audiences too broad or too small, offers that ask for a sales call too early, and lead gen forms producing contacts who never answer.

## Principle: measure to pipeline, not to cost per lead
Cost per lead on LinkedIn looks bad against other channels and may still be the best source of pipeline. Judge by qualified leads, opportunities, and revenue where the CRM allows. Where it does not, say the comparison is incomplete.

## Inputs
- Read access (API, connector, or exports): campaigns, ad groups, ads, audiences, demographic reports (job function, seniority, industry, company size, company name), lead gen form data, conversion setup, 90 days of results
- CRM data for lead stages and outcomes, if available
- `clients/<slug>/context.md`: ICP, goals, target cost per qualified lead or opportunity, sales cycle, restrictions

## Audit areas
1. **Tracking and conversions.** Insight Tag installed and firing on key pages, conversion definitions (URL-based, event-based), Conversions API for server events, lead gen form conversions, offline conversion upload from CRM, attribution window, duplicate counting. Hand deeper verification to the conversion tracking audit.
2. **ICP and targeting.** Does targeting match the ideal customer profile? Review job titles and functions, seniority, industries, company size, skills and groups, and account lists (matched audiences from target account lists). Check audience size per campaign against a workable range (commonly 50,000 or more for most campaigns, smaller for account-based efforts) and whether Audience Expansion is on or off deliberately. Flag overly narrow or stacked criteria, and unintended mixed-intent combos.
3. **Demographic reports.** Compare who actually engaged and converted (job function, seniority, industry, company size) to the ICP. Quantify spend on off-ICP segments.
4. **Objectives and funnel fit.** Awareness, consideration, and conversion objectives matched to audience stage; retargeting windows and website audiences; content offers fitting the sales cycle (guides and webinars for cold audiences, demos and consultations for warm).
5. **Formats and creative.** Mix of single image, document, video, thought leader ads, conversation ads; CTR and conversion rate by format; message angles; fatigue indicated by frequency over time and CTR decay; number of ads per campaign.
6. **Lead gen forms.** Form fields (job title, company, work email prefilled by LinkedIn), qualifying questions, friction versus quality, privacy policy and consent text, thank-you message, routing to CRM and speed of follow-up. Defer detailed quality analysis to the lead form audit.
7. **Bidding and budget.** Bid strategy (maximum delivery, cost cap, manual), budget relative to audience size and cost per click so delivery is not starved, daily versus lifetime budgets, spend concentration, and pacing.
8. **Efficiency.** Cost per click, cost per lead, lead-to-qualified rate, cost per qualified lead, and opportunity or revenue metrics from CRM, by campaign and audience. Compare to targets and to benchmarks labeled as benchmarks.
9. **Hygiene.** Naming, UTMs, company page, brand safety lists, placement settings (LinkedIn Audience Network on or off), and policy status.

## Scoring and impact
Score each area 0 to 5 with evidence. Quantify, in code, spend on off-ICP audiences, spend in campaigns with audience-size problems, and cost per qualified lead by segment. State date range and sample size, and be cautious: B2B volumes are small, so label findings with low sample sizes as directional.

## Output
Save to `clients/<slug>/outputs/YYYY-MM/linkedin-audit.md` with an `.xlsx` of tables.
```
Bottom line (3 sentences): account health, the largest issue, and what it costs.
Scorecard: area, score, evidence.
Top findings (max 8): evidence, impact range, fix, owner, effort, [NEEDS APPROVAL] for live changes.
ICP match table: ICP vs actual engaged and converted.
Quick wins vs structural changes.
Not audited and why.
```

## Rules
- Read-only; recommend, do not edit.
- Do not conclude on tiny samples; label as directional.
- Do not recommend broadening targeting by reflex when the account is already off-ICP; fix relevance before volume.
- Cite sources and date ranges; compute in code.
