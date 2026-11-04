Client: Larkspur Family Dental
Checked: 2026-11-24
Live: https://larkspurdental.com (saved pages: live-rerun/)
Staging domain: larkspur.staging-wise.site (qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md)
Dev handoff index: handoff/larkspur-dental/larkspur-dental-dev-handoff-index.md (GO)
Redirects: 3 of 3 tested answer 301 or 308 to their New URL (from redirects-rerun.txt)
Compared with: qa/larkspur-dental/larkspur-dental-launch-check-2026-11-20.md

# Launch Check: Larkspur Family Dental

## Summary

Pages checked: 13 of 13 Build pages (0 missing on the live site); skipped (not Build): 1
Open findings: 0 CRITICAL, 1 MAJOR, 0 MINOR
By department: Content 0, SEO 0, Design 0, Development 1
Re-run: 1 FIXED, 0 OPEN, 1 NEW
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-c81d0e6b | /services/sedation-dentistry/ | Development | MAJOR | The meta description is "Sedation dentistry" ; the approved description is "Calm, comfortable visits with oral and IV sedation in Boise. Ask about options for anxious patients and longer treatments.". | Set the meta description to the approved text. |

## Re-run Status

| Finding ID | Status | Page URL | Department | Severity | Finding |
|---|---|---|---|---|---|
| QA-5e2f8a33 | FIXED | /meet-us.html | Development | MAJOR | https://larkspurdental.com/meet-us.html does not redirect (HTTP 404); it should answer 301 to /about/team/. |
| QA-c81d0e6b | NEW | /services/sedation-dentistry/ | Development | MAJOR | The meta description is "Sedation dentistry" ; the approved description is "Calm, comfortable visits with oral and IV sedation in Boise. Ask about options for anxious patients and longer treatments.". |

## Dev Tick List

Checked by hand on the live site; a script cannot prove these.

- [ ] Forms submit, and the test entry reaches the client's notification inbox
- [ ] Live chat loads and a test message arrives
- [ ] Analytics firing: a visit shows in GA4 Realtime
- [ ] Juvo snippet installed
- [ ] SSL certificate valid: the padlock shows and the certificate does not expire within 30 days

## Not Checked

- Redirect for https://larkspurdental.com/specials/ not tested: NO TARGET in the dev handoff index (SEO to decide).
- Saved pages from live-rerun: HTTPS and response headers (X-Robots-Tag) were not checked.
- Dental Anxiety Guide (/blog/dental-anxiety-guide/) skipped: priority Post-Launch.

RESULT: LIVE ISSUES
