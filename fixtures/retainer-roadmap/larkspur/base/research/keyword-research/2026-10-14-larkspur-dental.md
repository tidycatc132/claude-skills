# Keyword brief: Larkspur Family Dental, Boise

Date: 2026-10-14. Market: en-us, Boise, Idaho metro. Goal: more new-patient and emergency appointment requests. Domain strength: DR 9 (Measured, SE Ranking). Data: SE Ranking metrics (Measured), relevance and trend judged by the analyst (Estimated), scores from `score_keywords.py` (Calculated). Scored CSV: 2026-10-14-larkspur-dental-scored.csv.

## Executive Summary

The new site can compete first on emergency and family dentistry in Boise: "emergency dentist boise" (vol 1,300, KD 32) and "family dentist boise" (vol 720, KD 28) are both P0 Quick Wins. "dentist boise" (vol 6,600, KD 61) is the biggest prize but needs authority the domain does not have yet. Implants are the highest-value service: "dental implants boise" (vol 880, KD 44, CPC 31.20).

## Top Opportunities

### Quick Wins (KD 1 to 39, commercial or transactional)

1. **emergency dentist boise**, vol 1,300, KD 32, transactional, P0 4.45, Opportunity 121.88 (Calculated). Reason: no Boise practice has a dedicated emergency page in the top 5.
2. **family dentist boise**, vol 720, KD 28, transactional, P0 4.21, Opportunity 77.14 (Calculated). Reason: matches the practice's core patient base.
3. **sedation dentistry boise**, vol 210, KD 21, transactional, P0 4.01, Opportunity 30.00 (Calculated). Reason: anxious patients are a stated audience.

### Growth (KD 40 to 69)

4. **dentist boise**, vol 6,600, KD 61, transactional, P0 4.04, Opportunity 324.59 (Calculated). Reason: head term; earn it with the service pages first.
5. **dental implants boise**, vol 880, KD 44, commercial, P0 4.03, Opportunity 40.00 (Calculated). Reason: highest CPC in the set.

### GEO candidates

| Keyword | Volume | KD | Intent | Answer format |
|---|---|---|---|---|
| what to do for a cracked tooth | 2,900 | 17 | informational | direct answer, then numbered steps |
| how much do dental implants cost | 9,900 | 48 | informational | cost range table, then what changes the price |

## Topic Clusters

### Cluster: Emergency dental care (pattern: use case)
Pillar: "emergency dentist boise"  vol 1300  KD 32  transactional  service page  new
Cluster pages:
  1. "what to do for a cracked tooth"  vol 2900  KD 17  I  explainer  new
Viability: fails the 5,000/mo test on its own; kept for a stated strategic reason (emergency visits are the practice's fastest-growing line)

### Cluster: Dental implants (pattern: use case)
Pillar: "dental implants boise"  vol 880  KD 44  commercial  service page  new
Cluster pages:
  1. "how much do dental implants cost"  vol 9900  KD 48  I  cost guide  new
Viability: passes (combined 10,780/mo)

## Content Calendar (3 months)

| Month | Page | Primary keyword | Format | Why now |
|---|---|---|---|---|
| January | /blog/cracked-tooth/ | what to do for a cracked tooth | explainer + FAQ | lowest KD in the set |
| February | /blog/dental-implant-cost/ | how much do dental implants cost | cost guide | supports the implants page |
| March | /blog/are-dental-x-rays-safe/ | are dental x rays safe | explainer | common new-patient question |

## Next Steps

1. Build the P0 service pages into the new site.
2. Brief the calendar pages after launch.

```
status: DONE
objective: Keyword research for Larkspur Family Dental, Boise
key_findings: emergency and family dentistry are the Quick Wins; dentist boise needs authority first; implants carry the highest CPC
evidence: SE Ranking keyword metrics, Measured, 2026-10-14
assumptions: relevance and trend judged by the analyst
open_loops: none
next_skill: content-brief (write briefs from the targets block)
```

targets:
  - id: emergency-dentist-boise
    primary_keyword: emergency dentist boise
    secondary_keywords: [same day dentist boise, emergency dental care boise]
    intent: Transactional
    funnel: BOFU
    format: service page
    cluster: Emergency dental care
    pillar_url: /emergency-dentist/        # this page is the pillar
    geo_candidate: false
    geo_answer_format: N/A
    metrics: {volume: 1300, kd: 32, source: Measured}
    why_now: no dedicated emergency page in the Boise top 5
  - id: dental-implants-boise
    primary_keyword: dental implants boise
    secondary_keywords: [tooth implant boise, implant dentist boise]
    intent: Commercial
    funnel: BOFU
    format: service page
    cluster: Dental implants
    pillar_url: /dental-implants/        # this page is the pillar
    geo_candidate: false
    geo_answer_format: N/A
    metrics: {volume: 880, kd: 44, source: Measured}
    why_now: highest CPC in the set
