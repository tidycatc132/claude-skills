# Workflow detail: the eight phases

Announce each phase in chat as `[Phase X/8: Name]`. The templates below are what each phase produces; keep them short in chat and full in the saved report.

## Phase 1/8: Scope

Infer first, ask second. With a client domain, pull what you can (SEOGets `list_sites`, SE Ranking `DATA_getDomainOverviewWorldwide`, `DATA_getDomainAuthority`) before asking anything.

```
Product/service:   <what they sell, in one line>
Audience:          <who buys, segment and role>
Business goal:     <leads | sales | signups | reach | GEO visibility>
Domain strength:   DR/DA <n> (Measured from <tool>) or N/A
Geography:         <country, region, city if local>
Language/market:   <hl/gl pair, e.g. en-us>
Existing assets:   <known pages, exports supplied>
Data available:    <SE Ranking | SEOGets | scripts only | user export>
```

Ask only for what is missing and material: business goal and geography matter; DR is nice to have.

## Phase 2/8: Discover

**Striking distance first.** If SEOGets is connected: `list_sites`, then `list_site_queries` for the client site with a high row limit (the API sorts by clicks and has no position filter, so ask for 1,000+ rows). Save the export as a CSV with `query, clicks, impressions, ctr, position`, then:

```
python3 scripts/score_keywords.py gsc_queries.csv --position-range 5 20 --source Measured --out striking.csv --md striking.md
```

That set is the fastest opportunity pool. Report it as Measured (position, impressions, clicks) and enrich it with volume and KD from SE Ranking when available.

Then seed from five angles, 3 to 5 seeds each:

| Angle | Example for a plumber | Example for a SaaS |
|---|---|---|
| Core product or service | water heater repair, drain cleaning | project management software |
| Problem terms | no hot water, slow drain | missed deadlines, task overload |
| Solution terms | tankless water heater, hydro jetting | gantt chart tool, kanban board |
| Audience language | "plumber who shows up on time" | "pm tool my team will actually use" |
| Industry jargon | backflow testing, sewer scope | WBS, sprint velocity |

Expand each seed with `DATA_getRelatedKeywords`, `DATA_getSimilarKeywords`, `DATA_getLongTailKeywords` and `DATA_getKeywordQuestions`; without tools, `scripts/autocomplete.py "<seed>" --expand` (ideas only, no metrics).

## Phase 3/8: Variations

Modifiers: best, top, for [audience], [year], how to, what is, vs [alternative], examples, tools, cost, pricing, reviews, alternatives.

Long-tail patterns: for beginners, for small business, free, software / tool / service, template, checklist, guide, near me, [city], [neighbourhood], emergency, same day, DIY, "without [thing]".

Keep a variation only if it has a plausible distinct intent or page. "plumber denver" and "denver plumber" are one keyword; "plumber denver cost" is another.

## Phase 4/8: Classify

Use `references/intent-taxonomy.md`. For the shortlist, verify against the SERP with `DATA_getSerpResults` and record "SERP-verified"; otherwise label the intent Estimated. Add the `intent` column to the working CSV before scoring.

## Phase 5/8: Score

Fill `relevance` (1 to 5, Estimated unless the user set it) and `trend` (growing / stable / declining, from SE Ranking history, `scripts/wiki_pageviews.py` as a proxy, or Estimated). Then:

```
python3 scripts/score_keywords.py keywords.csv --out scored.csv --md scored.md
```

Quote scores from the output; never recompute in prose.

Difficulty bands used in the report:

- **Low, KD 1 to 39**: weak competitors, thin content, forums or long-tail pages in the top 10. A DR 20 site can win with a good page.
- **Medium, KD 40 to 69**: mixed authority; some strong brands, some beatable pages. Needs a better page plus a few links.
- **High, KD 70 to 100**: major brands, heavy link requirement, often ad-heavy SERPs. A pillar-level, multi-quarter effort.

## Phase 6/8: GEO-Check

