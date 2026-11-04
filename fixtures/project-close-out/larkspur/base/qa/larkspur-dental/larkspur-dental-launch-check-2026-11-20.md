Client: Larkspur Family Dental
Checked: 2026-11-20
Live: https://larkspurdental.com (saved pages: live/)
Staging domain: larkspur.staging-wise.site (qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md)
Dev handoff index: handoff/larkspur-dental/larkspur-dental-dev-handoff-index.md (GO)
Redirects: 2 of 3 tested answer 301 or 308 to their New URL (from redirects.txt)
Compared with: none (first run)

# Launch Check: Larkspur Family Dental

## Summary

Pages checked: 13 of 13 Build pages (0 missing on the live site); skipped (not Build): 1
Open findings: 0 CRITICAL, 1 MAJOR, 0 MINOR
By department: Content 0, SEO 0, Design 0, Development 1
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-5e2f8a33 | /meet-us.html | Development | MAJOR | https://larkspurdental.com/meet-us.html does not redirect (HTTP 404); it should answer 301 to /about/team/. | Add a 301 redirect from /meet-us.html to /about/team/. |

## Dev Tick List

Checked by hand on the live site; a script cannot prove these.

- [ ] Forms submit, and the test entry reaches the client's notification inbox
- [ ] Live chat loads and a test message arrives
- [ ] Analytics firing: a visit shows in GA4 Realtime
- [ ] Juvo snippet installed
- [ ] SSL certificate valid: the padlock shows and the certificate does not expire within 30 days

## Not Checked

- Redirect for https://larkspurdental.com/specials/ not tested: NO TARGET in the dev handoff index (SEO to decide).
- Saved pages from live: HTTPS and response headers (X-Robots-Tag) were not checked.
- Dental Anxiety Guide (/blog/dental-anxiety-guide/) skipped: priority Post-Launch.

RESULT: LIVE ISSUES
