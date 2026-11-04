# Roadmap format and task rules

## File: `roadmap/<slug>/<slug>-seo-roadmap.md`

```
Client: <client>
Date: <YYYY-MM-DD>
Growth blueprint: <path>
Keyword research: <path> | none
Competitor analysis: <path> | none
Dev handoff index: <path>
Staging QA: <path> | none
BugHerd status: <path> | none
Launch check: <path> (RESULT: LIVE OK | LIVE ISSUES) | none
Week 5 feedback: <path>; <path> | none
Live site: <URL from the launch check's Live: line> | unknown

# SEO/GEO Roadmap: <client>

## Summary

<three to five sentences>

## Roadmap

| Month | Task | Description | Priority | Est. hours | Owner | Source |
|---|---|---|---|---|---|---|
| 1 | ... | ... | high | 0.5 | SEO | launch carry-over |

## Not Planned

- <Source>: <reason>
```

Column values: `Month` is `1`, `2` or `3`. `Priority` is `high`, `medium` or `low`. `Est. hours` is a number above 0 (0 only for an `Already done` row). `Owner` is `SEO`, `Content`, `AM` or `Dev`. `Source` is `launch carry-over` or one or more `<path> > <row>` parts joined by `; `, each path a file in the working folder. Rows are sorted by month, then priority. The header lines tell `check` and Month 1 mode which reports the roadmap was built from; leave them as written.

## Where each task comes from (what scaffold writes)

| From | Task | Month, priority, hours, owner |
|---|---|---|
| launch carry-over (always) | the six tasks in SKILL.md, with the live URL and the Blueprint's high-priority sitemap pages filled in | 1, high, 0.5 to 1 h, SEO |
| staging QA `## Findings` row (newest report) | `<page>: <Fix>`; the description says whether it was deferred at the Week 5 sweep (BugHerd `deferred`) or is still open. Rows whose BugHerd status is done or closed are skipped | CRITICAL or MAJOR: 1, high; MINOR: 2, low; 1 h; owner from the department (Design and Development are Dev, Account Management is AM) |
| launch check `## Findings` row (newest report) | `<page>: <Fix>`, "Open on the launch check of <date> (BugHerd #<id>)". A fix shows up as `FIXED` on Dev's next launch check run | as above, Dev |
| dev index `### Redirects` row with `NO TARGET` | `Choose a 301 target for <old URL>` | 1, high, 0.5 h, SEO |
| Week 5 feedback `Scope Change` row | the row's Action; the description quotes the client and the `PM/AM:` note | 1, medium, 1 h, AM |
| keyword report content calendar row | `Write and publish <page> (<format>)`, or `Refresh <page>` when the calendar says refresh. The k-th month in the order the calendar lists them becomes Month k; months after the third go to Not Planned | Tier 2 keyword: high; otherwise medium; 6 h (refresh 3 h); Content |
| dev index page that is not `Build` and not in the calendar | `Write and publish <page> (<URL>)` | 2, medium, 6 h, Content |
| Blueprint Tier 2 keyword not in the calendar | `Choose the page that targets "<keyword>"` | 2, medium, 2 h, SEO |
| Blueprint Tier 3 keyword not in the calendar | `Plan content for "<keyword>"` | 3, low, 2 h, SEO |
| competitor report `Referring domains` row, when the client has fewer than the strongest rival | `Start local link building` | 2, medium, 4 h, SEO |
| competitor report review, citation, listing or link line (Strengths, Weaknesses, Priority Opportunities, Action Plan) | `[WRITE: ...]` for you to name; Source `<report> > <section> #<n>` | 3, medium, 2 h, SEO (change the owner to fit) |

Skipped automatically and listed under `## Not Planned`: a calendar row whose keyword is a Tier 1 (build) keyword, a calendar row whose page was built for launch, calendar months after the third, the "N more" Tier keywords the Blueprint table did not show, and any QA finding or Scope Change about markup work the process does not include.

`scaffold` prints a `WARN:` line when the keyword report has a Content Calendar it cannot read (missing `Month`, `Page` or `Primary keyword` columns) or the competitor report has no Referring domains row and no review, citation, listing or link lines. Say so in your answer; those tasks are missing, not absent.

## What `check` tests

- the header lines, the exact table header, no `[WRITE` left, a non-empty Summary;
- each row's Month, Priority, Owner and hours values, a Source on every row, and that each Source path exists;
- the six carry-over tasks in Month 1 with Source `launch carry-over` (found by sitemap, indexing, GA4, seo-drift-monitor, Core Web Vitals, Business Profile);
- no `Content` row (other than `Refresh` or `Update`, or a QA fix whose Source is a `QA-` or `CE-` id) names a Tier 1 keyword;
- each `## Not Planned` line is `- <Source>: <reason>`;
- no structured data, schema, JSON-LD or rich-result wording anywhere;
- every task scaffold would write from the current files is still in the table, or its Source is under `## Not Planned` with a reason. A new launch check re-run or a new feedback round after the roadmap shows up here: add its row (re-running scaffold with `--force` loses edits) or let Month 1 mode pick it up.

## Defaults taken

- The roadmap is three months. Blueprint Phase 3 (months 4 to 6) work appears as Month 3 starting tasks (Tier 3 planning, authority work), not as later months.
- Staging QA has no `DEFERRED` rows; deferrals are read from the BugHerd status file the Week 5 sweep used.
- Hours are starting estimates for the SEO to change.
