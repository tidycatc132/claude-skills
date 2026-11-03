Client: Fernhollow Bakery
Checked: 2026-11-05
Staging: https://fernhollow.staging-wise.site
Dev handoff index: handoff/fernhollow-bakery/fernhollow-bakery-dev-handoff-index.md (GO)
Design QA and dev prep: none
Compared with: none (first run)
Screenshots: none (Playwright not available)

# Staging QA: Fernhollow Bakery

## Summary

Pages checked: 4 of 5 Build pages (1 missing on staging); skipped (not Build): 0
Open findings: 1 CRITICAL, 1 MAJOR, 0 MINOR
By department: Content 0, SEO 1, Design 0, Development 1
AM items: 2
Launch toggles: 4
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-0c3d77e1 | /catering/ | Development | CRITICAL | The page is missing on staging. | Build and publish /catering/ from the approved page content. |
| QA-5fa2b810 | /custom-cakes/ | SEO | MAJOR | The meta description is missing; the approved description is "Custom cakes baked from scratch in Spokane for birthdays, weddings and every day in between." | Set the meta description to the approved text. |

## Launch Toggles

- 4 pages: noindex on staging. Remove it at launch so the pages can be indexed. (Development)

## AM Items

For the Account Manager's review. Not sent to BugHerd.

- The client still owes the catering menu prices for the catering page.
- The client asked on the kickoff call about an online ordering cart, which is not in the signed scope.

## Not Checked

- Saved pages from staging: HTTPS, HTTP status of other links and image loading were not checked.

RESULT: NOT READY
