# Transcript extraction

## Reading the CSV

Transcript exports differ by tool. Detect the layout before reading:

1. Look at the header row for a text column (`text`, `transcript`, `utterance`, `content`, `message`, `sentence`), a speaker column (`speaker`, `name`, `participant`) and a time column (`time`, `timestamp`, `start`, `start_time`).
2. If there is no header, or no text column, treat each row's non-empty cells joined with spaces as one utterance.
3. Keep the row number and timestamp for every utterance so it can be quoted later.

Work out who is who. The WISE sales manager asks questions and talks about WISE; the prospect describes their business. If speakers are unlabelled, infer from content and say so in the sales notes.

Only the **prospect's** statements count as facts about the business. The sales manager's statements are context.

## What to extract

| Item | Feeds | Notes |
|---|---|---|
| Company name | Sheet header | Prefer the name on the site if they differ; note the difference. |
| Services they sell, ranked by how much they stress them or say they earn from them | Keyword groups | |
| Cities and areas they serve or want to grow in | Cities column and rankings grid | |
| Number of business locations | `tracking.business_locations` | Verify against the site's location pages. |
| Website platform, if mentioned | `seo.website_platform` | Detection from the site wins if they conflict. |
| Ads they say they run (Google, Meta, other) | Tie-break for ads cells | Detection wins; record conflicts in notes. |
| Analytics or agency they mention | Notes | |
| Pain points (leads, rankings, reviews, site, competitors) | Observations and notes | |
| Goals and timeline | Notes | |
| Budget signals, objections, decision makers | Notes only | Never in the sheet. |
| Competitors named | Notes only | |

## Choosing the 5 keyword groups

1. Take the services the prospect stressed most.
2. Turn each into the search phrase a customer would type, without a city (`water heater repair`, not `water heater repair austin`).
3. Check monthly volume with SE Ranking keyword metrics. If a phrase has under 20 searches, try the closest common variant.
4. Pick the 5 with the best mix of what they want to sell and real volume. Record the reason for each in the notes.

## Choosing the 5 cities

1. The city they are based in first.
2. Then the cities they named as wanting more work from.
3. Then cities named on their service-area pages.
4. Pair each keyword group with one city for the "Location & Nearby Cities" column, in the same order (group 1 with city 1).

If fewer than 5 cities exist anywhere: for a local business use the main city's nearest suburbs by population; for a national or online business use the headquarters city plus the largest metros in other states, or the states the prospect names. Say so in the notes.
