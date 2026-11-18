# Index spec

`handoff/<slug>/<slug>-dev-handoff-index.md`, written only by `scripts/dev_index.py run`. This file says what each part holds and how the script finds it, so you can explain a status or a NO-GO.

## Header

```
Client: <client name>                  the `Client:` line of kickoff/<slug>/<slug>-context.md, else the slug
Checked: <YYYY-MM-DD>                  today, or --date
Sitemap report: <path>
Week 2 handoff: <path> (GO | NO-GO | missing)
Client feedback: <path of the latest feedback file>          or    none

# Dev Handoff Index: <client name>

Pages: <n> READY, <n> WAITING ON CLIENT CHANGES, <n> NOT WRITTEN
```

## Pages

One `###` block per row of the table under the sitemap report's `URL map` heading (columns `Page`, `URL`, `Priority` at least), in URL map order inside its group. Groups, in this order, only when they have pages: `## Homepage`, `## Service Pages`, `## Location Pages`, `## About Page`, `## Contact Page`, `## Resource Pages`, `## Pages Without a Template`.

```
### <Page>

- Page: <Page cell of the URL map>
- URL: <URL cell of the URL map>
- Content file: content/<url-slug>/article.md            or none
- Template: <Homepage | Service page | Location page | ...> (page type from <source>)    or none
- Meta title: <metadata.md Meta title, exactly>          or none
- Meta description: <metadata.md Meta description>      or none
- H1: <metadata.md H1>                                    or none
- Internal links:
  - <target> (anchor: <anchor text>)
  - <target> (anchor: <anchor text>) NOT IN SITEMAP, redirects to <new URL> | no redirect target
- Priority: Build | Post-Launch
- Status: <status> (<detail>)
```

How each value is found:

- **Content folder.** The folder under `content/` whose `metadata.md` `URL slug` equals the URL map's URL (compared as paths, lower case, trailing slash). Else the folder named after the URL's last segment, `home` for `/`.
- **Meta fields.** The metadata table row value, everything between the field cell and the row's last pipe, so a title such as `Roof Repair | Brand` keeps its pipe (seo-content-writer writes it that way).
- **Internal links.** Every markdown link in `article.md` whose target starts with `/`, in page order, repeats kept. Targets that are not a URL map URL are flagged with the redirect map's answer, so dev does not build a broken link.
- **Page type (group and Template).** `/` is the homepage. For any other page, the first of these that names a type: the `<!-- section: ... -->` markers in its `article.md` (Company Story, Mission and Values, Team, Credentials: about; Contact Form, Phone and Email, Address and Hours, Map: contact; How We Serve, Local Services, Local Proof, Directions: location; markers of two types name none); the `format` of its content brief in `research/content-briefs/` (its `page_url` path matched to the URL map's URL, so an unwritten page gets its type too; `service-page`, `product-page`: service; `location-page`: location; `about-page`: about; `contact-page`: contact; an article format such as `how-to` or `explainer`: resource); its URL (`/about/`, `/contact/`, a `services/` segment, a `locations/` or `areas/` segment, a `blog/`, `resources/` or `guides/` segment). The source is named in the Template line. A page none of them names goes under `Pages Without a Template` with `Template: none`.
- **Priority.** `Post-Launch` when the URL map's Priority cell contains post-launch, phase 2 or after launch; every other page, including pages marked `(not in SOW scope)`, is `Build`.

## Statuses

Checked in this order; the first that applies wins.

| Status | When | Who fixes it |
| --- | --- | --- |
| `NOT WRITTEN` | no content folder, no `article.md`, no `metadata.md`, or no Meta title or Meta description in it | Content, seo-content-writer |
| `WAITING ON CLIENT CHANGES` | the latest `feedback/<slug>/YYYY-MM-DD-feedback.md` (by the date in its name) has a `## Feedback Items` row whose Impact level is not `none` and that names the page, in Affects as `page: <url-slug>` or in the Impact's `pages <url-slug>, ...` list, and the page's `article.md` was last modified no later than that feedback file. The detail names the file and the row numbers | Content rewrites the page; re-run releases it |
| `READY` | none of the above | Dev builds it |

Holds compare file modification times. Copying, syncing or cloning the client folder can reset them; if a status looks wrong after a move, Content re-saves the rewritten page and the index is re-run.

An older feedback file never holds a page; only the latest one counts, because its rows are the client's current word.

## Global

Copied in this order:

- `### Analytics and tracking`: the fixed lines from `assets/global-requirements.md`, then every `tel:` and `mailto:` link and every contact form section in the written pages, by page, as the events to track.
- `### sitemap.xml`: the fixed lines, then every `Build` URL to list at launch and every `Post-Launch` URL to add when published.
- `### robots.txt`: the fixed lines.
- `### Structured data`: the line `Structured data: not in the current process`. Nothing in the build produces JSON-LD.
- `### Redirects`: the table `| Old URL | New URL | Note |`. One row per URL in the URL inventory whose path is not a URL map URL: its `New URL` from the redirect map (matched on the old URL's path) with the map's note, or `NO TARGET` and "SEO to decide". Redirect map rows whose old URL is not in the inventory follow, marked so. With a header-only inventory the section says `No existing site` (and notes any redirect map rows for SEO to confirm). Old URLs that keep their address get no row.

## Blocking and result

`## Blocking` lists each reason for `NO-GO` with its owner and skill:

- the sitemap report has no `URL map`, or there is none;
- the Week 2 handoff is missing or its last line is not `GO`;
- the URL inventory is missing or its header is not `url,title,page_type,status,source`;
- a `Build` page is `NOT WRITTEN`.

Below it, lines starting "Not blocking dev" count old URLs with `NO TARGET` (SEO picks a 301 target before launch), name the held pages, and name each written `Build` page of no recognised type (Dev picks the closest template).

The last line is `GO` or `NO-GO`.
