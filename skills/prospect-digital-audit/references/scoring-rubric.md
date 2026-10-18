# Scoring rubric

## Key pages

The homepage plus every core service page, capped at 10. A core service page is a page whose main purpose is one service or one location the business sells (from the main navigation, the services menu, or the sitemap). Blog posts, contact, about, privacy and legal pages are not key pages.

**Rule for every Correct/Incorrect cell: Incorrect if the homepage or any core service page fails the check.** Record which page failed and why in `audit.json` under `evidence`, so the sales manager can show it.

## SEO and content checks

| Cell | A key page fails when |
|---|---|
| URL Structure | URL has query strings, IDs, uppercase, underscores, file extensions, or is more than 3 folders deep; or the slug does not describe the page; a bare service-name slug such as /bookkeeping/ or /tax-services/ also fails. |
| Meta Titles | Missing, duplicated on another key page, over 60 characters, or missing the page's main service. A canonical pointing at a different URL, or `indexable` of 0, is reported as its own observation and in `evidence`. |
| Meta Descriptions | Missing, duplicated on another key page, under 70 or over 160 characters. |
| Headers / H Tags | Not exactly one H1, H1 missing the main service, or heading levels skipped (H2 to H4). |
| Structured Data | Homepage has no `LocalBusiness` (or subtype) or `Organization` schema; or schema fails to parse. Service pages are not required to have schema. |
| Page Word Count | Fewer than 500 unique words of main content (navigation, footer and repeated modules excluded; see data-sources). Aim for about 1,500 on service pages when recommending. |

Yes/No cells:

| Cell | Value |
|---|---|
| New Content Monthly | `Yes` if at least one new post or page in each of the last 3 months. |
| Duplicate Websites | `Yes` if any URL variant does not redirect to the main one, or a second site with the same content exists. |
| Duplicate Content | `Yes` if any key page shares most of its main text with another page. |
| Backlinks | `Yes` if 10 or more referring domains. |
| Internal Link Building | `Yes` if every core service page is linked from at least one other key page besides the menu. |
| External Link Building | `Yes` if referring domains grew in the last 6 months. |
| AI-Written Blogs | `Yes` if 2 of the 3 most recent posts show at least 3 of: generic intros that restate the title, no first-hand detail (names, places, jobs, photos), listicle structure with uniform paragraph lengths, stock phrases ("in today's fast-paced world", "delve", "navigate the complexities"). |

## UI and performance checks

| Cell | Value |
|---|---|
| SSL Secured | `Yes` if HTTPS loads with a valid certificate on the key pages. An http URL that returns 200 without redirecting is scored under Duplicate Websites, not here. |
| ADA Compliant | `No` if any key page has images without alt text, form fields without labels, missing `lang` attribute, or body text contrast obviously low. Otherwise `Yes`. This is a quick screen, not a WCAG certification; say so in the notes if challenged. |
| Privacy/Consent Compliance | `No` if no privacy policy link, or tracking tags fire with no consent banner or consent tool evidenced on the site or in its cookie notice. |
| Original Content | `No` if key pages use only stock photos (stock watermarks, reverse-image hits, generic people) and no own photos or video. |
| Clear Customer Journey | `Yes` if from the homepage a visitor reaches every core service in one click and each service page points to a next step. |
| Clear Conversion Path (CTAs) | `Yes` if every key page has a visible call or form CTA above the fold on mobile. |
| Effective Conversion Pages | `Yes` if the contact or quote page has a short form (6 fields or fewer), a click-to-call phone number, and trust signals (reviews, guarantees, licenses). |

## Subjective cells

Score 1 point for each statement that is true on the key pages; Correct at 3 or more.

**Look & Feel**: consistent colours and fonts across pages; nothing broken or overlapping on mobile; clear visual hierarchy (headline, subhead, CTA); the design does not look more than about 5 years old; images are sharp and sized correctly.

**Tone & Voice**: speaks to the customer ("you") more than about the company; plain language without jargon; consistent voice across pages; matches the audience and services discussed on the call; free of spelling and grammar errors.
