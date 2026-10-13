# Export Checklist (no connector)

Send this list to the user when no Google Ads connector is available. Ask for CSV exports for the last 30 days, plus the previous 30 days for the Campaigns report. Menu names in the Google Ads interface change from time to time; ask for each report by name and accept the closest equivalent. Exports are in currency units; do not divide by 1,000,000. Treat "--" as N/A and exclude totals rows.

| # | Report | Columns | Feeds dimension |
|---|---|---|---|
| 1 | Campaigns | Campaign, Status, Campaign type, Bid strategy type, Budget, Budget name / shared, Cost, Clicks, Impr., Conversions, Conv. value, Search impr. share, Search lost IS (budget), Search lost IS (rank) | 1, 5 |
| 2 | Ad groups | Ad group, Campaign, Status | 1 |
| 3 | Conversions summary (Goals → Conversions) | Conversion action, Source/type, Category, Count (one / every), Attribution model, Value setting, Primary/secondary, All conv. (30 days) | 2 |
| 4 | Search keywords | Keyword, Match type, Status, Campaign, Ad group, Quality Score, Cost, Clicks, Impr., Conversions | 3, 7 |
| 5 | Negative keywords and negative keyword lists (shared library) | Negative keyword, Match type, Campaign or list, Campaigns the list is applied to | 3 |
| 6 | Search terms | Search term, Added/Excluded, Campaign, Ad group, Cost, Clicks, Impr., Conversions | 3, 7 |
| 7 | Ads | Ad, Ad type, Ad strength, Status, Campaign, Ad group, Final URL, Headlines/descriptions count, Impr., Clicks, Conversions, Cost | 4 |
| 8 | Assets | Asset type (sitelink, callout, structured snippet, call), Level (account/campaign/ad group), Status | 4 |
| 9 | Change history (last 30 days, filtered to ads) | Date, Change type, Campaign | 4 |
| 10 | Landing pages | Landing page, Clicks, Cost, Conversions | 4 |
| 11 | Devices (Campaigns segmented by device) | Campaign, Device, Cost, Clicks, Conversions, Conv. value, Bid adj. | 5, 6 |
| 12 | Locations (where ads showed) | Location, Campaign, Cost, Clicks, Conversions, Conv. value | 6, 7 |
| 13 | Ad schedule / Day and hour | Campaign, Day of week, Hour, Cost, Clicks, Conversions | 6 |
| 14 | Audiences | Audience segment, Campaign, Ad group, Targeting/observation, Cost, Conversions | 6 |
| 15 | Where ads showed (placements) and placement exclusions | Placement, Type, Campaign, Cost, Clicks, Conversions; excluded placements | 6, 7 |

If the user can only provide some of these, audit what arrives and mark the uncovered dimensions Not assessed, naming the missing report. Label all export figures as user-provided with their date range.
