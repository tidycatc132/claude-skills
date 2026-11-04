Client: Quillfeather Plumbing
Checked: 2026-11-17
Dev handoff index: handoff/quillfeather-plumbing/quillfeather-plumbing-dev-handoff-index.md
Staging QA: qa/quillfeather-plumbing/quillfeather-plumbing-staging-qa-2026-11-17.md (RESULT: NOT READY)
BugHerd status: qa/quillfeather-plumbing/quillfeather-plumbing-bugherd-status.json (read 2026-11-17, BugHerd connector)
Week 5 email: emails/quillfeather-plumbing/quillfeather-plumbing-week-5-email.md
Client edits: feedback/quillfeather-plumbing/2026-11-12-feedback.md
AM review: qa/quillfeather-plumbing/quillfeather-plumbing-am-review.md

# Week 5 final sweep: Quillfeather Plumbing

## Checks

| # | Check | Result | Detail | Owner |
|---|---|---|---|---|
| 1 | Dev handoff index | PASS | handoff/quillfeather-plumbing/quillfeather-plumbing-dev-handoff-index.md ends GO | PM |
| 2 | Staging QA re-run | PASS | qa/quillfeather-plumbing/quillfeather-plumbing-staging-qa-2026-11-17.md: re-run, 0 FIXED, 1 OPEN, 2 NEW (RESULT: NOT READY) | PM |
| 3 | Open CRITICAL | FAIL | 1 open: QA-daf2e19b (CRITICAL cannot be deferred) | Content |
| 4 | Open MAJOR | FAIL | 2 open and not deferred: QA-81660a68, QA-dcc6e684 | SEO |
| 5 | BugHerd tasks | FAIL | 1 problem(s); 8 done, 0 deferred or post-launch | PM |
| 6 | Week 5 email | PASS | sent 2026-11-10, reply by 2026-11-13 | AM |
| 7 | Client edits | PASS | feedback/quillfeather-plumbing/2026-11-12-feedback.md: 4 edit(s) classed (1 Mechanical, 1 Strategic, 1 Scope Change, 1 Approval); 1 Scope Change(s) with PM/AM notes | AM |
| 8 | AM sign-off | PASS | qa/quillfeather-plumbing/quillfeather-plumbing-am-review.md: Riley Shaw, 2026-11-09 | AM |

## Blocking

- QA-daf2e19b /services/water-heater-repair/: Placeholder text is on the page: "Lorem ipsum". CRITICAL, must be fixed before launch. No BugHerd task yet: create it. (owner: Content)
- QA-81660a68 /: The link to /about/ with the text "Meet the crew" is missing. MAJOR, fix it or have the PM defer it with a reason. No BugHerd task yet: create it. (owner: SEO)
- QA-dcc6e684 /services/drain-cleaning/: The image /wp-content/uploads/drain-header.webp has no alt text. MAJOR, fix it or have the PM defer it with a reason. BugHerd #25: 'SEO Review'. (owner: SEO)
- BugHerd #31 (CE-66f3ebb0) "/contact/: Change the opening hours to 7 to 6 on weekdays" is still 'Copy Review' in BugHerd (owner: Content)

## Carried to Post-Launch

- none

## Scope Changes

- #3 site-wide: Discuss an online booking calendar. PM/AM: Online booking is new functionality beyond the SOW; quote it as a change order or plan it after launch

## Close in BugHerd

- none

## Notes

- Not checked by the QA re-run: Saved pages from staging-after: HTTPS, HTTP status of other links and image loading were not checked.
- Not checked by the QA re-run: Winter Pipe Guide (/blog/winter-pipe-guide/) skipped: priority Post-Launch.

NO-GO
