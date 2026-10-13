# Page Inclusion and Nesting (architecture mode)

Used at Step 1b (Decide Which Pages Exist) and Step 3 (Design the Hierarchy) of [SKILL.md](../SKILL.md). Missing data is N/A, never zero.

## Inputs (all optional)

- **Inventory and performance**: the inventory from [data-collection.md](data-collection.md), joined to 12 months of per-page sessions, key events, clicks and impressions (SEO Gets `get_site_performance` by page, or a GA4/GSC export).
- **Candidate pages**: queries with impressions but no page targeting them (SEO Gets `list_site_queries`), and related or question keywords around each offer (SE Ranking `DATA_getRelatedKeywords`, `DATA_getKeywordQuestions`, volumes from `DATA_getKeywordsMetrics`).
- **Competitors**: 3–5 user-named, else SE Ranking `DATA_getDomainCompetitors` sorted by `common_keywords`. WebFetch each homepage and record its Level 1 nav labels in order. With no web access, skip the benchmark and say so.
- **Internal site search**: only from a user-supplied GA4 search-term export or CMS search log; otherwise N/A.
- **Card-sort or tree-test results, heatmaps**: user-supplied only. If given, they override the model's grouping and labels.

## Inclusion score (0–12)

| Metric | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| T. Traffic (sessions, 12 months) | ≤ 12 | 13–120 | 121–1,200 | > 1,200 |
| D. Search demand (impressions or volume per month for an intent no other page serves) | none | < 50 | 50–500 | > 500 |
| S. Internal searches (12 months) | none | 1–25 | 26–100 | > 100 |
| C. Conversion (key events on page) | none | funnel step, no events | 1–10 | > 10 or user-named conversion page |

Score = (T + D + S + C) × 12 ÷ points available − M, floored at 0, where M = 2 for high-maintenance pages (prices, specs, regulations, dated stats, team lists), else 0. Points available is 3 per metric that is not N/A; rescale before subtracting M and label the result Calculated. New builds score candidates on D and C only; with neither, every user-listed page is `create` with score N/A and the reason "user-specified, no demand data".

**Overrides**: legal or required pages are kept (footer). Pages with C ≥ 2 are never retired; low-traffic, high-value pages (spec sheets, case studies, pricing) are kept and moved to a more visible parent. URLs the user must keep are kept.

**ROT tags**: Redundant (same intent as another page; merge into the stronger), Outdated (stale facts or offers; revise), Trivial (thin, no unique purpose; retire or merge), OK.

| Condition | Decision |
|---|---|
| Redundant | merge into the stronger page |
| Score ≥ 6 | keep (revise if Outdated or Trivial) |
| Score 3–5.9 | revise if it has its own intent (D ≥ 1), else merge into the closest parent |
| Score < 3 and T = 0 | retire, or merge if it has inbound links worth keeping |
| Score < 3 and T ≥ 1 | merge into the closest parent (keeps the traffic via a 301) |
| Candidate with D ≥ 2 | create |
| Candidate with D = 1 | add as a section of an existing page |

A retire or merge on a page with C ≥ 1 or more than 5% of site sessions goes to the user as a decision (keep / merge / retire), with its numbers (this is the architecture decision gate in SKILL.md).

**Decision table columns**: page, current URL, action, merge into, ROT, score, reason (cites the numbers), evidence label.

## Labels

For each Level 1 and Level 2 concept, compare the audience's wording (persona file, testimonials, FAQ), top query wording, the label most competitors use, and the current label. Choose the users' word; prefer the competitor convention when it is also the users' word; never internal jargon. If most competitors put a page type in the main nav (Pricing for B2B SaaS, Locations for multi-location services), include it or say why not.

## Nesting rules

1. Level 1 has 4–7 categories (utility links and the CTA do not count), matching the header spec. More than 7 costs −5 in the architecture score.
2. Level 1 labels are mutually exclusive: for each audience question exactly one label is the obvious home.
3. Level 1–2 parents are hubs that summarize and route; plan a hub page for any empty container.
4. Children are a specific instance, facet, or deeper dive of the parent.
5. A parent with one child: merge the child into the parent (−5 each if left).
6. A parent with more than 12 children: split into subgroups (10–12 is a warning).
7. Important pages stay within 3 clicks. Other pages may sit at Level 4–5 when every click clearly narrows the choice.
8. Each page has one parent; cross-branch links belong in Step 6.
9. Directories, stores and resource libraries use filters for attributes. A filter combination gets its own page only with D ≥ 2 for that exact combination; list the rest as "filter, not a page".

## Validation without a tree-testing tool

Write 8–12 "Where would you find…?" tasks from the audience's top questions, with the expected path. Walk each through the tree and flag any where two Level 1 labels are plausible. Offer the list to the user to run in any survey or tree-test tool.

## targets.csv (for content-brief-creator)

Offered in Save Results as `seo-reports/site-structure-optimizer/YYYY-MM-DD-<site-or-topic>-targets.csv`, UTF-8, header row first. One row per page whose action is `create` or `revise` and that has a primary keyword. A page with no keyword gets no row and goes in `open_loops` as "needs keyword research (keyword-research)".

```
page_slug,primary_keyword,secondary_keywords,intent,funnel_stage,pillar,cluster_role,geo_format,priority_tier,opportunity_bucket,volume,kd,existing_url,source
```

| Column | Value | Source |
|---|---|---|
| `page_slug` | last URL segment from the URL map | Step 4 |
| `primary_keyword` | the query with the most impressions on the page (inventory) or the candidate query itself (create) | traffic data or candidate list; empty = no row |
| `secondary_keywords` | other queries for the same page, `;`-separated, may be empty | same |
| `intent` | `informational`, `commercial`, `transactional`, `navigational` | model inference from the query wording, labeled Estimated |
| `funnel_stage` | `awareness`, `consideration`, `decision` | from `intent` (informational→awareness, commercial→consideration, transactional or navigational→decision) |
| `pillar` | the hub's `page_slug` | Step 6 |
| `cluster_role` | `pillar` for hubs, else `cluster` | Step 6 |
| `geo_format` | `faq`, `how-to`, `comparison`, `definition`, `list`, or empty | model inference from `intent` and page type, labeled Estimated |
| `priority_tier` | `P1` (C ≥ 2 or score ≥ 9), `P2` (score 6–8.9), `P3` | inclusion score |
| `opportunity_bucket` | `new-page` (create), `revise` (revise), `consolidate` (merge target that is also revised) | decision table |
| `volume` | monthly search volume of `primary_keyword`, empty when no keyword tool returned it | SE Ranking `DATA_getKeywordsMetrics` or user-provided |
| `kd` | keyword difficulty 0–100 from the same call, empty when unavailable | same |
| `existing_url` | current URL for revise rows, empty for create rows | inventory |
| `source` | `site-structure-optimizer` | fixed |

Never invent `volume` or `kd`; leave them empty and say so in `assumptions`.
