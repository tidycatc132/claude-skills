---
name: growth-blueprint
description: Writes a website build's Growth Blueprint and the internal AM Briefing from the files Week 1 produced. Use when SEO or the AM asks to write or redo the Growth Blueprint, the Blueprint document or strategy write-up for a new build, or the AM Briefing on the Blueprint, for a client whose kickoff folder, Reference Kit, saved keyword research, sitemap report and competitor report exist. A script copies the keyword tiers and sitemap from the reports and checks sections, Source lines, that every figure is in a named source and the page cap. Missing inputs become NEEDS INPUT lines, never invented figures. Do NOT use for the keyword research itself (use keyword-research), planning the sitemap (use site-structure-optimizer), benchmarking competitors (use competitor-analysis), the Blueprint Input Package from the Kickoff Call (use kickoff-call-processing), the brand and voice files (use client-reference-kit), or checking that Week 1 is complete (use week-1-handoff-check).
---

# Growth Blueprint

The Blueprint is the strategy record for a new website build: the client-facing document SEO writes in Week 2, plus a one-page internal AM Briefing. It is assembled from what Week 1 already decided. Where a Week 1 file and the Blueprint would disagree, the file wins and the Blueprint quotes it.

## Inputs

Paths are relative to the client's working folder. `<slug>` is the kickoff folder name; `<client-slug>` is the folder under `client-reference/` (found automatically when there is only one).

| Input | Path | Written by |
|---|---|---|
| Client context (scope cap in `SOW pages:`) | `kickoff/<slug>/<slug>-context.md` | new-build-kickoff, client-context-update |
| Blueprint Input Package | `kickoff/<slug>/<slug>-blueprint-input-package.md` | kickoff-call-processing |
| Quote bank | `kickoff/<slug>/<slug>-quote-bank.md` | kickoff-call-processing |
| Reference Kit | `client-reference/<client-slug>/` `brand.md`, `voice.md`, `style.md`, `audience.md`, `compliance.md` | client-reference-kit |
| Keyword report and its scored CSV | last-named `research/keyword-research/*.md` and the `*-scored.csv` beside it | keyword-research |
| Sitemap report and its targets CSV | last-named `seo-reports/site-structure-optimizer/*.md` and the `*-targets.csv` beside it | site-structure-optimizer |
| Competitor report | last-named `seo-reports/competitor-analysis/*.md` | competitor-analysis |

The script reads two machine formats exactly:

- The keyword scored CSV, header `keyword`, `volume`, `kd`, `intent`, `funnel`, `relevance`, `trend`, `cpc`, `position`, `impressions`, `clicks`, `source`, `priority_score`, `tier`, `intent_value`, `opportunity_score`, `bucket`, `impact`, `confidence`, `impact_confidence`. Only `keyword`, `volume`, `kd`, `intent` and `tier` (`P0` to `P3`, or `N/A`) are required; rows tiered `P3` or `N/A` are left out unless they are a build page's keyword.
- The sitemap targets CSV, header `page_slug`, `primary_keyword`, `secondary_keywords`, `intent`, `funnel_stage`, `pillar`, `cluster_role`, `geo_format`, `priority_tier`, `opportunity_bucket`, `volume`, `kd`, `existing_url`, `source`. It uses `page_slug`, `primary_keyword`, `volume`, `kd` and `opportunity_bucket` (`new-page`, `revise`, `consolidate`). Optional: without it, Tier 1 falls back to the report's `P0` keywords and there is no content plan table.

From the last-named sitemap report that has a `countable pages N / SOW cap M` line (an architecture-mode report; linking-mode reports are skipped) it copies N and the first table with a `URL` column (the URL map, `| Page | URL | Parent | Nav location | Priority |`), verbatim. A report without a URL map gets a `[NEEDS INPUT: ...]` line instead.

## Outputs

