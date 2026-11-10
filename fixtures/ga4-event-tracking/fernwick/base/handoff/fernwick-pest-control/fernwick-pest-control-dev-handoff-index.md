Client: Fernwick Pest Control
Checked: 2026-11-03
Sitemap report: seo-reports/site-structure-optimizer/2026-10-20-fernwick-pest-control.md
Week 2 handoff: handoff/fernwick-pest-control/fernwick-pest-control-week-2-handoff.md (GO)
Page-type design briefs: design/fernwick-pest-control/fernwick-pest-control-page-type-design-briefs.md
Design QA and dev prep: design/fernwick-pest-control/fernwick-pest-control-design-qa-devprep.md (RESULT: PASS)
Client feedback: feedback/fernwick-pest-control/2026-10-30-feedback.md

# Dev Handoff Index: Fernwick Pest Control

Pages: 6 READY, 0 WAITING ON CLIENT CHANGES, 1 NOT WRITTEN, 0 NO TEMPLATE

Every value below is copied from the file named beside it. Re-run the skill after any change; only statuses move.

## Homepage

### Home

- Page: Home
- URL: /
- Content file: content/home/article.md
- Template: Homepage (design/fernwick-pest-control/fernwick-pest-control-homepage-design-brief.md)
- Meta title: Pest Control in Ashby, MA | Fernwick Pest Control
- Meta description: Ants, mice, wasps and termites handled by a licensed Ashby crew. Same-week visits and a written plan for every home.
- H1: Pest Control for Ashby Homes
- Internal links:
  - /contact/ (anchor: Book an inspection)
  - /services/termite-treatment/ (anchor: Termite treatment)
  - /services/rodent-control/ (anchor: Rodent control)
- Priority: Build
- Status: READY

## Service Pages

### Termite Treatment

- Page: Termite Treatment
- URL: /services/termite-treatment/
- Content file: content/termite-treatment/article.md
- Template: Service page (design/fernwick-pest-control/fernwick-pest-control-page-type-design-briefs.md)
- Meta title: Termite Treatment in Ashby, MA | Fernwick Pest Control
- Meta description: How we find and treat termites in Ashby homes, what it costs and how long the barrier lasts.
- H1: Termite Treatment in Ashby
- Internal links:
  - /services/rodent-control/ (anchor: rodent control)
  - /contact/ (anchor: Get a termite inspection)
- Priority: Build
- Status: READY

### Rodent Control

- Page: Rodent Control
- URL: /services/rodent-control/
- Content file: content/rodent-control/article.md
- Template: Service page (design/fernwick-pest-control/fernwick-pest-control-page-type-design-briefs.md)
- Meta title: Mouse and Rat Control in Ashby, MA | Fernwick Pest Control
- Meta description: Mice in the walls or rats in the shed? We seal entry points and clear them out, with a follow-up visit included.
- H1: Mouse and Rat Control in Ashby
- Internal links:
  - /services/termite-treatment/ (anchor: termite treatment)
  - /contact/ (anchor: Book a rodent visit)
- Priority: Build
- Status: READY

## Location Pages

### Townsend Pest Control

- Page: Townsend Pest Control
- URL: /townsend-pest-control/
- Content file: content/townsend-pest-control/article.md
- Template: Location page (design/fernwick-pest-control/fernwick-pest-control-page-type-design-briefs.md)
- Meta title: Pest Control in Townsend, MA | Fernwick Pest Control
- Meta description: The same licensed crew and same-week visits for Townsend homes, ten minutes from our Ashby base.
- H1: Pest Control in Townsend
- Internal links:
  - /services/termite-treatment/ (anchor: Termite treatment in Townsend)
  - /contact/ (anchor: Book a Townsend visit)
- Priority: Build
- Status: READY

## About Page

### About

- Page: About
- URL: /about/
- Content file: content/about/article.md
- Template: About page (design/fernwick-pest-control/fernwick-pest-control-page-type-design-briefs.md)
- Meta title: About Fernwick Pest Control | Ashby Since 2012
- Meta description: A family pest control company in Ashby since 2012, licensed in Massachusetts. Meet the crew.
- H1: About Fernwick Pest Control
- Internal links:
  - /townsend-pest-control/ (anchor: Townsend)
- Priority: Build
- Status: READY

## Contact Page

### Contact

- Page: Contact
- URL: /contact/
- Content file: content/contact/article.md
- Template: Contact page (design/fernwick-pest-control/fernwick-pest-control-page-type-design-briefs.md)
- Meta title: Contact Fernwick Pest Control | Book an Inspection
- Meta description: Call 978-555-0147 or send the form to book a pest inspection in Ashby or Townsend.
- H1: Contact Fernwick Pest Control
- Internal links: none
- Priority: Build
- Status: READY

## Pages Without a Template

### Spring Ant Guide

- Page: Spring Ant Guide
- URL: /blog/spring-ant-guide/
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

- Home: tel:+19785550147 (anchor: 978-555-0147)
- Termite Treatment: tel:+19785550147 (anchor: 978-555-0147)
- Rodent Control: tel:+19785550147 (anchor: 978-555-0147)
- Contact: tel:+19785550147 (anchor: 978-555-0147)
- Contact: mailto:office@fernwickpest.com (anchor: office@fernwickpest.com)
- Contact: contact form (section: Book an Inspection)

### sitemap.xml

- Generate sitemap.xml automatically from the published pages and submit it in Google Search Console at launch.
- List only canonical, indexable URLs that return 200; leave out redirected old URLs, staging URLs, thank-you pages and noindex pages.

URLs to list at launch (Build priority):

- /
- /services/termite-treatment/
- /services/rodent-control/
- /townsend-pest-control/
- /about/
- /contact/

Add when published (Post-Launch):

- /blog/spring-ant-guide/

### robots.txt

- Staging: block all crawlers (Disallow: /) and noindex every page until launch.
- Live: allow crawling of the whole site, block only admin and utility paths, and add the line Sitemap: followed by the live sitemap.xml URL.
- Check on launch day that the staging block did not carry over to the live site.

### Structured data

Structured data: not in the current process

### Redirects

| Old URL | New URL | Note |
|---|---|---|
| https://fernwickpest.com/services.html | /services/termite-treatment/ | 301, old catch-all services page |

## Blocking

- none

GO
