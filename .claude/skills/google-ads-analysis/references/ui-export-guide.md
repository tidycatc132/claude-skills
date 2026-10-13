# Working From Google Ads Report Exports

Use this when no Google Ads connector is available. Ask the user to download each report below as CSV for the analysis window (and the previous period, when comparing). Menu names in the Google Ads interface change from time to time; ask for the report by name and the columns listed, and accept the closest equivalent.

Exports are in currency units (not micros) and rates are already percentages. Do not divide by 1,000,000.

| Question | Report to export | Columns to include |
|---|---|---|
| Campaign performance | Campaigns | Campaign, Campaign status, Campaign type, Bid strategy type, Budget, Cost, Clicks, Impr., Conversions, Conv. value, CTR, Avg. CPC, Cost / conv. |
| Wasted spend | Search terms | Search term, Added/Excluded, Campaign, Ad group, Cost, Clicks, Impr., Conversions (filter Conversions = 0, sort by Cost) |
| Quality Score | Search keywords | Keyword, Match type, Campaign, Ad group, Quality Score, Exp. CTR, Ad relevance, Landing page exp., Cost, Clicks, Impr., Conversions |
| Device | Campaigns, segmented by Device | Device, Cost, Clicks, Impr., Conversions, Conv. value |
| Impression share | Campaigns | Campaign, Search impr. share, Search lost IS (budget), Search lost IS (rank) |
| Geography | Locations (matched or user locations) | Location, Campaign, Cost, Clicks, Conversions, Conv. value |
| Period-over-period | Any of the above with a comparison date range, or two separate exports | Same columns for both periods |

Column name mapping to the API fields used in SKILL.md:

| Export column | API field |
|---|---|
| Cost | metrics.cost_micros ÷ 1,000,000 |
| Conv. value | metrics.conversions_value |
| Cost / conv. | metrics.cost_per_conversion ÷ 1,000,000 |
| Avg. CPC | metrics.average_cpc ÷ 1,000,000 |
| Search lost IS (budget) | metrics.search_budget_lost_impression_share |
| Search lost IS (rank) | metrics.search_rank_lost_impression_share |
| Exp. CTR | quality_info.search_predicted_ctr |
| Ad relevance | quality_info.creative_quality_score |
| Landing page exp. | quality_info.post_click_quality_score |

Notes:
- Exports often include a totals row and "--" for empty values. Exclude the totals row from per-entity tables and treat "--" as N/A, not zero.
- "< 10%" in impression share columns means under 10%; show it as "<10%".
- Label every figure from an export as user-provided, with the export's date range.
