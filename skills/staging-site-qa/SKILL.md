---
name: staging-site-qa
description: Runs the pre-launch QA of a website build's staging site against the build's own files (dev handoff index, written pages, design asset checklist, client context), comparing each page's titles, H1, sections, CTA, internal links and contact details with the approved values, and turns every issue into a BugHerd task for the department that fixes it (Content, SEO, Design, Development), plus an AM list. Use when the PM asks to QA the staging site, run QA automation on staging, do staging QA for a client, check staging pages against the dev handoff index, send the QA issues to BugHerd, or re-run QA after fixes to see what is fixed or new. Works from the staging URL or saved page HTML. Do NOT use for live-site technical SEO audits (use technical-seo-checker), post-launch snapshots (use seo-drift-monitor), building the dev index (use dev-handoff-index), checking design templates before dev (use design-qa-dev-prep), the client's staging edits (use client-feedback), or the staging link email (use week-5-client-email).
---

# Staging site QA

One QA pass over the staging site, run by the PM, that covers every department. A script compares each Build page on staging with the values the build already approved, so most findings are exact mismatches, not opinions. BugHerd is the punch list: each finding becomes one task in its department's column, created only after the PM has seen the preview.

## Inputs

All paths are relative to the client's working folder; `<slug>` is the client folder name (for example `quillfeather-plumbing`).

| Input | Required | What is read |
|---|---|---|
| Staging base URL | yes | The site root (not a subfolder); every Build page is fetched from it. Basic auth user and password may be given at run time; they are passed to the script and never written to any file. |
| Saved pages folder | when staging can't be reached from here | Page HTML saved as `<folder>/index.html`, `<folder>/about/index.html` and so on. The base URL is still needed, to spot staging-domain links. |
| `handoff/<slug>/<slug>-dev-handoff-index.md` | yes | Each page's `Page`, URL, `Content file`, `Meta title`, `Meta description`, `H1`, `Internal links` (with anchors) and `Priority`. Only `Build` pages are checked. |
| `content/<url-slug>/article.md` | yes, per page | H2 sections in order, and the call to action: the links in the `<!-- section: Final CTA -->` section (else the last H2 section before `## Sources`). |
| `design/<slug>/<slug>-design-qa-devprep.md` | if it exists | `## Asset Checklist`, mainly `### Images`, and its `RESULT:` line. |
| `kickoff/<slug>/<slug>-context.md` | yes | Phone numbers, email addresses, street address and the `Website:` line (the production domain for canonicals). |
| `qa/routing.md` | if it exists | Department to BugHerd column and assignee, and a `BugHerd project:` line. Format in `references/report-format.md`. |

If the index or the context is missing, the script stops and says which skill makes it. Run that first.

## Outputs

- `qa/<slug>/<slug>-staging-qa-<YYYY-MM-DD>.md`: summary counts by severity and department, the findings table `| # | Page URL | Department | Severity | Finding | Fix |` (the `#` cell is the stable `finding_id`), `## Re-run Status` on a re-run, `## Launch Toggles`, `## AM Items`, `## Not Checked`, and a last line `RESULT: READY`, `RESULT: CONDITIONAL` (MAJOR open, no CRITICAL) or `RESULT: NOT READY` (any CRITICAL).
- `qa/<slug>/<slug>-bugherd-tasks.json`: one object per finding with `finding_id`, `status` (`NEW`, `OPEN`, `FIXED`), `create`, `bugherd_task_id` (filled once the task exists), `page_url`, `department`, `column`, `assignee`, `severity`, `bugherd_severity`, `title`, `description`. AM items are never in it.
- `qa/<slug>/<slug>-qa-scan.json` (the script's working file) and `qa/<slug>/screens/` (desktop and mobile screenshots, when Playwright is available).

Load `references/report-format.md` when you need the exact layout of these files, and `references/checks.md` when you explain why a finding has its department or severity.

## Steps

Run the scripts as plain `python3` commands from the working folder. If a command is refused, retry the same plain `python3` command once; never redo a script's checks by hand.

1. **Scan.**
   `python3 <skill-folder>/scripts/qa.py scan --slug <slug> --base-url <staging URL>` and add `--saved <folder>` for saved pages, `--user <u>` for a protected staging site with the password in the `STAGING_PASSWORD` environment variable (or `--password <p>` if the shell can't set one; it is never saved), `--date YYYY-MM-DD` when the user gives the run date. If it prints `STOP`, tell the user exactly what it said, write nothing else and end there: never guess findings for a site you could not load.
2. **Look at the screenshots** (only if the scan says it took them). Open each file in `qa/<slug>/screens/` and note only problems you can see: broken or missing images, overlapping or cut-off text, a layout that breaks on mobile, an empty block. If the scan took no screenshots, you add no Design findings from looking. The asset checklist comparison (images whose size or format differs from `### Images`) may use the `images` list in the scan file.
3. **Write review notes** only if you have Design findings or AM items to add: `qa/<slug>/<slug>-review-notes.md`, format in `references/report-format.md`. Every Design row names its evidence: a screenshot path from this scan, or `asset checklist: <the exact checklist line>`. AM items are things for the Account Manager, not for a department: missing client content, scope questions, decisions the client must make. Budget or scope notes go here and never into a finding.
4. **Report.** `python3 <skill-folder>/scripts/qa.py report --slug <slug>` (same `--date` as the scan). It merges the notes, compares with the newest earlier report by `finding_id`, writes both files and runs `check`. If check fails, fix the cause (usually a notes row) and run report again; never edit the report by hand.
5. **Show the PM the preview.** Give the result line and the counts, then name each CRITICAL finding in one line as what blocks launch, then the tasks that will be created (`create: true`) grouped by department and column, with the assignee. Name any department without an assignee. Then stop and wait for the PM's go. Do not create anything before it.
6. **Create the BugHerd tasks** after the PM says go: follow `references/bugherd.md`. Only `create: true` objects become tasks. Then record the ids BugHerd returned: `python3 <skill-folder>/scripts/qa.py created --slug <slug> QA-xxxxxxxx=<task id> ...`. Later runs carry those ids forward and never create a task that already has one. Tell the PM how many were created per column and list any `FIXED` findings whose BugHerd tasks they can close.

## Re-run after fixes

Run the same steps with the new date. In the preview, give the open total as OPEN plus NEW (for example "3 open: 2 still open from last time, 1 new") so it reads the same as the summary counts. The report marks every finding `FIXED`, `OPEN` or `NEW` against the newest report dated before this run, and only `NEW` findings with no `bugherd_task_id` get `create: true`. A second run on the same day overwrites that day's report and compares with the same earlier report; the recorded task ids are what stop it creating tasks twice, so always run `created` after step 6, and never delete or replace the task file between runs. A finding that was FIXED and comes back is a regression: it is NEW, and its old id is dropped so a new task is offered.

## Rules

- Findings come from the script, the screenshots or the asset checklist. Nothing else, and no guessing from HTML about how a page looks.
- One department per finding: Content, SEO, Design or Development. Account Management has no BugHerd task; its items stay in `## AM Items`.
- `noindex` on staging is a launch toggle for Development, never a finding. So are a staging robots.txt that blocks crawlers, a canonical on the staging domain with the right path, and theme or menu URLs that follow the site URL setting.
- Structured data, accessibility audits and chat widgets are not part of this QA. The report says `Structured data: not in the current process` once.
- Clients can be guests on the BugHerd project, so task text stays plain and client-safe. The check rejects internal words such as budget or scope change in task text.
- Assignee names live only in the client's `qa/routing.md` or come from the PM; never write them anywhere else.
