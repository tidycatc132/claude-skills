Client: Saltmarsh Tree Care
Checked: 2026-11-18
Live: https://saltmarshtreecare.com (saved pages: live/)
Staging domain: saltmarsh.staging-wise.site (qa/saltmarsh-tree-care/saltmarsh-tree-care-staging-qa-2026-11-10.md)
Dev handoff index: handoff/saltmarsh-tree-care/saltmarsh-tree-care-dev-handoff-index.md (GO)
Redirects: 2 of 3 tested answer 301 or 308 to their New URL (from redirects.txt)
Compared with: none (first run)

# Launch Check: Saltmarsh Tree Care

## Summary

Pages checked: 4 of 4 Build pages (0 missing on the live site); skipped (not Build): 1
Open findings: 1 CRITICAL, 3 MAJOR, 0 MINOR
By department: Content 0, SEO 0, Design 0, Development 4
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-b4932d69 | /services/tree-pruning/ | Development | CRITICAL | The page is still set to noindex, so search engines will drop it. | Remove the noindex robots tag (and any X-Robots-Tag header) from the page. |
| QA-8fd79815 | /services/tree-removal/ | Development | MAJOR | 1 link(s), image(s) or file(s) on the live page still point at the staging domain: https://saltmarsh.staging-wise.site/wp-content/uploads/2026/11/crane-removal.webp. | Change them to the live domain (or relative links) and re-check the page. |
| QA-36f63ead | /contact/ | Development | MAJOR | The canonical tag points at the staging domain (https://saltmarsh.staging-wise.site/contact/). | Point the canonical tag at https://saltmarshtreecare.com/contact/. |
| QA-a6d0b724 | /trimming.html | Development | MAJOR | https://saltmarshtreecare.com/trimming.html does not redirect (HTTP 404); it should answer 301 to /services/tree-pruning/. | Add a 301 redirect from /trimming.html to /services/tree-pruning/. |

## Dev Tick List

Checked by hand on the live site; a script cannot prove these.

- [ ] Forms submit, and the test entry reaches the client's notification inbox
- [ ] Live chat loads and a test message arrives
- [ ] Analytics firing: a visit shows in GA4 Realtime
- [ ] Juvo snippet installed
- [ ] SSL certificate valid: the padlock shows and the certificate does not expire within 30 days

## Not Checked

- Redirect for https://saltmarshtreecare.com/gallery/ not tested: NO TARGET in the dev handoff index (SEO to decide).
- Saved pages from live: HTTPS and response headers (X-Robots-Tag) were not checked.
- Storm Prep Guide (/blog/storm-prep-guide/) skipped: priority Post-Launch.

RESULT: LIVE ISSUES
