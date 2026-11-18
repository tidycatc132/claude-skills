---
name: retainer-roadmap
description: Writes a launched website's three-month SEO/GEO roadmap for the monthly retainer, then turns its Month 1 into ClickUp tasks. Roadmap mode reads the Growth Blueprint, keyword calendar, competitor authority gaps, dev handoff index, staging QA, launch check, BugHerd deferrals and Week 5 Scope Changes; a script builds the task table, each row with a Source, plus launch carry-over tasks. Month 1 mode, after close-out, adds items deferred since and creates the Month 1 ClickUp tasks only after SEO approves a preview. Use when asked for an SEO roadmap, GEO roadmap, post-launch roadmap, Month 1 tasks, the transition to the monthly retainer, or to put Month 1 in ClickUp. Do NOT use for the Growth Blueprint (use growth-blueprint), keyword research (use keyword-research), staging QA or the launch check (use staging-site-qa), drift snapshots (use seo-drift-monitor), the close-out package or transition email (use project-close-out), or logging an agent's progress in ClickUp (use clickup-progress-sync).
---

# Retainer roadmap

The plan the SEO team works from after a website build launches. Two modes, run at two moments:

- **Roadmap** (launch week, board card "SEO/GEO roadmap"): writes `roadmap/<slug>/<slug>-seo-roadmap.md`.
- **Month 1** (after close-out, card "transition to monthly retainer"): writes `roadmap/<slug>/<slug>-month-1-tasks.md` and the recorded plan `roadmap/<slug>/<slug>-clickup-tasks.json`, then, after SEO says go, creates the tasks in ClickUp.

All paths are relative to the client's working folder. `<slug>` is the client's folder name (for example `larkspur-dental`). Every step runs `scripts/roadmap.py` as a plain `python3` command from the working folder; if one is refused, retry the same plain command once before doing anything else, and never hand-build a table the script builds.

## Inputs

| File | What is read | Needed |
|---|---|---|
| `blueprint/<slug>/<slug>-growth-blueprint.md` | `Client:`, the `Keyword Opportunity` tiers (Tier 1 = build pages, Tier 2, Tier 3), `### Phase 2`, `### Phase 3`, the sitemap table, `Source:` lines | yes |
| `handoff/<slug>/<slug>-dev-handoff-index.md` | `- URL:` and `- Priority:` of each page (`Build` pages were launched; `Post-Launch` and other pages were not), the `### Redirects` table (`NO TARGET` rows) | yes |
| keyword report (named in the Blueprint's `Source:` line, else the newest in `research/keyword-research/`) | the content calendar: `Month`, `Page`, `Primary keyword`, `Format`, `Why now` | if it exists |
| competitor report (Blueprint `Source:` line, else newest in `seo-reports/competitor-analysis/`) | the `Referring domains` row of the landscape table; review, citation, listing and link lines | if it exists |
| newest `qa/<slug>/<slug>-staging-qa-<date>.md` + `qa/<slug>/<slug>-bugherd-status.json` (written at the Week 5 sweep by week-5-handoff-check) | `## Findings` rows; the status file's `read_on` and `tasks`, with BugHerd `status` and `deferred` per `finding_id` | if they exist |
| newest `qa/<slug>/<slug>-launch-check-<date>.md` + `qa/<slug>/<slug>-launch-bugherd-tasks.json` | `Live:`, `## Findings` (still open on the live site), `## Re-run Status` (`FIXED` rows), `RESULT:`; the task list's `tasks` for each finding's BugHerd id | if it exists |
| every `feedback/<slug>/<date>-feedback.md` whose `Week:` line is 5 | `Class` rows marked `Scope Change`, their Action and `PM/AM:` note | if they exist |

Roadmap mode stops if the Blueprint or the dev handoff index is missing. Pass `--keywords <path>` or `--competitors <path>` (or `none`) to pick a report the Blueprint does not name.

## Roadmap mode

1. `python3 <skill>/scripts/roadmap.py scaffold --slug <slug> --date <today>`. It refuses to overwrite a roadmap that already exists (SEO may have edited it); rebuild with `--force` only when asked.
2. Open the file. Write the `## Summary`: three to five sentences for the retainer team on what launched, what Month 1 finishes and starts, and what Months 2 and 3 build on, taken from the Blueprint's `### Phase 2` and `### Phase 3`. No numbers the files don't contain.
3. Replace every `[WRITE: ...]` task with a short task name for the evidence beside it (a review drive, a citation push, a listing clean-up). Set its Owner. If the evidence is already covered by another row, delete the row and add `- <its Source>: covered by <task>` under `## Not Planned`.
4. Adjust months, priorities and hours where the Blueprint or the user gives a reason. Keep every Source as written. To drop a task, move its Source to `## Not Planned` with the reason. You may add rows; each needs a Source naming a real file and row.
5. `python3 <skill>/scripts/roadmap.py check roadmap/<slug>/<slug>-seo-roadmap.md` until it prints `CHECK PASS`, and say so in your answer with the task count per month.

How each task is made, the table rules and the defaults (months, priorities, hours) are in `references/roadmap-format.md`. Read it before editing rows or when check fails.

## Month 1 mode

1. Run `python3 <skill>/scripts/roadmap.py month1 --slug <slug> --date <today> [--list "<ClickUp list name>"]`. The list defaults to the client's name in the `Client Monthly Work` space. It checks the roadmap's rows itself. Do not run `check` on the roadmap first: items raised since the roadmap make that full check report them as missing, which is expected here, and month1 adds them.
2. Put the preview in your answer: every Month 1 task as a table with its number, name, priority, estimated time and owner (from the task list file), then what was added since the roadmap and what was left out (fixed since, or already done). A summary is not a preview: the SEO approves the list they can see. Ask the SEO to approve it. **Stop here until they say go.** If no ClickUp connector is in the session, say so and stop with the plan written.
3. After the go: find the list with the ClickUp connector (by name in `Client Monthly Work`, or the list the SEO names), create each task in the plan with `clickup_create_task` using its `args` and the list id, in plan order, then record the ids: `python3 <skill>/scripts/roadmap.py created roadmap/<slug>/<slug>-clickup-tasks.json --list-id <id> --approved-by "<role>" --task 1=<id> --task 2=<id> ...`.

Details, the plan's JSON shape and what a re-run does are in `references/month-1.md`. Read it before step 3.

## Rules

- Every task has a Source naming the file and row it came from, or `launch carry-over`.
- Month 1 always holds the six launch carry-over tasks: submit the sitemap to Search Console and Bing, request indexing for the homepage and top priority pages, confirm GA4 and Search Console, baseline with seo-drift-monitor, Core Web Vitals, the Google Business Profile link. If SEO says one is already done, start its Description with `Already done` and set its hours to 0; Month 1 mode leaves it out.
- No keyword that is a build page's main keyword (Blueprint Tier 1) is planned as new content. Improving the launched page is a `Refresh` task.
- The roadmap and the ClickUp tasks never include a structured data, schema or rich-result task; check fails on those words.
- Owners are roles (`SEO`, `Content`, `AM`, `Dev`), never names. Assignees are chosen in ClickUp by the SEO, not stored in files.
- Nothing is written to ClickUp before the SEO approves the preview in this conversation.
