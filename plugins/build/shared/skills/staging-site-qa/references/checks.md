# Checks

What `scripts/qa.py scan` checks on each `Build` page of the dev handoff index, and the department and severity it gives. Severities follow the launch rules: CRITICAL must be fixed before launch (broken functionality, missing content or page, SEO-blocking), MAJOR should be fixed before launch, MINOR can go to the post-launch backlog.

| Check | What counts as a finding | Department | Severity |
|---|---|---|---|
| Page exists | 404 on staging, a redirect to another page (live mode), or no saved file for the URL | Development | CRITICAL |
| HTTP status | anything other than 200 (or no response) | Development | CRITICAL |
| HTTPS | the page or the staging base URL is plain HTTP (live mode only) | Development | MAJOR |
| `Meta title` | missing (CRITICAL) or not exactly the index value (MAJOR) | SEO | CRITICAL / MAJOR |
| `Meta description` | missing or not exactly the index value | SEO | MAJOR |
| `H1` | missing (CRITICAL), not the index value (MAJOR), more than one H1 (MINOR) | SEO | as stated |
| Canonical | missing, on another domain, or not this page's path (the staging domain with the right path is a launch toggle) | SEO | MAJOR |
| H2 sections | an H2 of `article.md` is not on the page (`## Sources` is not checked: it can hold internal records) | Content | CRITICAL |
| Section order | the H2s that are present are in a different order | Content | MAJOR |
| Call to action | a link from the CTA section (page, `tel:` or `mailto:`) is not in the page's main content | Content | MAJOR |
| `Internal links` | a link from the index is not in the page's main content (MAJOR), or is there with different text (MINOR); links marked NOT IN SITEMAP are skipped | SEO | MAJOR / MINOR |
| Broken internal links | a link to a page that is not on staging (saved mode: only index pages and saved pages can be judged; others are listed under Not Checked) | Development | MAJOR |
| Staging domain | links or images in the page's main content, or og:url, on the staging host: one finding per page with a count and examples. Theme, menu, script and stylesheet URLs on the staging host follow the site URL setting, so they are one site-wide launch toggle instead | Development | MAJOR |
| Placeholder text | Latin filler text, bracketed insert notes, template braces, "sample text" | Content | CRITICAL |
| Alt text | an image with no alt attribute (an empty alt is decorative and allowed) | SEO | MAJOR |
| Broken image | an image on the staging host that does not load (live mode) | Design | MAJOR |
| Asset checklist | a file named in `### Images` is not used on any page | Design | MAJOR |
| Viewport | no viewport meta tag | Development | MAJOR |
| Favicon | no icon link (and, live, no /favicon.ico) | Development | MINOR |
| Open Graph | no og:title or no og:description | SEO | MINOR |
| Phone, email, address | a phone number or email on the page that is not in the client context, or a street address that is a near miss of the client's (same house number or same street words, different text) | Content | CRITICAL |

Main content is the page's `<main>` element; without one, the whole page. The context's contact details come from its `- Phone:`, `- Email:` and `- Address:` lines when it has them (the first listed is the one a fix names), otherwise from anywhere in the file. Address comparison treats Street/St, Northeast/NE/N.E. and similar as equal. The base URL must be the site root. Comparisons ignore case, extra spaces, curly quotes and end punctuation for headings and anchors; meta values must match exactly apart from spacing and entities.

Not findings:

- `noindex` (meta robots or the X-Robots-Tag header) is a launch toggle for Development.
- robots.txt with `Disallow: /` on staging is a launch toggle.
- A canonical on the staging domain whose path is right is a launch toggle.
- Theme, menu, script and stylesheet URLs on the staging domain are one site-wide launch toggle.
- A context with no phone, email or address when the page shows one becomes an AM item to confirm with the client.
- A page whose index status is not READY becomes an AM item.

`finding_id` is `QA-` plus the first 8 hex digits of a SHA-1 over the page path, the check name and a detail. Where there is an approved value (meta title, description, H1, an H2, an index link, the full approved section order), the detail is that value, so the problem keeps its id while its wrong value changes. Otherwise the detail is the problem itself: the wrong phone, email or address, the image path without alt text, the broken link target, which placeholder pattern matched, or a fixed word (staging-domain content, canonical, viewport). If such a value changes, the old id shows FIXED and the new one NEW.

The launch check (Dev, live site, after deployment) has its own checks, where noindex and a staging canonical are findings: `references/launch-check.md`.
