Client: Quillfeather Plumbing
Checked: 2026-11-17
Staging: https://quillfeather.staging-wise.site (saved pages: staging-after/)
Dev handoff index: handoff/quillfeather-plumbing/quillfeather-plumbing-dev-handoff-index.md (GO)
Design QA and dev prep: design/quillfeather-plumbing/quillfeather-plumbing-design-qa-devprep.md
Compared with: qa/quillfeather-plumbing/quillfeather-plumbing-staging-qa-2026-11-06.md
Screenshots: none (turned off (--no-screens))

# Staging QA: Quillfeather Plumbing

## Summary

Pages checked: 5 of 5 Build pages (0 missing on staging); skipped (not Build): 1
Open findings: 1 CRITICAL, 2 MAJOR, 0 MINOR
By department: Content 1, SEO 2, Design 0, Development 0
Re-run: 0 FIXED, 1 OPEN, 2 NEW
AM items: 0
Launch toggles: 6
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-daf2e19b | /services/water-heater-repair/ | Content | CRITICAL | Placeholder text is on the page: "Lorem ipsum". | Replace it with the approved page content. |
| QA-81660a68 | / | SEO | MAJOR | The link to /about/ with the text "Meet the crew" is missing. | Add the link to /about/ with the text "Meet the crew". |
| QA-dcc6e684 | /services/drain-cleaning/ | SEO | MAJOR | The image /wp-content/uploads/drain-header.webp has no alt text. | Add alt text that says what the image shows. |

## Re-run Status

| Finding ID | Status | Page URL | Department | Severity | Finding |
|---|---|---|---|---|---|
| QA-daf2e19b | NEW | /services/water-heater-repair/ | Content | CRITICAL | Placeholder text is on the page: "Lorem ipsum". |
| QA-81660a68 | NEW | / | SEO | MAJOR | The link to /about/ with the text "Meet the crew" is missing. |
| QA-dcc6e684 | OPEN | /services/drain-cleaning/ | SEO | MAJOR | The image /wp-content/uploads/drain-header.webp has no alt text. |

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

- Saved pages from staging-after: HTTPS, HTTP status of other links and image loading were not checked.
- Winter Pipe Guide (/blog/winter-pipe-guide/) skipped: priority Post-Launch.

RESULT: NOT READY
