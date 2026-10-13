---
name: google-ads-audit
description: Structured Google Ads account audit across 7 dimensions (account structure, conversion tracking, keyword strategy, ad creative, bidding and budget, targeting, wasted spend). Use when the user asks to "audit my account", "audit my Google Ads", "check for problems", "find issues", "review my campaigns", "account health check", or requests a comprehensive account health assessment or a PPC account review before taking over or restructuring an account. Pulls data through a connected Google Ads connector (GAQL) or from report exports, rates every finding Critical / High / Medium / Low, scores the account out of 10, estimates monthly wasted spend, and ends with prioritized fixes, top quick wins, and a 30/60/90-day plan. It is read-only and never changes the account.
---

<!-- Adapted from itallstartedwithaidea/google-ads-skills skills/google-ads-audit. -->

# Google Ads Audit

You are a Google Ads auditor conducting a structured account review. When asked to audit an account, systematically check all 7 dimensions below and report findings with severity ratings.

**Read-only**: this skill never changes the account. Even if the connected Google Ads tools can write, every fix goes into the report as a recommendation for the user to make.

## Getting the data

Use the first route that is available and say which one you used:

1. **Google Ads connector**: if a connected tool can run GAQL or has named report tools, confirm the customer ID (ask which account if several are accessible), then run the queries in [audit-queries.md](references/audit-queries.md). Default window: `LAST_30_DAYS`; use the previous 30 days for comparisons.
2. **Report exports**: if no connector is available, send the user the list in [export-checklist.md](references/export-checklist.md) and audit what they provide.
3. **Partial data**: audit what you have. A dimension with no data is reported as **Not assessed** with the export that would fill it. Never guess a finding.

API money fields are micros (÷ 1,000,000); export money is already in currency units. Format currency with 2 decimal places in the account currency (`$` for USD).

## Audit Dimensions

### 1. Account Structure

- Campaign naming conventions (consistent? descriptive?)
- Ad group theme tightness (single keyword ad groups vs broad themes)
- Campaign type coverage (Search, Display, PMax, Shopping, Video)
- Budget allocation vs performance alignment
- Number of paused vs enabled entities

### 2. Conversion Tracking

- Are conversions being tracked? (check `conversion_action` data)
- Conversion action types (Webpage, Phone Call, Import, etc.)
- Attribution model in use (last-click, data-driven, etc.)
- Conversion counting (one vs many)
- Value tracking enabled?

### 3. Keyword Strategy

- Match type distribution (Broad, Phrase, Exact)
- Quality Score distribution (% below 5, % above 7)
- Negative keyword coverage (campaign-level, shared lists)
- Search term relevance (high-spend zero-conversion terms)
- Keyword-to-ad-group ratio

### 4. Ad Creative

- RSA ad strength scores (Poor, Average, Good, Excellent)
- Headlines and descriptions per ad (min 3 headlines, 2 descriptions)
- Ad testing velocity (how recently were ads updated?)
- Ad extensions/assets (sitelinks, callouts, structured snippets, calls)
- Landing page diversity

### 5. Bidding & Budget

- Bidding strategy per campaign (Manual CPC, tCPA, tROAS, Max Conversions)
- Budget utilization (capped campaigns losing impression share)
- Budget-to-performance ratio (high budget + low ROAS campaigns)
- Shared budgets analysis
- Bid adjustment coverage (device, location, schedule)

### 6. Targeting

- Geographic targeting scope and performance
- Device performance variance (mobile vs desktop CPA)
- Ad schedule coverage and performance by hour/day
- Audience targeting (remarketing lists, customer match, in-market)
- Placement exclusions (for Display/Video)

### 7. Wasted Spend

- Search terms with spend but zero conversions
- Total wasted spend as % of total spend
- Low-QS keywords consuming budget
- Underperforming geographic regions
- Display placement waste

The query for each check, and how to compute it, is in [audit-queries.md](references/audit-queries.md).

## Severity Framework

| Severity | Definition | Examples |
|---|---|---|
| **Critical** | Immediate revenue impact or tracking failure | No conversion tracking, zero conversions with high spend |
| **High** | Significant efficiency loss | > 20% wasted spend, budget-capped top performers, QS < 3 |
| **Medium** | Optimization opportunity | Missing ad extensions, suboptimal bidding strategy, QS 4-5 |
| **Low** | Best practice recommendation | Naming conventions, testing cadence, minor structural improvements |

Default severities for every check, the numeric thresholds, the wasted-spend calculation, and the scoring rule for the Overall Score are in [severity-and-scoring.md](references/severity-and-scoring.md). Read it before rating any finding.

## Output Format

```
## Account Audit: [Account Name]

### Overall Score: X/10

### Critical Issues (fix immediately)
1. [Issue] — [Impact] — [Fix]

### High Priority (fix this week)
1. [Issue] — [Impact] — [Fix]

### Medium Priority (optimize this month)
1. [Issue] — [Impact] — [Fix]

### Low Priority (best practices)
1. [Issue] — [Impact] — [Fix]

### Summary
- Total issues: X
- Estimated wasted spend: $X/month
- Top 3 quick wins: ...
```

Under the Overall Score, add one line with the account ID, date window, data source (connector or exports), and currency, then a small table of the 7 dimension scores (or "Not assessed"). Every [Impact] names a number where one exists (spend, conversions, share), and every [Fix] names the entity and the change.

## 30/60/90-Day Strategy

After the audit, offer a phased action plan:

- **30 days**: Fix critical and high-priority issues
- **60 days**: Implement medium-priority optimizations, A/B test new strategies
- **90 days**: Review results, adjust targets, expand winning strategies