- `blueprint/<slug>/<slug>-growth-blueprint.md`: header lines `Client:`, `Date:`, `Prepared by:`, then exactly these `##` sections in this order: `Executive Summary`, `Business and Market Overview`, `Competitive Analysis`, `Strategic Positioning`, `Keyword Opportunity`, `Site Architecture and Content Plan`, `Growth Strategy` (with `### Phase 1`, `### Phase 2`, `### Phase 3`, `### Trajectory` subsections), `Measurement and Next Steps`. Every section ends with a line `Source: path; path` naming the files it came from.
- `blueprint/<slug>/<slug>-am-briefing.md` (internal, one page, at most 500 words): `Executive Summary` (3 to 5 bullets), `Key Strategic Bets` (3 or 4), `Numbers the AM Should Know`, `Anticipated Client Questions` (5, as `1. Q: ...` with an `A: ...` line under each), `Calibration Framing`.

## Running the script

Run each command as its own plain `python3` command with paths as arguments: no `cd`, no `&&`, no pipes. If a command is denied, retry that exact plain command once before doing anything else; never hand-compute what the script does. Read files with the file-reading tool, not shell commands. `<skill-folder>` below is this skill's own folder (where this SKILL.md is); write its real path into the command. Run from the client's working folder, or pass `--root <working folder>`.

## Workflow

1. **Scaffold.** `python3 <skill-folder>/scripts/blueprint.py scaffold --slug <slug>` writes both files with every section, a pre-filled `Source:` line per section and `[WRITE: ...]` placeholders. Keyword Opportunity and Site Architecture and Content Plan are already filled from the reports. It prints which inputs it found; a missing input is printed `MISSING`. Add `--client-slug` when there are several kit folders, and `--keywords`, `--sitemap`, `--competitors` to point at a specific report. `--agency` sets the `Prepared by:` line (default `WISE Digital Partners`). It will not overwrite existing files without `--force`.
2. **Read the inputs**, then read `references/section-guide.md` for what each section holds.
3. **Write the prose sections** in place of each `[WRITE: ...]`, in order, leaving Executive Summary for last. Do not edit the tables in the two copied sections; a sentence of commentary above them is fine. Edit each section's existing `Source:` line in place to name the files that section actually drew on; a section has exactly one `Source:` line, never a second one added below it.
4. **Write the AM Briefing** from the finished Blueprint only.
5. **Check.** `python3 <skill-folder>/scripts/blueprint.py check --slug <slug>` (same input flags as scaffold). Fix every `FAIL` row in the files, never by loosening a figure into vagueness the source does not support, and run it again. `references/checks.md` says what each row tests and how to fix it. Stop when the result is `PASS`, or `NEEDS_INPUT` with only genuine gaps left.
6. **Answer** with the two paths, the check's final `RESULT:` line copied exactly (`RESULT: PASS`, `RESULT: NEEDS_INPUT` or `RESULT: FAIL`), and each open `[NEEDS INPUT: ...]` flag with who can supply it.

## Rules

- **Figures come from files.** Every number in a section (counts of 10 and above, any decimal, price or percentage) must appear in a file named on that section's `Source:` line, or in the two copied sections. No sums, averages, growth projections or invented targets. A directional trajectory says what should move and in which direction, not by how much.
- **Quote, don't rewrite.** Positioning, mission, differentiators, voice and audiences live in the Reference Kit: quote them (`> ` lines, verbatim) and explain what they mean for the site. Client language comes from the quote bank, verbatim.
- **The source wins.** The page count is the sitemap report's number held to the context's `SOW pages:` cap, never a number the client asked for on a call. A `CONFLICT:` in the Blueprint Input Package is reported as decided by the scope, not re-opened.
- **Missing input is visible.** No competitor report, no keyword data or no page cap becomes a `[NEEDS INPUT: what, from whom]` line in that section, and its `Source:` line says `none` when nothing was used.
- **Client-facing.** The Blueprint is read by the client: plain sentences, no internal terms (AM, funnel codes, P0 to P3, tool names, file slugs). Internal notes go in the AM Briefing.
- **No promises.** No guaranteed rankings, positions, traffic or lead numbers, and no timeline the client asked for unless the sources commit to it.

## References

- `references/section-guide.md`: read at step 2. What goes in each Blueprint section and each AM Briefing section, with the source to draw each from.
- `references/checks.md`: read at step 5, or whenever a check row fails. Every check, its rule, and the usual fix.
