# Keyword brief: Harbor & Pine Plumbing, water heaters

Date: 2026-10-14. Market: en-us, Portland, Oregon metro. Goal: more water heater service and replacement calls. Domain strength: DR 22 (Measured, SE Ranking). Data: SE Ranking metrics (Measured), Search Console via SEOGets (Measured), relevance and trend judged by the analyst (Estimated), scores from `score_keywords.py` (Calculated).

## Executive Summary

The water heater cluster is viable: 8 pages, 9,140/mo combined volume (Calculated from Measured volumes), and no Portland competitor has more than 2 pages on it. The best informational entry point is "how long does a tankless water heater last" (vol 1,600, KD 19, Measured), a GEO candidate that AI Overviews answer with a single lifespan figure. "tankless water heater vs tank" (vol 2,400, KD 38) is the MOFU bridge to the installation page. The pillar, /water-heaters/, ranks 14.2 for "water heater repair portland" (Measured, Search Console) and needs a refresh first.

## Top Opportunities

### Quick Wins (KD 1 to 39, commercial or transactional)

1. **water heater repair portland**, vol 590, KD 27, transactional, P0 4.38, Opportunity 87.4 (Calculated). Reason: ranking 14.2 with a 410-word service page.
2. **tankless water heater installation portland**, vol 260, KD 24, transactional, P0 4.11, Opportunity 41.6 (Calculated). Reason: no dedicated page yet.

### Growth (KD 40 to 69)

3. **tankless water heater cost**, vol 3,600, KD 44, commercial, P1 3.71, Opportunity 151.2 (Calculated). Reason: national SERP, local angle missing.

### GEO candidates

| Keyword | Volume | KD | Intent | Answer format |
|---|---|---|---|---|
| how long does a tankless water heater last | 1,600 | 19 | informational | direct answer, then a lifespan comparison table |
| tankless water heater vs tank | 2,400 | 38 | commercial | comparison table (lifespan, cost, efficiency), one-paragraph verdict |

## Topic Clusters

### Cluster: Water heaters (pattern: use case)
Pillar: "water heater repair portland"  vol 590  KD 27  transactional  service page  refresh
Cluster pages:
  1. "how long does a tankless water heater last"  vol 1,600  KD 19  I  explainer  new
  2. "tankless water heater vs tank"  vol 2,400  KD 38  C  comparison  new
  3. "tankless water heater installation portland"  vol 260  KD 24  T  service page  new
  4. "tankless water heater maintenance"  vol 880  KD 16  I  how-to  new
  5. "tankless water heater cost"  vol 3,600  KD 44  C  cost guide  new
  6. "water heater anode rod replacement"  vol 720  KD 21  I  how-to  exists (/blog/tank-water-heater-anode-rod/)
  7. "signs your water heater is going out"  vol 1,090  KD 23  I  troubleshooting  new
Viability: passes (8 subtopics, 9,140/mo combined, client services 500+ water heaters a year, no competitor above 2 pages)
Build order: pillar refresh, then pages 1, 4 (lowest KD), then 2, 7, then 3, 5

## Content Calendar (3 months)

| Month | Page | Primary keyword | Format | Why now |
|---|---|---|---|---|
| November | /water-heaters/ refresh | water heater repair portland | service page | ranking 14.2, thin page |
| November | /blog/how-long-does-a-tankless-water-heater-last/ | how long does a tankless water heater last | explainer + FAQ | GEO candidate, lowest KD in cluster |
| December | /blog/tankless-vs-tank-water-heater/ | tankless water heater vs tank | comparison | winter replacement season |
| January | /blog/tankless-water-heater-maintenance/ | tankless water heater maintenance | how-to | KD 16 |

## Next Steps

1. Approve the calendar.
2. Brief the November pages first.

```
status: DONE
objective: Water heater keyword research for Harbor & Pine Plumbing, Portland
key_findings: water heater cluster viable (8 pages, 9,140/mo); GEO entry point is the tankless lifespan question; pillar ranks 14.2 and needs a refresh
evidence: SE Ranking keyword metrics, Measured, 2026-10-14; Search Console via SEOGets, Measured, last 3 months
assumptions: relevance and trend judged by the analyst
open_loops: no competitor page-level audit yet
next_skill: content-brief (write briefs from the targets block)
```

targets:
  - id: water-heater-repair-portland
    primary_keyword: water heater repair portland
    secondary_keywords: [water heater repair near me, water heater service portland]
    intent: Transactional
    funnel: BOFU
    format: service page
    cluster: Water heaters
    pillar_url: /water-heaters/        # this page is the pillar
    geo_candidate: false
    geo_answer_format: N/A
    metrics: {volume: 590, kd: 27, source: Measured}
    why_now: ranking 14.2 with a thin page
  - id: how-long-does-a-tankless-water-heater-last
    primary_keyword: how long does a tankless water heater last
    secondary_keywords: [tankless water heater lifespan, tankless vs tank water heater lifespan, tankless water heater maintenance]
    intent: Informational
    funnel: TOFU
    format: explainer + FAQ
    cluster: Water heaters
    pillar_url: /water-heaters/
    geo_candidate: true
    geo_answer_format: direct answer
    metrics: {volume: 1600, kd: 19, source: Measured}
    why_now: lowest KD in the cluster and an AI Overview answers it with one figure
  - id: tankless-water-heater-vs-tank
    primary_keyword: tankless water heater vs tank
    secondary_keywords: [tankless vs tank water heater cost, is a tankless water heater worth it]
    intent: Commercial
    funnel: MOFU
    format: comparison
    cluster: Water heaters
    pillar_url: /water-heaters/
    geo_candidate: true
    geo_answer_format: comparison table
    metrics: {volume: 2400, kd: 38, source: Measured}
    why_now: winter replacement season
