# Prioritization: three scores, one fixed order

All three are implemented in `scripts/score_keywords.py`. Do the arithmetic there, never in prose. Every score the script prints is labeled **Calculated**; its inputs keep their own labels (Measured, User-provided, Estimated).

Order of use:

1. **Priority Score** triages the long list into tiers (P0 to P3). Run it first, on everything.
2. **Opportunity Score** orders the shortlist and the content calendar inside each tier.
3. **Impact x Confidence** is an optional third pass when CPC, current position and trend are all known. Use it to break ties and to argue for a keyword to a client who cares about revenue.

Reporting a score from pass B for a keyword that never went through pass A is the mistake to avoid: a huge Opportunity Score on a tangential keyword is noise.

## A. Priority Score (triage)

Five factors, each scored 1 to 5, weighted and summed. The result is on a 1 to 5 scale.

| Factor | Weight | 1 = | 5 = | How the script fills it |
|---|---|---|---|---|
| Search volume | 20% | 100/mo or less | 10,000/mo or more | `volume` column, interpolated on log10 between the anchors (100 = 1, 1,000 = 3, 10,000 = 5) |
| Keyword difficulty | 25% | KD 80 or more | KD 20 or less | `kd` column, linear between the anchors |
| Business relevance | 30% | tangential | core offering | `relevance` column 1 to 5, a judgment call. Label it **Estimated** unless the user supplied it |
| Intent match | 15% | informational | transactional | `intent` column, informational 1, navigational 2, commercial 4, transactional 5 |
| Trend | 10% | declining | growing | `trend` column, declining 1, stable 3, growing 5, or a number 1 to 5 |

Why log10 for volume: the anchors are two orders of magnitude apart. Linear interpolation on raw volume would score 1,000/mo at 1.4, which puts a healthy mid-volume keyword next to a dead one. Say in the report that the volume band is log-scaled.

Tiers:

| Tier | Score | Meaning |
|---|---|---|
| **P0 Must Target** | 4.0 to 5.0 | Create or optimize now |
| **P1 High Value** | 3.0 to 3.9 | Next sprint |
| **P2 Opportunity** | 2.0 to 2.9 | Future calendar |
| **P3 Monitor** | 1.0 to 1.9 | Watch, do not build |

A row missing any of the five inputs gets `N/A` for the score and tier. Fill the input (from a tool, the user, or a labeled estimate for relevance and trend) rather than guessing a number into the data file.

## B. Opportunity Score (shortlist ordering)

```
Opportunity = (volume x intent value) / max(kd, 1)
intent value: informational 1, navigational 1, commercial 2, transactional 3
```

The score has no fixed scale; it only orders keywords against each other within one research set. Quote it alongside its inputs ("Opportunity 162.9, vol 1,900, KD 35, transactional"), never alone.

Buckets, decided by KD band and intent (volume differentiates inside the bucket through the score itself):

| Bucket | KD | Intent | Stars | Use |
|---|---|---|---|---|
| **Quick Win** | low, 1 to 39 | commercial or transactional | ★★★★★ | First 4 to 6 weeks |
| **Growth** | medium, 40 to 69 | commercial or transactional | ★★★★ | Months 2 to 3, needs links or a stronger page |
| **Long-term** | high, 70 to 100 | commercial or transactional | ★★★ | Pillar-level investment, 6+ months |
| **Research** | low, 1 to 39 | informational or navigational | ★★ | TOFU and GEO coverage, cluster support |
| **Hold** | 40 to 100 | informational or navigational | ★ | Only as cluster support for a pillar that needs it |

High volume with low KD and high intent is still a Quick Win; the spec's "low to medium volume" in that bucket describes what is usually found there, not a cap.

## C. Impact x Confidence (optional third pass)

Only runs when `volume`, `kd`, `cpc`, `trend` and a `position` column are present. Each component is normalized 0 to 1; the weights are constants at the top of the script (`IMPACT_W`, `CONF_W`).

```
Impact     = 0.40 volume + 0.20 cpc + 0.25 funnel stage + 0.15 trend
Confidence = 0.45 inverse KD + 0.35 current position + 0.20 topical authority
Priority   = Impact x Confidence           (0 to 1)
```

Normalization:

- volume: the Priority Score volume factor rescaled to 0 to 1 (log10 band)
- cpc: dollars divided by 10, capped at 1 (a $10+ CPC is "max commercial value")
- funnel stage: TOFU 0.33, MOFU 0.66, BOFU 1.0
- trend: declining 0, stable 0.5, growing 1
- inverse KD: 1 minus KD/100
- current position: 1 to 10 = 1.0, 11 to 20 = 0.8, 21 to 50 = 0.5, 51 to 100 = 0.3, not ranking = 0.2
- topical authority: relevance rescaled to 0 to 1 as a proxy, unless the user gives a better signal

Read it as "how much is this worth, times how likely are we to get it". A blank position cell in a file that has a position column means "not ranking" and is a known value; a file with no position column at all means the pass cannot run.

## Funnel tags

The script tags every keyword with a funnel stage from intent plus signal words:

- **BOFU**: commercial or transactional intent, or the keyword contains pricing, price, cost, best, vs, services, agency, hire, buy, near me, quote, company, contractor, installation, repair, replacement, emergency, cleaning, detection, testing, inspection.
- **MOFU**: informational with buying signals such as how to, guide, ROI, case study, review, comparison, checklist, template, examples, tips.
- **TOFU**: everything else that is informational.

When the goal is revenue, work BOFU first. TOFU and MOFU exist for reach, cluster support and GEO coverage, and they are what the GEO-Check phase feeds on. The full six-stage funnel and how these three tags map onto it is in `intent-taxonomy.md`.

## Running the script

```
python3 scripts/score_keywords.py keywords.csv --out scored.csv --md scored.md
python3 scripts/score_keywords.py keywords.csv --mode opportunity --out shortlist.csv
python3 scripts/score_keywords.py gsc.csv --position-range 5 20 --source Measured --out striking.csv
python3 scripts/score_keywords.py --selftest
```

Input columns (CSV or JSON): `keyword, volume, kd, intent, relevance, trend, cpc, position, impressions, clicks, source`. `query` is accepted for `keyword`. Missing columns produce `N/A` in every score that needs them.

Output columns, always in this order: `keyword, volume, kd, intent, funnel, relevance, trend, cpc, position, impressions, clicks, source, priority_score, tier, intent_value, opportunity_score, bucket, impact, confidence, impact_confidence`.

`--mode all` (default) sorts by tier then Opportunity; `triage`, `opportunity`, `impact` sort by that score; `striking` (set automatically with `--position-range`) sorts by impressions.
