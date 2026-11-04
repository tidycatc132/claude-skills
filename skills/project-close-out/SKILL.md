---
name: project-close-out
description: Writes a launched website build's close-out package from the build's own files - the internal project summary with a Build complete table and outstanding items, the client transition email that moves them to the monthly retainer, and the retainer handoff brief for SEO and the AM. A script reads the go-live email, dev handoff index, articles, launch check, staging QA, Week 5 feedback, roadmap and case study, fills every table, and checks the email (under 300 words, real numbers only, no internal terms, no structured data claim). Use when the PM or AM asks to close out the project, for the close-out package, the post-launch transition email, or the retainer handoff brief. Do NOT use for the go-live email (use week-6-go-live-email), the SEO roadmap, the Month 1 task plan or the ClickUp retainer tasks (use retainer-roadmap), the case study (use case-study), the live site check (use staging-site-qa), or the Week 5 go/no-go (use week-5-handoff-check).
---

# Project close-out

The site is live. Before the retainer starts, three things get written: an internal record of what the build delivered and what is still open, an email that tells the client the build is done and what the monthly work looks like, and a brief that lets SEO and the AM pick up the account without asking the PM anything. Every fact is already in a file. `scripts/closeout.py` reads the files and writes every table and list; you write the prose around them, and the script checks the result. Finish only on `RESULT: PASS`.

## Inputs

Paths are relative to the client's working folder; `<slug>` is the client's folder name.

| File | From | Read for | Needed |
|---|---|---|---|
| `kickoff/<slug>/<slug>-context.md` | new-build-kickoff, client-context-update | `Client:`, the `## Snapshot` lines (`Website`, `Service area`, `Primary contact`), any bullet about communication preferences (`prefer`, `communication`) or the Google Business Profile, the `## Goals and Conversion` lines | yes |
| `handoff/<slug>/<slug>-dev-handoff-index.md` | dev-handoff-index | page blocks (`Page`, `URL`, `Content file`, `Priority`) under each page-type group; `### Redirects` (`Old URL`, `New URL`, `Note`) | yes |
| `content/<url-slug>/article.md` | seo-content-writer | words per Build page (the same rule as case-study) | per page |
| `emails/<slug>/<slug>-go-live-email.md` | week-6-go-live-email | header `Client:`, `Launch:` (the launch date), `Pages launching:`, `Integrations:`; any `WARNING:` line | for the launch date |
| newest `qa/<slug>/<slug>-launch-check-<YYYY-MM-DD>.md` | staging-site-qa (launch mode) | `Live:`, `Checked:`, `## Findings`, `RESULT:` (`LIVE OK` or `LIVE ISSUES`) | no |
| newest `qa/<slug>/<slug>-staging-qa-<YYYY-MM-DD>.md` and `qa/<slug>/<slug>-bugherd-status.json` | staging-site-qa, week-5-handoff-check | open `## Findings` rows; `tasks` (`finding_id`, `status`, `deferred`) to skip done items and name deferrals | no |
| `feedback/<slug>/<date>-feedback.md` with `Week: 5` | client-feedback | rows whose `Class` is `Scope Change`, with their `PM/AM:` notes | no |
| `roadmap/<slug>/<slug>-seo-roadmap.md` | retainer-roadmap | the table's `Month`, `Task`, `Priority`, `Est. hours`, `Owner`, `Source`; `## Not Planned` | no |
| `roadmap/<slug>/<slug>-clickup-tasks.json` | retainer-roadmap (Month 1 mode) | `space`, `list`, `tasks[].clickup_task_id` | no |
| `case-study/<slug>/<slug>-case-study.md` | case-study | `Feature consent:`; its check result | no |
| `client-reference/<slug>/voice.md` | client-reference-kit | the Email row of the Tone Matrix | no |
| `blueprint/<slug>/<slug>-growth-blueprint.md` | growth-blueprint | the strategic decisions you summarise | no |

At run time the PM may give: the launch date (`--launch`), the Account Manager's name (`--am`), the reporting and check-in rhythm (`--cadence`, default `a monthly report and a monthly check-in call`) and the ClickUp list (`--clickup-list "Space > List"`). Exactly what each reader takes, and how the Build complete rows are decided: [Package Format](references/package-format.md).

## Outputs

All in `closeout/<slug>/`:

