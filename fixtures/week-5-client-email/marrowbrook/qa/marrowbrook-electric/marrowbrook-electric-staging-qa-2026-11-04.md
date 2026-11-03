Client: Marrowbrook Electric
Checked: 2026-11-04
Staging: https://marrowbrook.staging-wise.site
Dev handoff index: handoff/marrowbrook-electric/marrowbrook-electric-dev-handoff-index.md (GO)
Design QA and dev prep: design/marrowbrook-electric/marrowbrook-electric-design-qa-devprep.md
Compared with: none (first run)
Screenshots: qa/marrowbrook-electric/screens/ (12 files)

# Staging QA: Marrowbrook Electric

## Summary

Pages checked: 6 of 6 Build pages (0 missing on staging); skipped (not Build): 1
Open findings: 1 CRITICAL, 2 MAJOR, 0 MINOR
By department: Content 1, SEO 1, Design 0, Development 1
AM items: 1
Launch toggles: 6
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-4b1e09a2 | /contact/ | Content | CRITICAL | The phone number 208-555-0136 does not match the client's number (208-555-0163). | Change it to 208-555-0163. |
| QA-77c0d3f1 | /services/ev-charger-installation/ | SEO | MAJOR | The image /wp-content/uploads/ev-charger.webp has no alt text. | Add alt text that says what the image shows. |
| QA-a90e6c55 | /about/ | Development | MAJOR | 1 link(s) or image(s) in the page content still point at the staging domain: https://marrowbrook.staging-wise.site/contact/. | Change them to relative links or the live domain. |

## Launch Toggles

- 6 pages: noindex on staging. Remove it at launch so the pages can be indexed. (Development)

## AM Items

For the Account Manager's review. Not sent to BugHerd.

- The client has not sent the team photo for the about page.

## Not Checked

- Winter Safety Guide (/blog/winter-safety/) skipped: priority Post-Launch.

RESULT: NOT READY
