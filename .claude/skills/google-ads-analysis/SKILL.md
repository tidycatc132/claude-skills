---
name: google-ads-analysis
description: Google Ads campaign performance analysis using GAQL (Google Ads Query Language) or Google Ads report exports. Use when the user asks about campaign performance, ad spend, ROAS, CPA, CTR, CPC, conversions, keyword metrics, Quality Score, search terms, wasted spend, device breakdown, geographic performance, impression share, budget pacing, or period-over-period changes, or asks any other Google Ads reporting question ("how are my campaigns doing", "why did CPA go up", "where am I wasting spend"). Delivers structured tables with summary metrics, entity breakdowns, automatic anomaly flags with severity, and specific prioritized recommendations. It is read-only and never changes the account.
---

<!-- Adapted from itallstartedwithaidea/google-ads-skills skills/google-ads-analysis, with formulas from skills/google-ads-math. -->

# Google Ads Analysis

You are a senior Google Ads analyst. When the user asks about campaign performance, ad metrics, or account data, follow these patterns to deliver structured, actionable analysis.

**Read-only**: this skill never changes the account. Even if the connected Google Ads tools can write (pause, bid, budget, negatives), list those changes as recommendations and let the user make them.

## Getting the data

Use the first route that is available and say which one you used:

1. **Google Ads connector**: if a connected tool can run GAQL (for example a tool named like `execute_gaql`, `search`, or `run_query`) or has named report tools (campaign performance, keyword performance, search terms, impression share, device, geo), use it. Confirm the customer ID first; if several accounts are accessible, ask which one. Run the queries in this file and in [gaql-queries.md](references/gaql-queries.md).
2. **Report exports**: if no connector is available, ask the user for CSV exports from the Google Ads interface. [ui-export-guide.md](references/ui-export-guide.md) lists which report and columns map to each query below.
3. **Numbers in chat**: if the user only pastes figures, compute with [ppc-formulas.md](references/ppc-formulas.md) and say which questions the data cannot answer.

Never estimate account metrics that were not provided. Mark them N/A and say what export would fill the gap.

Default window: `LAST_30_DAYS` (which excludes today). For trend or "why did it change" questions, also pull the previous period of equal length and compare.

## GAQL Query Patterns

Use these templates when querying the Google Ads API. All monetary values are in micros (divide by 1,000,000 for currency units).

### Campaign Performance

```sql
SELECT
  campaign.id, campaign.name, campaign.status,
  campaign.advertising_channel_type, campaign.bidding_strategy_type,
  campaign_budget.amount_micros,
  metrics.cost_micros, metrics.clicks, metrics.impressions,
  metrics.conversions, metrics.conversions_value,
  metrics.ctr, metrics.average_cpc, metrics.cost_per_conversion
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

### Search Terms (Wasted Spend Detection)

```sql
SELECT
  search_term_view.search_term, search_term_view.status,
  campaign.name, ad_group.name,
  metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS
  AND metrics.conversions = 0
ORDER BY metrics.cost_micros DESC
LIMIT 100
```

### Keyword Quality Scores

```sql
SELECT
  ad_group_criterion.keyword.text,
  ad_group_criterion.keyword.match_type,
  ad_group_criterion.quality_info.quality_score,
  ad_group_criterion.quality_info.creative_quality_score,
  ad_group_criterion.quality_info.post_click_quality_score,
  ad_group_criterion.quality_info.search_predicted_ctr,
  campaign.name, ad_group.name,
  metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions
FROM keyword_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

### Device Performance

```sql
SELECT
  segments.device,
  metrics.cost_micros, metrics.clicks, metrics.impressions,
  metrics.conversions, metrics.conversions_value
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

### Impression Share

```sql
SELECT
  campaign.name,
  metrics.search_impression_share,
  metrics.search_budget_lost_impression_share,
  metrics.search_rank_lost_impression_share
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

### Period-over-Period Comparison

Use `BETWEEN 'YYYY-MM-DD' AND 'YYYY-MM-DD'` to compare two date ranges. Calculate deltas as `(period_a - period_b) / period_b * 100` for percentage change, where `period_a` is the current period and `period_b` the previous one.

More templates (account currency and time zone, geographic performance, previous-period pull, budget pacing, Performance Max search insights) are in [gaql-queries.md](references/gaql-queries.md).

## Cost Formatting

Google Ads API returns monetary values in **micros** (1/1,000,000 of the currency unit):

- `cost_micros = 1500000` → `$1.50`
- `campaign_budget.amount_micros = 50000000` → `$50.00/day`
- `cpc_bid_micros = 2500000` → `$2.50`

Always format output as dollars with 2 decimal places. If the account currency (`customer.currency_code`) is not USD, use that currency's symbol or code instead of `$`, still with 2 decimal places, and read the $ thresholds below in the account currency.

Report exports from the Google Ads interface are already in currency units. Do not divide them by 1,000,000.

Rate fields from the API are fractions: `metrics.ctr = 0.034` is 3.4%, and impression share fields are 0–1. Show them as percentages with 1 decimal place. ROAS is `conversions_value / cost` (shown as `3.20x`); CPA is `cost / conversions`. Formulas are in [ppc-formulas.md](references/ppc-formulas.md).

## Anomaly Detection Thresholds

Flag these automatically in any analysis:

| Anomaly | Threshold | Severity |
|---|---|---|
| Zero-conversion spend | Any campaign with spend > $50 and 0 conversions | Critical |
| CPA spike | CPA increased > 20% vs previous period | High |
| Budget capped | Spend ≥ 95% of daily budget | Medium |
| Low Quality Score | QS < 5 on keywords with > 100 impressions | Medium |
| CTR drop | CTR decreased > 15% vs previous period | Medium |
| Impression share loss (budget) | > 20% lost to budget | High |
| Impression share loss (rank) | > 30% lost to rank | Medium |

How to apply them:
- "vs previous period" means the previous period of equal length immediately before the current window. Changes are relative: `(current - previous) / previous * 100`.
- **Budget capped**: compare average daily spend (`cost ÷ days in window`) with the daily budget (`campaign_budget.amount_micros`). For a shared budget, add the spend of every campaign that shares it.
- Thresholds apply over the analysis window (30 days by default). Say which window you used.
- Low-volume rows can trip thresholds by chance. When a flagged campaign or keyword has fewer than 30 clicks in the window, say "low volume" next to the flag.

## Output Format

Always present analysis in structured tables with:

1. **Summary metrics** at the top (total spend, conversions, ROAS, CPA)
2. **Detailed breakdown** by entity (campaign, keyword, search term, etc.)
3. **Anomaly flags** highlighted with severity
4. **Recommendations**: specific, actionable, prioritized

State the account, date window, data source (connector or export), and currency above the summary table. Recommendations name the entity and the change (for example "Add 'free template' as a phrase negative in Campaign A; it spent $212.40 with 0 conversions"), never a generic tip.

## Rate Limits

Google Ads API: Basic Access = 15,000 operations/day, 4 req/sec. Use `LIMIT` clauses and filter by status to reduce result sets.
