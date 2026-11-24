# Package format

What `closeout.py` reads from each file, how it decides each script-made line, and what `check` compares. Load this when a Build complete row or an outstanding item looks wrong, or when an input file has an unusual shape.

## Readers

- **Client context** (`kickoff/<slug>/<slug>-context.md`). `Client:`. Under `## Snapshot`, `- Website:`, `- Service area:`, `- Primary contact:` (or `- Contact:`); the name before the first comma is who the email goes to. Every bullet anywhere in the file that mentions `prefer` or `communication` goes under Communication Preferences; every bullet that mentions the Google Business Profile (or `GBP`) goes under Google Business Profile. Lines in `## Goals and Conversion` starting `Main`, `Primary` or `Second` go in the Quick Reference. Trailing source tags (`[transcript]`) are dropped.
- **Dev handoff index** (`handoff/<slug>/<slug>-dev-handoff-index.md`). Each `##` group and its `###` page blocks: `- Page:`, `- URL:`, `- Content file:`, `- Priority:`. A page is built when its `Priority` is `Build` and its content file exists; a `Build` page with no file is left out with a `WARN:`. Other priorities (`Post-Launch`) are listed as not built for launch. From `### Redirects` (`| Old URL | New URL | Note |`), a row with a path in `New URL` counts as redirected unless an open finding on the newest launch check is about that old URL (the redirect does not answer on the live site yet); those are counted apart, so the email never claims them. Any other row (`NO TARGET`) is an outstanding item.
- **Articles** (`content/<url-slug>/article.md`). Words are counted after dropping HTML comments and tags and keeping only link text; each whitespace-separated token with a letter or digit counts. This is case-study's rule, so both files give the same total.
- **Go-live email** (`emails/<slug>/<slug>-go-live-email.md`). The first `YYYY-MM-DD` on its `Launch:` line is the launch date when `--launch` is not given; `Launch: client to confirm` gives none, and the scaffold refuses. `Integrations:` limits which integrations the transition email may name. A `WARNING:` line above the email means it was not cleared.
- **Launch check** (newest `qa/<slug>/<slug>-launch-check-<YYYY-MM-DD>.md`). `Live:` (the live address, else `https://` plus the context's `Website`), `Checked:`, the `## Findings` table (`| # | Page URL | Department | Severity | Finding | Fix |`) and the last `RESULT:` line. The findings table holds only what is still open on that run.
- **Staging QA** (newest `qa/<slug>/<slug>-staging-qa-<YYYY-MM-DD>.md`) and the **BugHerd status file** (`qa/<slug>/<slug>-bugherd-status.json`: `read_on`, and `tasks` with `finding_id`, `status`, `deferred`). A task whose status is `done`, `closed` or `archived` counts as done (week-5-handoff-check's rule; any other status is open). A staging finding done there is skipped; one with a `deferred` reason is "Deferred at the Week 5 sweep"; the rest are "Still open". A launch-check finding marked done in the status file is skipped too. A client-edit task (`CE-` id) in the status file that is not done is an outstanding item, with its deferral reason when it has one.
- **Week 5 feedback** (`feedback/<slug>/<date>-feedback.md` whose `Week:` line is `5`). Rows of `| # | Feedback | Source | Page URL | Class | Department | Action | Task |` whose `Class` is `Scope Change`, with the `- #<n> ...: PM/AM: <note>` line from `## Scope Changes`.
- **Roadmap** (`roadmap/<slug>/<slug>-seo-roadmap.md`). The table `| Month | Task | Description | Priority | Est. hours | Owner | Source |` and the `## Not Planned` lines. An outstanding item is matched to a roadmap row when the row's `Source` names the finding id, the old URL, or the feedback path and `#<n>` as a whole (`#1` does not match `#12`).
- **Month 1 plan** (`roadmap/<slug>/<slug>-clickup-tasks.json`). `space` and `list` give the ClickUp location when `--clickup-list` is not given; `tasks[].clickup_task_id` says how many were created. With neither, the location is `Client Monthly Work > <client>`, marked as a default to confirm.
- **Case study** (`case-study/<slug>/<slug>-case-study.md`). Its header lines `Client:`, `Launch:` and `Feature consent:`; consent goes into the Evidence column.
- **Voice** (`client-reference/<slug>/voice.md`, else the only kit folder with a `voice.md`). The `Email` row of `## Tone Matrix`.

## Build complete rows

| # | Item | `yes` when |
|---|---|---|
| 1 | Go-live email written | the file exists and has no `WARNING:` line on top |
| 2 | Launch check LIVE OK, or every issue closed or deferred | the newest launch check ends `RESULT: LIVE OK` with no CRITICAL or MAJOR still open (a MINOR may stay), or each finding still in its table is done in the BugHerd status file, deferred there, or planned in the roadmap (a row's `Source` names its id). A CRITICAL finding is never counted as deferred, wherever it is planned: it keeps the row at `no` until it is fixed |
| 3 | Roadmap written | the roadmap exists and retainer-roadmap's `roadmap.py check` passes on it |
| 4 | Case study written | the case study exists and case-study's `case_study.py check` ends `RESULT: PASS` |

When retainer-roadmap or case-study is not installed beside this skill, rows 3 and 4 only test that the file exists (and the roadmap table has rows), and the Evidence column says the check script was not found. A `no` row never stops the scaffold or the check.

## Outstanding items

One line each, in this order: staging QA findings not done, launch-check findings not done, client-edit tasks not done, old URLs with no 301 target, then Scope Changes. Each line ends with where it went: `Roadmap Month <n>: "<task>"`, `Roadmap: Not Planned (<reason>)`, `not in the roadmap`, or `not in a roadmap (no roadmap yet)`. The handoff's Technical Debt is the same list without the Scope Changes.

## What `check` compares

- The header lines of all three files against what the scaffold writes now (the `Written:` date is taken from the file).
- Every section with no `[WRITE` slot must be exactly what the scaffold writes now. A section with a slot must keep every script-made line and have prose in place of the slot.
- The summary's Strategic Decisions has 3 to 5 bullets, each ending with `[<path>]` naming a file that exists, and no structured data wording; no `[WRITE` is left anywhere.
- The email rules in [Transition Email](transition-email.md).

If the inputs changed after the scaffold (a launch check re-run, a roadmap written later), the script-made sections no longer match: run `scaffold --force` and write the prose again.
