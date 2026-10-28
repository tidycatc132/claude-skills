# Week 1 checklist

What `scripts/handoff_check.py run` checks, in report order. Paths are relative to the working folder; `<slug>` is the kickoff folder name. "Incomplete" means the file exists but lacks what the column says, and is reported as `missing` with the lack in the note. Each item's owner (person and producing skill) is in the note of a failing row.

| Item | Required | Looked for at | Complete when | Stale when |
|---|---|---|---|---|
| Client context | yes | `kickoff/<slug>/<slug>-context.md` | has `## Snapshot`, `## Scope Summary`, `## Open Items`, `## Sources` and a `SOW pages:` line | a `<slug>-call-updates.md` exists but the change log has no row whose Source starts `call` |
| URL inventory | yes | `kickoff/<slug>/<slug>-url-inventory.csv` | header is exactly `url`, `title`, `page_type`, `status`, `source` (no rows is fine: no website) | |
| Gap questions | yes | `kickoff/<slug>/<slug>-gap-questions.md` | not empty | |
| Project instructions | yes | `kickoff/<slug>/<slug>-project-instructions.md` | not empty | |
| Setup checklist | yes | `kickoff/<slug>/<slug>-setup-checklist.md` | not empty | |
| Paid media brief | only when the setup checklist has new-build-kickoff's `Send the paid media brief to Paid Media` item (added only when paid media is signed scope); else `n/a` | `kickoff/<slug>/<slug>-paid-media-brief.md` | not empty | |
| Welcome email | yes | `welcome-email/<slug>/<slug>-welcome-email.md` | has a `Subject:` line | |
| Change log | yes | `kickoff/<slug>/<slug>-change-log.md` | has the `| Date | Source | Section | Change | Before | After |` table with at least one row (gap responses were processed) | |
| Missing items | yes | `kickoff/<slug>/<slug>-missing-items.md` | has `## Intake Items`, `## Platform Access`, `## Kickoff Call Agenda` | |
| Platform access confirmed | no | the missing items' `| Platform | Status | Note |` table | every platform is `confirmed` or `n/a`; the note lists the rest | |
| Kickoff Call brief | yes | `kickoff/<slug>/<slug>-kickoff-call-brief.md` | has its six sections, `## Call Goals` to `## Relationship Notes` | |
| Call updates | yes | `kickoff/<slug>/<slug>-call-updates.md` | has `Source: call` and `## Updates` | |
| Blueprint Input Package | yes | `kickoff/<slug>/<slug>-blueprint-input-package.md` | has its nine sections, `## Services Priority` to `## Open Items` | |
| Quote bank | yes | `kickoff/<slug>/<slug>-quote-bank.md` | has the `| # | Quote | Speaker | Timestamp | Use for |` table | |
| Reference Kit (one row per file) | yes | `client-reference/<client-slug>/` `brand.md`, `voice.md`, `style.md`, `audience.md`, `compliance.md`; the only folder there, or `--kit` | each has `## Sources` | |
| Keyword research | yes | the last-named `research/keyword-research/*.md` | has a `targets:` block | |
| Sitemap within scope page cap | yes | the last-named `seo-reports/site-structure-optimizer/*.md` with a `countable pages N / SOW cap M` line | that line exists (the last one counts, after any trimming) and N is at most M; over the cap is reported `missing` | the cap differs from the context's `SOW pages:` number, or the report's cap is `Unknown` while the context now has a number |
| Homepage content brief | yes | `research/content-briefs/*.md` with front-matter `format: homepage` (older `.vN.md` copies skipped) | `status` is `DONE` or `DONE_WITH_CONCERNS` | |
| Homepage content | yes | `content/home/`, else the one `content/*/` whose `article.md` has `<!-- section: Hero -->`, or `--content` | `article.md`, `article.html`, `handoff.md` all exist and the `VERDICT:` (from `handoff.md`, else `qa/<url-slug>/qa_report.md`, else an older page's `qa_report.md` in its folder) is `READY` or `NEEDS_INPUT`; the note counts open client flags | |
| Editorial sign-off | yes | the design brief's `Content review:` line, or `--signoff` from the user | the line starts `confirmed` | |
| Homepage design brief | yes | `design/<slug>/<slug>-homepage-design-brief.md` | has its ten sections, `## Goals` to `## Sources` | its Section Map rows do not match the article's `<!-- section: ... -->` markers, in order (when either side has none, the note says the map was not compared) |
| Homepage wireframe | no | `design/<slug>/<slug>-homepage-wireframe.html` | exists; else `n/a` (optional) | |
| Week 1 client email | yes | `emails/<slug>/<slug>-week-1-email.md` | has `Subject:` and a `Design options:` block with at least 2 `<name>: <link>` lines | |
| Client feedback | no | the last-named `feedback/<slug>/*-feedback.md` | exists; absent is listed but never blocks | a `*-feedback-updates.md` file is not named in any change log Source |

## Choices behind the rules

- The scope page cap: with `SOW pages: unknown` (no page count in the scope source) and a report cap of `Unknown`, the sitemap row is `present` with a note that the AM confirms the page count. The check cannot hold a sitemap to a cap nobody signed.
- Editorial sign-off is read from the design brief because homepage-design-brief records it there (`Content review: confirmed (<who>, <date>)`) and the design brief is written after the editorial review.
- Client feedback and platform access are listed so nothing is forgotten, but Week 2 does not wait for them.
