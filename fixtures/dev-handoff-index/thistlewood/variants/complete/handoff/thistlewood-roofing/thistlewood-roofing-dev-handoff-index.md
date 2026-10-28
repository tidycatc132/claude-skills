Client: Thistlewood Roofing
Checked: 2026-10-22
Sitemap report: seo-reports/site-structure-optimizer/2026-10-14-thistlewood-roofing.md
Week 2 handoff: handoff/thistlewood-roofing/thistlewood-roofing-week-2-handoff.md (GO)
Page-type design briefs: design/thistlewood-roofing/thistlewood-roofing-page-type-design-briefs.md
Design QA and dev prep: not run yet (design-qa-dev-prep)
Client feedback: feedback/thistlewood-roofing/2026-10-21-feedback.md

# Dev Handoff Index: Thistlewood Roofing

Pages: 4 READY, 2 WAITING ON CLIENT CHANGES, 2 NOT WRITTEN, 0 NO TEMPLATE

Every value below is copied from the file named beside it. Re-run the skill after any change; only statuses move.

## Homepage

### Home

- Page: Home
- URL: /
- Content file: content/home/article.md
- Template: Homepage (design/thistlewood-roofing/thistlewood-roofing-homepage-design-brief.md)
- Meta title: Redmond Roofing Company | Thistlewood Roofing
- Meta description: Roof replacement, repairs and gutters from a Redmond crew that has worked Central Oregon roofs since 2009. Free inspections.
- H1: Redmond Roofing Company for Replacements, Repairs and Gutters
- Internal links:
  - /contact/ (anchor: Book a free roof inspection)
  - /services/roof-replacement/ (anchor: Roof replacement)
  - /services/roof-repair/ (anchor: Roof repair)
  - /services/gutter-installation/ (anchor: Seamless gutters)
  - /contact/ (anchor: Request an inspection)
- Priority: Build
- Status: READY

## Service Pages

### Roof Replacement

- Page: Roof Replacement
- URL: /services/roof-replacement/
- Content file: content/roof-replacement/article.md
- Template: Service page (design/thistlewood-roofing/thistlewood-roofing-page-type-design-briefs.md)
- Meta title: Roof Replacement in Redmond, OR | Thistlewood Roofing
- Meta description: What a roof replacement costs in Redmond, how long it takes, and when a repair is enough. Free inspection with a written quote.
- H1: Roof Replacement in Redmond, OR
- Internal links:
  - /services/roof-repair/ (anchor: roof repair)
  - /gallery/ (anchor: past projects) NOT IN SITEMAP, no redirect target
  - /contact/ (anchor: Book a free roof inspection)
- Priority: Build
- Status: READY

### Roof Repair

- Page: Roof Repair
- URL: /services/roof-repair/
- Content file: content/roof-repair/article.md
- Template: Service page (design/thistlewood-roofing/thistlewood-roofing-page-type-design-briefs.md)
- Meta title: Roof Repair in Redmond: Leaks, Flashing and Storm Damage | Thistlewood Roofing
- Meta description: Leak, flashing and storm repairs for Redmond homes, usually done in a day. What a repair costs and when it is not worth it.
- H1: Roof Repair in Redmond: Leaks, Flashing and Storm Damage
- Internal links:
  - /services/roof-replacement/ (anchor: full roof replacement)
  - /contact/ (anchor: Book a repair visit)
