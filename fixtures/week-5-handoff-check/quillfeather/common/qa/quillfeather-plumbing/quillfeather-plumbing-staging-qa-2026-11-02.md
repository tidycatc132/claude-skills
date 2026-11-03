Client: Quillfeather Plumbing
Checked: 2026-11-02
Staging: https://quillfeather.staging-wise.site (saved pages: staging/)
Dev handoff index: handoff/quillfeather-plumbing/quillfeather-plumbing-dev-handoff-index.md (GO)
Design QA and dev prep: design/quillfeather-plumbing/quillfeather-plumbing-design-qa-devprep.md
Compared with: none (first run)
Screenshots: none (turned off (--no-screens))

# Staging QA: Quillfeather Plumbing

## Summary

Pages checked: 4 of 5 Build pages (1 missing on staging); skipped (not Build): 1
Open findings: 3 CRITICAL, 6 MAJOR, 0 MINOR
By department: Content 2, SEO 3, Design 0, Development 4
AM items: 0
Launch toggles: 5
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-65f2ee1c | /services/drain-cleaning/ | Content | CRITICAL | The section "Do you inspect the main line with a camera?" is missing. | Add the "Do you inspect the main line with a camera?" section from the approved page content. |
| QA-d1bfad17 | /services/water-heater-repair/ | Development | CRITICAL | The page is missing on staging (not in the saved pages). | Build and publish /services/water-heater-repair/ from the approved page content. |
| QA-2fd83d99 | /contact/ | Content | CRITICAL | The phone number 503-555-0174 does not match the client's number (503-555-0147). | Change it to 503-555-0147. |
| QA-81660a68 | / | SEO | MAJOR | The link to /about/ with the text "Meet the crew" is missing. | Add the link to /about/ with the text "Meet the crew". |
| QA-2cf94f4a | / | Development | MAJOR | The link to /services/water-heater-repair/ is broken: that page is not on staging. | Publish /services/water-heater-repair/ or remove the link. |
| QA-dcc6e684 | /services/drain-cleaning/ | SEO | MAJOR | The image /wp-content/uploads/drain-header.webp has no alt text. | Add alt text that says what the image shows. |
| QA-d7e9d0c5 | /services/drain-cleaning/ | Development | MAJOR | The link to /services/water-heater-repair/ is broken: that page is not on staging. | Publish /services/water-heater-repair/ or remove the link. |
| QA-76c273e5 | /about/ | SEO | MAJOR | The meta title is "About Us \| Quillfeather Plumbing"; the approved title is "About Quillfeather Plumbing \| Portland Plumbers Since 2012". | Set the meta title to "About Quillfeather Plumbing \| Portland Plumbers Since 2012". |
| QA-9b522990 | /contact/ | Development | MAJOR | 1 link(s) or image(s) in the page content still point at the staging domain: https://quillfeather.staging-wise.site/services/drain-cleaning/. | Change them to relative links or the live domain. |

## Launch Toggles

- /: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /services/drain-cleaning/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /about/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- /contact/: noindex on staging. Remove it at launch so the page can be indexed. (Development)
- 4 theme, menu or file URL(s) use the staging domain (for example https://quillfeather.staging-wise.site/about/). Switch the site URL to the live domain at launch and re-check. (Development)

## AM Items

For the Account Manager's review. Not sent to BugHerd.

- none

## Not Checked

- Saved pages from staging: HTTPS, HTTP status of other links and image loading were not checked.
- Winter Pipe Guide (/blog/winter-pipe-guide/) skipped: priority Post-Launch.

RESULT: NOT READY