- `<slug>-project-summary.md` (internal): header lines `Client:`, `Launch:`, `Written:`, `Go-live email:`, `Launch check:`, `Roadmap:`, `Case study:`; then `## Build Complete` (`| # | Item | Done | Evidence |`, four rows, `yes` or `no`), `## What We Built` (page inventory), `## Strategic Decisions` (you), `## Content Produced` (words per page), `## Outstanding Items`, `## Roadmap`.
- `<slug>-transition-email.md` (client-facing): header lines `Client:`, `To:`, `Launch:`, `Account manager:`, a blank line, `Subject:`, then the body, under 300 words.
- `<slug>-retainer-handoff.md` (internal): header lines `Client:`, `Launch:`, `Written:`, `Roadmap:`, `ClickUp:`; then `## Client Quick Reference`, `## Month 1 Priorities`, `## Content Status`, `## Google Business Profile`, `## Technical Debt`, `## Communication Preferences`, `## ClickUp Location`.

## Running the script

`<skill-folder>` is the folder this SKILL.md is in; write its real path. Run each command from the client's working folder as one plain `python3` command, nothing chained before or after it (no `cd`, `&&` or pipes). If a call is denied, send the same plain command again. Read files with the file tool. Never count, total or copy by hand what the script does.

## Steps

1. **Run-time facts.** Take from the request the launch date if given, the AM's name, a cadence other than the default, and the ClickUp list if named. Pass only what the PM said.
2. **Scaffold.** `python3 <skill-folder>/scripts/closeout.py scaffold --slug <slug>` plus those options. It prints the counts, the Build complete rows, the outstanding items and any `WARN:` line, and writes the three files with `[WRITE: ...]` slots. It refuses with no launch date (ask the PM) and will not overwrite existing files without `--force`.
3. **Read** the roadmap, the Growth Blueprint and the voice file the scaffold named, then [Transition Email](references/transition-email.md) before writing the email.
4. **Write** every `[WRITE: ...]` slot in place: the summary's Strategic Decisions (3 to 5 bullets, each ending with its source file in brackets), the handoff's Month 1 paragraph, and the email. Never edit a script-made line, table or header.
5. **Check.** `python3 <skill-folder>/scripts/closeout.py check --slug <slug>` with the same options. Fix each `FAIL` in the prose and run it again until `RESULT: PASS`. If the files changed under you (a new launch check, a roadmap written later), run `scaffold --force` and rewrite the prose.
6. **Answer** with the three paths, the Build complete table as written, the outstanding items count and which of them are not in the roadmap, the email's subject, any `WARN:` line, and the check's `RESULT:` line. Say the AM sends the email; you never send it.

## Rules

- **The Build complete table reports; it never stops the package.** A `no` row is listed first in your answer with what closes it (for example, run retainer-roadmap, or close the open launch finding).
- **Numbers come from the files.** Page, word and redirect counts are the script's. Every number in the email is a count, part of the launch date, or appears in the roadmap, the cadence or the go-live email.
- **The client hears only what was built and what the PM named.** No structured data, schema or rich result claims anywhere. No live chat or Juvo unless the go-live email's `Integrations:` names it, even when asked. No internal terms in the email (QA, BugHerd, severities, ClickUp, handoff, deferred, scope change, carry-over, tiers, SOW).
- **No roadmap, no promises.** Without a roadmap the email says the plan for the next three months follows with the first monthly report, and names no tasks.
- **Internal files stay internal.** The summary and handoff may use finding ids and file paths; the email may not.

## Scripts

| Command | Use |
|---|---|
| `scripts/closeout.py scaffold`, `check` | Write the three files; check them (exit 0 PASS, 1 FAIL or refused, 2 usage) |
| `scripts/closeout.py facts` | Print every fact as JSON without writing anything |
| `scripts/closeout.py contract golive|roadmap|index <file>` | Print what is read from a go-live email, a roadmap or a dev handoff index, as JSON; `contract --validate <fixture>` accepts the contract fixtures |
| `scripts/selftest_closeout.py` | Cases on temporary copies of the Larkspur Family Dental fixture; run after changing the script |

Standard-library Python 3 only. The check runs retainer-roadmap's and case-study's own checks when those skills are installed beside this one; otherwise it says so in the Evidence column.
