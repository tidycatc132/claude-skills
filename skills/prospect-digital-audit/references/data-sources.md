# Data sources by section

SE Ranking tool names below are the `mcp__SE_Ranking__*` tools. Before the first call to any of them, load its schema and use the parameters it lists; do not guess parameter names. If SE Ranking is not connected, stop and tell the user, because rankings, authority and AI visibility depend on it.

## Site crawl (SEO and UI cells)

- Start an SE Ranking standard audit on the URL (`DATA_createStandardAudit`), poll `DATA_getAuditStatus`, then read `DATA_getAuditReport` and `DATA_getAuditPagesByIssue` for meta titles, meta descriptions, headings, duplicate content, word count, internal links and structured data.
- Also fetch every key page and save its HTML to `<run-folder>/pages/`. Judgment cells (Tone & Voice, customer journey, CTAs, original content) need the page itself, and the ADA check runs on the saved files. Direct requests to the prospect site may be blocked in the sandbox and a summarizing page fetch cannot see raw HTML or JSON-LD. When that happens use `DATA_getCrawledPages` for per-page `title_len`, `description_len`, `h1_len`, `words_count`, `canonical` and `indexable`, and mark cells that need raw HTML or rendering (Structured Data, ADA, Internal Link Building, AI-Written Blogs) as `Unknown`.
- If the audit has not finished after about 10 minutes, use the page fetches alone and note it.
- `words_count` in the crawl includes repeated header, footer and menu text. Estimate the site's boilerplate from a thin page (for example a thank-you page) and subtract it to get unique words.

