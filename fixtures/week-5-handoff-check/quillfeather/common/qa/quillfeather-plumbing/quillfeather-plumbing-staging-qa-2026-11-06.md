Client: Quillfeather Plumbing
Checked: 2026-11-06
Staging: https://quillfeather.staging-wise.site (saved pages: staging-final/)
Dev handoff index: handoff/quillfeather-plumbing/quillfeather-plumbing-dev-handoff-index.md (GO)
Design QA and dev prep: design/quillfeather-plumbing/quillfeather-plumbing-design-qa-devprep.md
Compared with: qa/quillfeather-plumbing/quillfeather-plumbing-staging-qa-2026-11-02.md
Screenshots: none (turned off (--no-screens))

# Staging QA: Quillfeather Plumbing

## Summary

Pages checked: 5 of 5 Build pages (0 missing on staging); skipped (not Build): 1
Open findings: 0 CRITICAL, 1 MAJOR, 0 MINOR
By department: Content 0, SEO 1, Design 0, Development 0
Re-run: 8 FIXED, 1 OPEN, 0 NEW
AM items: 0
Launch toggles: 6
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-dcc6e684 | /services/drain-cleaning/ | SEO | MAJOR | The image /wp-content/uploads/drain-header.webp has no alt text. | Add alt text that says what the image shows. |

## Re-run Status

| Finding ID | Status | Page URL | Department | Severity | Finding |
|---|---|---|---|---|---|
| QA-dcc6e684 | OPEN | /services/drain-cleaning/ | SEO | MAJOR | The image /wp-content/uploads/drain-header.webp has no alt text. |
| QA-65f2ee1c | FIXED | /services/drain-cleaning/ | Content | CRITICAL | The section "Do you inspect the main line with a camera?" is missing. |
| QA-d1bfad17 | FIXED | /services/water-heater-repair/ | Development | CRITICAL | The page is missing on staging (not in the saved pages). |
| QA-2fd83d99 | FIXED | /contact/ | Content | CRITICAL | The phone number 503-555-0174 does not match the client's number (503-555-0147). |
| QA-81660a68 | FIXED | / | SEO | MAJOR | The link to /about/ with the text "Meet the crew" is missing. |
| QA-2cf94f4a | FIXED | / | Development | MAJOR | The link to /services/water-heater-repair/ is broken: that page is not on staging. |
| QA-d7e9d0c5 | FIXED | /services/drain-cleaning/ | Development | MAJOR | The link to /services/water-heater-repair/ is broken: that page is not on staging. |
| QA-76c273e5 | FIXED | /about/ | SEO | MAJOR | The meta title is "About Us \| Quillfeather Plumbing"; the approved title is "About Quillfeather Plumbing \| Portland Plumbers Since 2012". |
| QA-9b522990 | FIXED | /contact/ | Development | MAJOR | 1 link(s) or image(s) in the page content still point at the staging domain: https://quillfeather.staging-wise.site/services/drain-cleaning/. |

## Launch Toggles

- /: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /services/drain-cleaning/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /services/water-heater-repair/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /about/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /contact/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- 4 theme, menu or file URL(s) use the staging domain (for example https://quillfeather.staging-wise.site/about/). Switch the site URL to the live domain at launch and re-check. (Development)

## AM Items

For the Account Manager's review. Not sent to BugHerd.

- none

## Not Checked

- Saved pages from staging-final: HTTPS, HTTP status of other links and image loading were not checked.
- Winter Pipe Guide (/blog/winter-pipe-guide/) skipped: priority Post-Launch.

RESULT: CONDITIONAL
