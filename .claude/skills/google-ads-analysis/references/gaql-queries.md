# Additional GAQL Queries

Supporting queries for [SKILL.md](../SKILL.md). Money fields are micros (÷ 1,000,000). Replace dates with real `YYYY-MM-DD` values.

## Account context (run first)

```sql
SELECT
  customer.id, customer.descriptive_name,
  customer.currency_code, customer.time_zone
FROM customer
```

Use `currency_code` for formatting and `time_zone` when stating the window.

## Previous period (for any period-over-period comparison)

Same fields as the current-period query, with explicit dates. Example for a 30-day comparison where the current window is the last 30 days:

```sql
SELECT
  campaign.id, campaign.name,
  metrics.cost_micros, metrics.clicks, metrics.impressions,
  metrics.conversions, metrics.conversions_value,
  metrics.ctr, metrics.cost_per_conversion
FROM campaign
WHERE segments.date BETWEEN '2026-08-14' AND '2026-09-12'
ORDER BY metrics.cost_micros DESC
```

Compute CPA and CTR for each period from the raw totals (cost ÷ conversions, clicks ÷ impressions) rather than averaging daily rates.

## Daily trend (when the user asks "when did it change")

```sql
SELECT
  segments.date, campaign.name,
  metrics.cost_micros, metrics.clicks, metrics.conversions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
ORDER BY segments.date
```

## Budget pacing

```sql
SELECT
  campaign.name, campaign.status,
  campaign_budget.name, campaign_budget.amount_micros,
  campaign_budget.explicitly_shared,
  metrics.cost_micros
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
  AND campaign.status = 'ENABLED'
```

Average daily spend = `cost_micros ÷ 1,000,000 ÷ 30`. Flag "Budget capped" when it is ≥ 95% of `amount_micros ÷ 1,000,000`. When `explicitly_shared` is true, sum spend across the campaigns on that budget name.

## Geographic performance

```sql
SELECT
  campaign.name,
  geographic_view.country_criterion_id,
  geographic_view.location_type,
  metrics.cost_micros, metrics.clicks,
  metrics.conversions, metrics.conversions_value
FROM geographic_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

Resolve IDs to names with:

```sql
SELECT geo_target_constant.id, geo_target_constant.name, geo_target_constant.canonical_name
FROM geo_target_constant
WHERE geo_target_constant.id IN (2840, 2826)
```

For region or city detail, use `user_location_view` with `segments.geo_target_region` or `segments.geo_target_city` if the connector supports them.

## Ad performance

```sql
SELECT
  campaign.name, ad_group.name,
  ad_group_ad.ad.id, ad_group_ad.ad.type, ad_group_ad.ad_strength,
  ad_group_ad.status,
  metrics.impressions, metrics.clicks, metrics.ctr,
  metrics.conversions, metrics.cost_micros
FROM ad_group_ad
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_ad.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

## Performance Max search insights

`search_term_view` does not cover Performance Max. For PMax, use search term categories:

```sql
SELECT
  campaign_search_term_insight.category_label,
  metrics.clicks, metrics.impressions, metrics.conversions
FROM campaign_search_term_insight
WHERE segments.date DURING LAST_30_DAYS
  AND campaign_search_term_insight.campaign_id = '<PMAX_CAMPAIGN_ID>'
```

This view has no cost metric, so PMax wasted spend cannot be measured at the term level. Say so instead of estimating it.

## Field notes

- `metrics.search_impression_share` and the lost-share fields are fractions (0–1). Values under 10% come back as 0.0999.
- `metrics.conversions` can be fractional under data-driven attribution. Show 1 decimal place.
- `quality_info` fields are null for keywords without enough traffic. Count them as "no QS" rather than as low QS.
