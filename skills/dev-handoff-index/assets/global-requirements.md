# Global requirements

Fixed lines the script copies into the index's Global section. One `##` per subsection; every non-empty line under it is copied as written. Change the agency standard here, never in the generated index.

## analytics
- Install the client's GA4 property and Google Tag Manager container on every page; use the access the AM confirmed in the kickoff setup checklist.
- Track every conversion point listed below as a GA4 event (form submit, click-to-call, email click), and mark the form submit as a key event.
- Leave tracking off the staging site, or filter staging traffic out, so test visits do not count.

## sitemap
- Generate sitemap.xml automatically from the published pages and submit it in Google Search Console at launch.
- List only canonical, indexable URLs that return 200; leave out redirected old URLs, staging URLs, thank-you pages and noindex pages.

## robots
- Staging: block all crawlers (Disallow: /) and noindex every page until launch.
- Live: allow crawling of the whole site, block only admin and utility paths, and add the line Sitemap: followed by the live sitemap.xml URL.
- Check on launch day that the staging block did not carry over to the live site.