Flag keywords likely to be answered by AI assistants and AI Overviews:

- questions (who, what, why, how, can, should, is)
- definitions and "what is X"
- comparisons (X vs Y, best X for Y)
- lists ("types of", "examples of", "tools for")
- how-tos with a bounded answer
- anything answerable in a paragraph or a table of facts
- well-documented topics with low to medium commercial friction (people ask an assistant before they hire)

For each candidate, recommend an answer format: direct answer paragraph (40 to 60 words), numbered steps, comparison table, definition plus example, FAQ block with schema. Note that GEO candidates are usually TOFU or MOFU and support a pillar; they are rarely the revenue page.

## Phase 7/8: Cluster

Use `references/topic-clusters.md`. Run the viability worksheet before naming a pillar. Output one cluster block per pillar using the template there.

## Phase 8/8: Deliver

Report sections in order:

1. **Executive Summary**: 3 to 5 sentences, the single best move first, with numbers.
2. **Top Opportunities**: Quick Wins, Growth, GEO. At least 3 in total, each with volume, KD, intent, tier, bucket, score and a reason.
3. **Topic Clusters**: cluster blocks.
4. **Content Calendar**: 3 months, 2 to 4 items a month, keyword, format, funnel, cluster, why now.
5. **Next Steps**: what the client must do, what the next skill is.

Then the handoff block (see SKILL.md). In the saved file, finish with the `targets:` block described in SKILL.md, one row per calendar page.

## Quality bar

Every recommendation carries at least one specific number and a reason.

| Generic (do not write) | Actionable (write this) |
|---|---|
| "Target long-tail keywords." | "Target 'project management for nonprofits' (vol 320, KD 22): no DR 40+ site in the top 10." |
| "This keyword has potential." | "Opportunity 8.4: vol 4,800, KD 28, transactional, and the top-5 content is from 2022." |
| "Create a pillar page about water heaters." | "Pillar 'water heater repair denver' (vol 880, KD 29, P0 4.43) with 9 cluster pages; combined volume 7,600/mo, no competitor has more than 3 pages on it." |
| "Improve rankings for striking-distance terms." | "'emergency plumber denver' sits at 7.8 with 4,100 impressions and 2.3% CTR; a title rewrite and a 24/7 proof block should move it into the top 5." |

Done when: every shortlisted keyword has volume, KD and intent (or a labeled N/A), keywords sit in pillar and cluster hubs, and 3 or more prioritized opportunities are named.

## Seasonal planning

| Keyword type | Plan | Publish | Example |
|---|---|---|---|
| Calendar events (holidays, tax season, back to school) | 3 to 4 months out | 6 to 8 weeks before peak | "frozen pipes what to do": publish by late October |
| Budget-cycle terms (software, agencies, B2B) | August | October to December | "best crm for nonprofits 2027" |
| Reactive industry events (regulation, outages, product launches) | pre-built templates | within 48 hours | "new [regulation] compliance checklist" |
| Evergreen | any time | lowest-KD first | "how to fix a leaking faucet" |

Confirm seasonality with SE Ranking history or `scripts/wiki_pageviews.py "<Article>" --months 24` (label it an attention proxy).

## Advanced modes

- **Intent mapping**: the user already has a list and wants it classified. Run Phases 4 and 5 only; deliver the scored CSV plus an intent summary table.
- **Seasonal analysis**: the user asks when to publish. Run Phase 2 on the topic, then the seasonal table above with monthly series from SE Ranking or Wikipedia pageviews.
- **Competitor keyword mode**: the user names one competitor and asks what it ranks for. Use `DATA_getDomainKeywords` for that domain, score the result, and stop there. A full gap analysis across several competitors is the competitor-analysis skill's job; say so and hand off.
- **Local keywords for [business] in [city]**: seed with service + city, service + "near me", service + neighbourhoods, and emergency / same-day variants. Check the map pack in the SERP. Quick Wins here are usually service-area pages, not blog posts.