- Priority: Build
- Status: WAITING ON CLIENT CHANGES (feedback/thistlewood-roofing/2026-10-21-feedback.md row #1)

## Location Pages

### Redmond Roofer

- Page: Redmond Roofer
- URL: /redmond-roofer/
- Content file: content/redmond-roofer/article.md
- Template: Location page (design/thistlewood-roofing/thistlewood-roofing-page-type-design-briefs.md)
- Meta title: Roofer in Redmond, OR | Thistlewood Roofing
- Meta description: A Redmond roofing crew for asphalt, metal and flat roofs. Local references, free inspections and directions to the yard on SW Veterans Way.
- H1: Your Redmond Roofer
- Internal links:
  - /services/roof-replacement/ (anchor: Roof replacement in Redmond)
  - /services/roof-repair/ (anchor: Roof repair in Redmond)
  - /contact/ (anchor: Book your free inspection)
- Priority: Build
- Status: WAITING ON CLIENT CHANGES (feedback/thistlewood-roofing/2026-10-21-feedback.md row #3)

## About Page

### About

- Page: About
- URL: /about/
- Content file: content/about/article.md
- Template: About page (design/thistlewood-roofing/thistlewood-roofing-page-type-design-briefs.md)
- Meta title: About Thistlewood Roofing | Redmond Roofers Since 2009
- Meta description: Family-run since 2009, licensed in Oregon (CCB #214477), with a crew of eleven. Meet the people who will be on your roof.
- H1: About Thistlewood Roofing
- Internal links:
  - /redmond-roofer/ (anchor: Redmond)
  - /contact/ (anchor: Book a free roof inspection)
- Priority: Build
- Status: READY

## Contact Page

### Contact

- Page: Contact
- URL: /contact/
- Content file: content/contact/article.md
- Template: Contact page (design/thistlewood-roofing/thistlewood-roofing-page-type-design-briefs.md)
- Meta title: Contact Thistlewood Roofing | Book a Free Roof Inspection
- Meta description: Call 541-555-0182 or send the form to book a free roof inspection in Redmond, Bend or Sisters.
- H1: Contact Thistlewood Roofing
- Internal links: none
- Priority: Build
- Status: READY

## Pages Without a Template

### Gutter Installation

- Page: Gutter Installation
- URL: /services/gutter-installation/
- Content file: none
- Template: none
- Meta title: none
- Meta description: none
- H1: none
- Internal links: none
- Priority: Build
- Status: NOT WRITTEN

### Storm Damage Roof Guide

- Page: Storm Damage Roof Guide
- URL: /blog/storm-damage-roof-guide/
- Content file: none
- Template: none
- Meta title: none
- Meta description: none
- H1: none
- Internal links: none
- Priority: Post-Launch
- Status: NOT WRITTEN

## Global

### Analytics and tracking

- Install the client's GA4 property and Google Tag Manager container on every page; use the access the AM confirmed in the kickoff setup checklist.
- Track every conversion point listed below as a GA4 event (form submit, click-to-call, email click), and mark the form submit as a key event.
- Leave tracking off the staging site, or filter staging traffic out, so test visits do not count.

Conversion points in the written pages (track each as an event):

- Home: tel:+15415550182 (anchor: 541-555-0182)
- Roof Replacement: tel:+15415550182 (anchor: 541-555-0182)
- Roof Repair: tel:+15415550182 (anchor: 541-555-0182)
- Contact: tel:+15415550182 (anchor: 541-555-0182)
- Contact: mailto:office@thistlewoodroofing.com (anchor: office@thistlewoodroofing.com)
- Contact: contact form (section: Contact Form)

### sitemap.xml

- Generate sitemap.xml automatically from the published pages and submit it in Google Search Console at launch.
- List only canonical, indexable URLs that return 200; leave out redirected old URLs, staging URLs, thank-you pages and noindex pages.

URLs to list at launch (Build priority):

- /
- /services/roof-replacement/
- /services/roof-repair/
- /services/gutter-installation/
- /redmond-roofer/
- /about/
- /contact/

Add when published (Post-Launch):

- /blog/storm-damage-roof-guide/

### robots.txt

- Staging: block all crawlers (Disallow: /) and noindex every page until launch.
- Live: allow crawling of the whole site, block only admin and utility paths, and add the line Sitemap: followed by the live sitemap.xml URL.
- Check on launch day that the staging block did not carry over to the live site.

### Structured data

Structured data: not in the current process

### Redirects

| Old URL | New URL | Note |
|---|---|---|
| https://thistlewoodroofing.com/about-us/ | /about/ | 301, same page renamed |
| https://thistlewoodroofing.com/roofing-services/ | /services/roof-replacement/ | 301, old catch-all services page |
| https://thistlewoodroofing.com/gallery/ | NO TARGET | SEO to decide: not in the sitemap or the redirect map |

## Blocking

- Page: Gutter Installation (/services/gutter-installation/) is NOT WRITTEN (Content, seo-content-writer)

Not blocking dev: 1 old URL(s) with NO TARGET; SEO picks a 301 target before launch.
Not blocking dev: waiting on client changes: Roof Repair, Redmond Roofer; build them after Content rewrites the page and this index is re-run.

NO-GO
