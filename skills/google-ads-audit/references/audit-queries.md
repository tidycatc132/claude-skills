# Audit Queries

GAQL for each check in [SKILL.md](../SKILL.md). Money fields are micros (÷ 1,000,000). Rate and impression-share fields are fractions (0–1). Default window `LAST_30_DAYS`. Use `LIMIT` and status filters to stay within API limits (Basic Access: 15,000 operations/day).

## 0. Account context (run first)

```sql
SELECT customer.id, customer.descriptive_name, customer.currency_code, customer.time_zone
FROM customer
```

## 1. Account Structure

Campaigns, types, budgets, and performance (also feeds dimensions 5 and 7):

```sql
SELECT
  campaign.id, campaign.name, campaign.status,
  campaign.advertising_channel_type, campaign.bidding_strategy_type,
  campaign_budget.name, campaign_budget.amount_micros, campaign_budget.explicitly_shared,
  metrics.cost_micros, metrics.clicks, metrics.impressions,
  metrics.conversions, metrics.conversions_value,
  metrics.search_impression_share,
  metrics.search_budget_lost_impression_share,
  metrics.search_rank_lost_impression_share
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

Paused vs enabled counts (no date filter):

```sql
SELECT campaign.id, campaign.status FROM campaign WHERE campaign.status != 'REMOVED'
```

```sql
SELECT ad_group.id, ad_group.status, campaign.name FROM ad_group WHERE ad_group.status != 'REMOVED'
```

- Naming: check whether names follow one pattern (for example `Type | Geo | Theme`). Judgment call; label it as such.
- Theme tightness and keyword-to-ad-group ratio: use the keyword query in section 3 and count keywords per ad group.
- Budget vs performance: rank campaigns by spend share and by ROAS or CPA; flag where the biggest budgets go to the worst performers.

## 2. Conversion Tracking

```sql
SELECT
  conversion_action.id, conversion_action.name, conversion_action.status,
  conversion_action.type, conversion_action.category,
  conversion_action.counting_type,
  conversion_action.attribution_model_settings.attribution_model,
  conversion_action.value_settings.default_value,
  conversion_action.value_settings.always_use_default_value,
  conversion_action.primary_for_goal,
  conversion_action.include_in_conversions_metric
FROM conversion_action
WHERE conversion_action.status = 'ENABLED'
```

Conversions recorded per action in the window:

```sql
SELECT segments.conversion_action_name, metrics.all_conversions, metrics.all_conversions_value
FROM customer
WHERE segments.date DURING LAST_30_DAYS
```

- No enabled action, or enabled actions with 0 conversions while the account spends: tracking failure.
- `counting_type = MANY_PER_CLICK` on lead actions (forms, calls) usually over-counts; on purchases it is correct.
- Value tracking: `always_use_default_value = true` or no values on a sales account means ROAS cannot be trusted.
- Attribution: note last-click vs data-driven.

## 3. Keyword Strategy

```sql
SELECT
  campaign.name, ad_group.id, ad_group.name,
  ad_group_criterion.keyword.text, ad_group_criterion.keyword.match_type,
  ad_group_criterion.status,
  ad_group_criterion.quality_info.quality_score,
  metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions
FROM keyword_view
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_criterion.status = 'ENABLED'
ORDER BY metrics.cost_micros DESC
```

- Match type distribution: share of keywords and of spend by BROAD / PHRASE / EXACT.
- QS distribution: % of keywords with QS < 5 and % with QS > 7, among keywords that have a QS. Report keywords without QS separately.
- Keyword-to-ad-group ratio: enabled keywords ÷ enabled ad groups.

Negative keyword coverage:

```sql
SELECT campaign.name, campaign_criterion.keyword.text, campaign_criterion.keyword.match_type
FROM campaign_criterion
WHERE campaign_criterion.negative = TRUE AND campaign_criterion.type = 'KEYWORD'
```

```sql
SELECT shared_set.id, shared_set.name, shared_set.member_count, shared_set.status
FROM shared_set
WHERE shared_set.type = 'NEGATIVE_KEYWORDS'
```

```sql
SELECT campaign.name, campaign_shared_set.shared_set, campaign_shared_set.status
FROM campaign_shared_set
```

Search term relevance: the zero-conversion search terms query in section 7.

## 4. Ad Creative

```sql
SELECT
  campaign.name, ad_group.name,
  ad_group_ad.ad.id, ad_group_ad.ad.type, ad_group_ad.ad_strength, ad_group_ad.status,
  ad_group_ad.ad.responsive_search_ad.headlines,
  ad_group_ad.ad.responsive_search_ad.descriptions,
  ad_group_ad.ad.final_urls,
  metrics.impressions, metrics.clicks, metrics.conversions, metrics.cost_micros
FROM ad_group_ad
WHERE segments.date DURING LAST_30_DAYS
  AND ad_group_ad.status = 'ENABLED'
```

- Ad strength distribution across RSAs; count headlines and descriptions per RSA.
- Ad groups with only one enabled ad have no test running.
- Landing page diversity: distinct final URLs across ad groups.

Testing velocity (change history only reaches back 30 days; dates must be explicit, so replace the placeholders with the date 29 days ago and today, and a LIMIT is required):

```sql
SELECT
  change_event.change_date_time, change_event.change_resource_type,
  change_event.resource_change_operation, campaign.name
