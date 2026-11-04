Client: Larkspur Family Dental
Date: 2026-11-21
Growth blueprint: blueprint/larkspur-dental/larkspur-dental-growth-blueprint.md
Keyword research: research/keyword-research/2026-10-14-larkspur-dental.md
Competitor analysis: seo-reports/competitor-analysis/2026-10-16-larkspur-dental.md
Dev handoff index: handoff/larkspur-dental/larkspur-dental-dev-handoff-index.md
Staging QA: qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md
BugHerd status: qa/larkspur-dental/larkspur-dental-bugherd-status.json
Launch check: qa/larkspur-dental/larkspur-dental-launch-check-2026-11-20.md (RESULT: LIVE ISSUES)
Week 5 feedback: feedback/larkspur-dental/2026-11-10-feedback.md
Live site: https://larkspurdental.com

# SEO/GEO Roadmap: Larkspur Family Dental

## Summary

Larkspur Family Dental launched on 2026-11-20 with the 13 build pages. Month 1 finishes launch: sitemaps, indexing, tracking and the baseline, the one missing redirect, the deferred Invisalign section and the sleep apnea page conversation. Months 2 and 3 follow the Blueprint's Phase 2 and Phase 3: the content calendar's guides for the Tier 2 searches, a target page for "dentist boise", and the start of local links and reviews to close the authority gap.

## Roadmap

| Month | Task | Description | Priority | Est. hours | Owner | Source |
|---|---|---|---|---|---|---|
| 1 | Submit the XML sitemap to Search Console and Bing | Submit https://larkspurdental.com/sitemap.xml in Google Search Console and Bing Webmaster Tools, and check both read it without errors. | high | 0.5 | SEO | launch carry-over |
| 1 | Request indexing for the homepage and top priority pages | Use URL Inspection in Search Console to request indexing for /, /emergency-dentist/, /services/family-dentistry/, /services/dental-implants/, /new-patients/, /contact/. | high | 1 | SEO | launch carry-over |
| 1 | Confirm GA4 and Search Console are connected | Check that GA4 records visits from the live domain and that the Search Console property is verified for it, and that the two are linked. | high | 0.5 | SEO | launch carry-over |
| 1 | Take a baseline with seo-drift-monitor | Snapshot every Build page on https://larkspurdental.com with seo-drift-monitor so later changes can be compared. | high | 1 | SEO | launch carry-over |
| 1 | Capture Core Web Vitals | Record LCP, INP and CLS for /, /emergency-dentist/, /services/family-dentistry/ on mobile and desktop. | high | 1 | SEO | launch carry-over |
| 1 | Update the Google Business Profile website link | Point the Google Business Profile website link at https://larkspurdental.com. | high | 0.5 | SEO | launch carry-over |
| 1 | /services/invisalign/: Add the section from the approved page content | The section "Is Invisalign right for me?" is missing. Deferred at the Week 5 sweep: Client is rewriting this section with their orthodontist after launch. | high | 1 | Content | qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md > QA-4c1e9a20 |
| 1 | /meet-us.html: Add a 301 redirect from /meet-us.html to /about/team/ | https://larkspurdental.com/meet-us.html does not redirect (HTTP 404); it should answer 301 to /about/team/. Open on the launch check of 2026-11-20. | high | 1 | Dev | qa/larkspur-dental/larkspur-dental-launch-check-2026-11-20.md > QA-5e2f8a33 |
| 1 | Choose a 301 target for https://larkspurdental.com/specials/ | The dev handoff index has no New URL for it (SEO to decide: not in the sitemap or the redirect map). Pick the closest launched page and ask Dev to add the redirect. | high | 0.5 | SEO | handoff/larkspur-dental/larkspur-dental-dev-handoff-index.md > Redirects: https://larkspurdental.com/specials/ |
| 1 | Write and publish /blog/cracked-tooth/ (explainer + FAQ) | Keyword: what to do for a cracked tooth. Why now: lowest KD in the set. Brief it with content-brief, then write it with seo-content-writer. | high | 6 | Content | research/keyword-research/2026-10-14-larkspur-dental.md > Content Calendar: January: what to do for a cracked tooth; blueprint/larkspur-dental/larkspur-dental-growth-blueprint.md > Tier 2: what to do for a cracked tooth |
| 1 | Discuss a sleep apnea mouthguard page | The client asked: "Our hygienists keep getting asked about sleep apnea mouthguards. Could we have a page for that?" PM/AM note: A thirteenth page is beyond the twelve-page SOW; plan it as retainer content after launch. | medium | 1 | AM | feedback/larkspur-dental/2026-11-10-feedback.md > #2 |
| 2 | Write and publish /blog/dental-implant-cost/ (cost guide) | Keyword: how much do dental implants cost. Why now: supports the implants page. Brief it with content-brief, then write it with seo-content-writer. | high | 6 | Content | research/keyword-research/2026-10-14-larkspur-dental.md > Content Calendar: February: how much do dental implants cost; blueprint/larkspur-dental/larkspur-dental-growth-blueprint.md > Tier 2: how much do dental implants cost |
| 2 | Write and publish Dental Anxiety Guide (/blog/dental-anxiety-guide/) | In the dev handoff index as Post-Launch; it was not built for launch. | medium | 6 | Content | handoff/larkspur-dental/larkspur-dental-dev-handoff-index.md > Dental Anxiety Guide |
| 2 | Choose the page that targets "dentist boise" | Keyword: dentist boise (6600 searches a month, difficulty 61). Tier 2 in the Growth Blueprint and not in the content calendar: decide whether a launched page takes it or new content is needed. | medium | 2 | SEO | blueprint/larkspur-dental/larkspur-dental-growth-blueprint.md > Tier 2: dentist boise |
| 2 | Start local link building | Referring domains: 14 for larkspurdental.com against 312 for treasurevalleysmiles.com. Earn links from local directories, partners, sponsorships and press. | medium | 4 | SEO | seo-reports/competitor-analysis/2026-10-16-larkspur-dental.md > Competitive Landscape: Referring domains |
| 2 | /about/team/: Add alt text that says what the image shows | The image /wp-content/uploads/team-group.webp has no alt text. Still open after the staging QA of 2026-11-16. | low | 1 | SEO | qa/larkspur-dental/larkspur-dental-staging-qa-2026-11-16.md > QA-7b3d5f11 |
| 3 | Write and publish /blog/are-dental-x-rays-safe/ (explainer) | Keyword: are dental x rays safe. Why now: common new-patient question. Brief it with content-brief, then write it with seo-content-writer. | medium | 6 | Content | research/keyword-research/2026-10-14-larkspur-dental.md > Content Calendar: March: are dental x rays safe; blueprint/larkspur-dental/larkspur-dental-growth-blueprint.md > Tier 3: are dental x rays safe |
| 3 | Collect reviews for the implant and Invisalign pages | Evidence: Treasure Valley Smiles has a service page for every treatment and 64 published reviews on its implant page. | medium | 2 | AM | seo-reports/competitor-analysis/2026-10-16-larkspur-dental.md > Strengths to Learn From #1 |
| 3 | Add direct cost answers to the implants page FAQ | Evidence: Boise Bright Dental answers cost questions directly, which is why AI answers cite it. | medium | 2 | Content | seo-reports/competitor-analysis/2026-10-16-larkspur-dental.md > Strengths to Learn From #2 |
| 3 | Pitch the implant cost guide for AI citations | Evidence: Implant cost guide to win AI citations from Boise Bright Dental. | medium | 2 | SEO | seo-reports/competitor-analysis/2026-10-16-larkspur-dental.md > Priority Opportunities #3 |

## Not Planned

- none