| Cell | How |
|---|---|
| Website Platform | Generator meta tag, asset paths (`/wp-content/`, `cdn.shopify.com`, `static.wixstatic.com`, `squarespace`, `webflow`), response headers. Transcript if undetectable. |
| URL Structure | Key page URLs per rubric. |
| Meta Titles / Descriptions / Headers / Structured Data / Page Word Count | Audit report plus page HTML, scored per rubric. |
| New Content Monthly | Blog post dates or sitemap `lastmod`. |
| Duplicate Websites | `http://`, `https://`, `www` and non-`www` variants must all redirect to one version; also search the business name for a second site with the same content. |
| Duplicate Content | Audit duplicate-content issues on key pages. |
| Backlinks | `DATA_getBacklinksSummary`. |
| Internal Link Building | Links between key pages, from the HTML. |
| External Link Building | `DATA_getNewLostRefDomainsCount` for the last 6 months. |
| Domain Authority | `DATA_getDomainAuthority` (SE Ranking's score, 0 to 100). Write it as "N (SE Ranking scale)"; other tools use other scales, so mention any figure quoted on the call in the notes. |
| Domain Age | RDAP: fetch `https://rdap.org/domain/<domain>` and read the registration event date. Write it as "N years". |
| SSL Secured | HTTPS loads with a valid certificate and HTTP redirects to it. |
| ADA Compliant / ADA Software | `scripts/check_ada.py` on the saved key-page HTML; see the section below. |
| Privacy/Consent Compliance | Privacy policy linked in the footer, and a consent banner if any tracking tag fires. |
| # of Core Pages | Sitemap URLs that are services, locations, industries, pricing or about pages. Exclude blog and resources articles, partner pages, offers, events, legal and thank-you pages. |
| # of Blog Posts | Post sitemap count; mention separate article sections (for example /resources/) in the notes. |
| AI-Written Blogs | Rubric judgment on the 3 most recent posts; `No` if there are no posts. |

## Core Web Vitals

Fetch PageSpeed Insights for the homepage, once per strategy. The keyless API is often quota-limited (HTTP 429): use a key if the user supplied one; otherwise take Overall Test Results from the SE Ranking audit's field Core Web Vitals (good share of 75% or more for LCP, CLS and INP on mobile means `Pass`) and write `Unknown` for the optimization and speed cells.
`https://www.googleapis.com/pagespeedonline/v5/runPagespeed?url=<url>&strategy=mobile` and `&strategy=desktop`.

| Cell | Value |
|---|---|
| Overall Test Results | `Pass` if the field-data Core Web Vitals assessment passes on mobile; if there is no field data, `Pass` only if mobile LCP is 2.5 s or less, CLS 0.1 or less and TBT 200 ms or less in lab data. Otherwise `Fail`. |
| Desktop / Mobile Page Optimization | Lighthouse performance score (`lighthouseResult.categories.performance.score` x 100) as a percentage. |
| Desktop / Mobile Speed | Lab Speed Index (`lighthouseResult.audits.speed-index.numericValue`, ms to seconds), one decimal. |
| Desktop / Mobile LCP | Largest Contentful Paint in seconds, one decimal: the field value `loadingExperience.metrics.LARGEST_CONTENTFUL_PAINT_MS.percentile` when PageSpeed returns one (Google's 28-day 75th percentile), otherwise the lab value `lighthouseResult.audits.largest-contentful-paint.numericValue`. Say in `evidence` which one it was. Under 2.5 s is good, 2.5 to 4.0 needs improvement, over 4.0 is poor. |

Run mobile and desktop as separate requests; each gives its own LCP.

## ADA Compliant / ADA Software

Save the HTML of every key page and run `python3 -I <skill folder>/scripts/check_ada.py <files...> --out <run-folder>/ada.json`. The result is `Pass` when accessibility software (overlay or widget) is detected or the quick screen is clean on every page, else `Fail`; the rubric has the rule. If the page HTML cannot be fetched at all, the cell is `Unknown`.

## Generative AI visibility

`DATA_getAiSearchOverview` and `DATA_getAiSearchPromptsByTarget` for the domain. `Yes` for an engine if the domain is cited or the brand mentioned for any prompt. Gemini covers Google AI Overviews and AI Mode; "Other" covers Perplexity and any other engine SE Ranking reports. If SE Ranking has no data for the domain, write `No` for each engine and note "no AI mentions found in SE Ranking data".

## Analytics and ads (no account access)

Scan the HTML of the homepage and one service page, plus any Tag Manager container script:

| Cell | Yes when |
|---|---|
| Google Analytics | `gtag/js?id=G-`, `G-XXXXXXX` config, or `analytics.js` / `UA-` |
| Google Tag Manager | `googletagmanager.com/gtm.js?id=GTM-` |
| Google Ads | `AW-` conversion tag on the site, or `DATA_getDomainAdsByDomain` shows paid ads in the last 3 months |
| Meta Ads | Meta Ad Library shows active ads for the business page, if reachable; otherwise Meta pixel (`fbq(`, `connect.facebook.net`) plus the prospect saying they run Meta ads |
| Other Ads | Microsoft UET (`bat.bing.com`), TikTok, LinkedIn Insight, Nextdoor or similar pixels, or the prospect naming another paid channel |

If GTM is present, fetch `https://www.googletagmanager.com/gtm.js?id=<GTM-ID>` and search it for `G-`, `AW-`, pixel and UET IDs too. A tag in the container that the prospect says is not running (for example a Meta pixel with no Meta ads) is recorded as `No` for the ads cell and listed in the notes.

When detection and the transcript disagree, detection wins and the conflict goes in the notes. When detection finds nothing and the transcript is clear, use the transcript and say so in the notes.

## GBP and reviews

Search the web for the business name plus city. Read stars and review counts from the Google Business Profile, Yelp and Facebook pages. A profile that does not exist is `0 - Stars` and `0 - Reviews`, and that goes in the observations if it matters.

## Keyword volumes

`DATA_getKeywordsMetrics` for the 5 keyword groups, US database. Volumes are national, not per city; say so in the notes.

## Rankings grid

For each of the 25 keyword x city pairs:

1. Resolve the city with `DATA_getSerpLocations` using "City, State"; short names return noisy lists, so save the output and filter it with a few lines of Python.
2. Request the SERP for the keyword at that location with `DATA_getSerpResults`. Send ONE query per call (a multi-query array returns only the first) and at most 3 calls in parallel. A call can time out at 60 seconds while the task still finishes: list tasks with `DATA_getSerpTasks` and fetch the finished one with `DATA_getSerpTaskAdvancedResults`. Do not re-run a query that timed out; advanced results cost credits. Each result is about 70 KB, so save it to a file and run `python3 -I <skill folder>/scripts/parse_serp.py <domain> "<business name>" <files...> --out <run-folder>/positions.json`, which writes the positions as JSON.
3. `maps_position`: the prospect's position in the local pack (1 to 3) matched by business name or website; empty if absent.
4. `organic_position`: the prospect's domain's best organic position if 10 or better; empty otherwise.