FROM change_event
WHERE change_event.change_date_time >= 'YYYY-MM-DD'
  AND change_event.change_date_time <= 'YYYY-MM-DD'
  AND change_event.change_resource_type = 'AD_GROUP_AD'
ORDER BY change_event.change_date_time DESC
LIMIT 1000
```

No ad changes in 30 days = no recent testing.

Assets (account, campaign, and ad group level):

```sql
SELECT customer_asset.field_type, customer_asset.status FROM customer_asset
```

```sql
SELECT campaign.name, campaign_asset.field_type, campaign_asset.status
FROM campaign_asset
WHERE campaign_asset.status = 'ENABLED'
```

```sql
SELECT campaign.name, ad_group.name, ad_group_asset.field_type, ad_group_asset.status
FROM ad_group_asset
WHERE ad_group_asset.status = 'ENABLED'
```

Check each Search campaign for SITELINK, CALLOUT, STRUCTURED_SNIPPET, and CALL at any level.

Landing pages:

```sql
SELECT landing_page_view.unexpanded_final_url, metrics.clicks, metrics.cost_micros, metrics.conversions
FROM landing_page_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

## 5. Bidding & Budget

Use the campaign query from section 1 (bidding strategy type, budget, spend, impression share).

- Budget utilization: average daily spend = cost ÷ 30; capped when ≥ 95% of the daily budget. Capped campaigns with `search_budget_lost_impression_share` > 20% are losing volume to budget.
- Budget-to-performance: campaigns in the top third by budget whose ROAS or CPA is in the bottom third.
- Shared budgets: `explicitly_shared = true`; list which campaigns share each budget and whether one starves the others.

Bid adjustments:

```sql
SELECT campaign.name, campaign_criterion.type, campaign_criterion.bid_modifier,
       campaign_criterion.device.type, campaign_criterion.location.geo_target_constant
FROM campaign_criterion
WHERE campaign_criterion.type IN ('DEVICE', 'LOCATION', 'AD_SCHEDULE')
```

Bid adjustments other than device −100% are ignored by most Smart Bidding strategies; say so instead of flagging their absence on tCPA/tROAS/Max Conversions campaigns.

## 6. Targeting

Geography:

```sql
SELECT campaign.name, geographic_view.country_criterion_id, geographic_view.location_type,
       metrics.cost_micros, metrics.clicks, metrics.conversions, metrics.conversions_value
FROM geographic_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
```

Resolve IDs with `SELECT geo_target_constant.id, geo_target_constant.name FROM geo_target_constant WHERE geo_target_constant.id IN (...)`.

Device:

```sql
SELECT campaign.name, segments.device, metrics.cost_micros, metrics.clicks,
       metrics.conversions, metrics.conversions_value
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

Compare mobile vs desktop CPA per campaign: variance = (mobile CPA − desktop CPA) ÷ desktop CPA.

Ad schedule:

```sql
SELECT campaign.name, segments.day_of_week, segments.hour,
       metrics.cost_micros, metrics.clicks, metrics.conversions
FROM campaign
WHERE segments.date DURING LAST_30_DAYS
```

Audiences:

```sql
SELECT campaign.name, ad_group.name, ad_group_criterion.type, ad_group_criterion.display_name,
       metrics.cost_micros, metrics.conversions
FROM ad_group_audience_view
WHERE segments.date DURING LAST_30_DAYS
```

```sql
SELECT campaign.name, campaign_criterion.type, campaign_criterion.display_name,
       metrics.cost_micros, metrics.conversions
FROM campaign_audience_view
WHERE segments.date DURING LAST_30_DAYS
```

Placement exclusions (Display/Video):

```sql
SELECT campaign.name, campaign_criterion.placement.url
FROM campaign_criterion
WHERE campaign_criterion.type = 'PLACEMENT' AND campaign_criterion.negative = TRUE
```

## 7. Wasted Spend

Zero-conversion search terms:

```sql
SELECT
  search_term_view.search_term, search_term_view.status,
  campaign.name, ad_group.name,
  metrics.cost_micros, metrics.clicks, metrics.impressions, metrics.conversions
FROM search_term_view
WHERE segments.date DURING LAST_30_DAYS
  AND metrics.conversions = 0
  AND metrics.cost_micros > 0
ORDER BY metrics.cost_micros DESC
LIMIT 1000
```

Display/Video placement waste:

```sql
SELECT detail_placement_view.display_name, detail_placement_view.target_url,
       detail_placement_view.placement_type, campaign.name,
       metrics.cost_micros, metrics.clicks, metrics.conversions
FROM detail_placement_view
WHERE segments.date DURING LAST_30_DAYS
ORDER BY metrics.cost_micros DESC
LIMIT 500
```

Low-QS keywords consuming budget: keywords from section 3 with QS < 5, summed by spend. Underperforming regions: locations from section 6 with spend and 0 conversions, or CPA more than 2× the account CPA.

Performance Max is not in `search_term_view`; its search terms (categories only, no cost) come from `campaign_search_term_insight` filtered by campaign ID. Note PMax waste as Not measurable rather than estimating it.

Compute total wasted spend per [severity-and-scoring.md](severity-and-scoring.md).
