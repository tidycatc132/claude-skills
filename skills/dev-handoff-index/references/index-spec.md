# Index spec

`handoff/<slug>/<slug>-dev-handoff-index.md`, written only by `scripts/dev_index.py run`. This file says what each part holds and how the script finds it, so you can explain a status or a NO-GO.

## Header

```
Client: <client name>                  first line of the page-type briefs, else the slug
Checked: <YYYY-MM-DD>                  today, or --date
Sitemap report: <path>
Week 2 handoff: <path> (GO | NO-GO | missing)
Page-type design briefs: <path>
Design QA and dev prep: <path> (RESULT: PASS | FAIL | none)    or    not run yet (design-qa-dev-prep)
Client feedback: <path of the latest feedback file>          or    none

# Dev Handoff Index: <client name>

Pages: <n> READY, <n> WAITING ON CLIENT CHANGES, <n> NOT WRITTEN, <n> NO TEMPLATE
```

## Pages

One `###` block per row of the table under the sitemap report's `URL map` heading (columns `Page`, `URL`, `Priority` at least), in URL map order inside its group. Groups, in this order, only when they have pages: `## Homepage`, `## Service Pages`, `## Location Pages`, `## About Page`, `## Contact Page`, `## Resource Pages`, `## Pages Without a Template`.

```
### <Page>

- Page: <Page cell of the URL map>
- URL: <URL cell of the URL map>
- Content file: content/<url-slug>/article.md            or none
- Template: <Service page | Location page | ...> (<brief path>)    or none
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
- **Template.** The homepage's is the homepage design brief, when it exists. Any other page's is the page-type section of the briefs whose `### Pages` list names `content/<url-slug>/article.md`.
- **Priority.** `Post-Launch` when the URL map's Priority cell contains post-launch, phase 2 or after launch; every other page, including pages marked `(not in SOW scope)`, is `Build`.

## Statuses

Checked in this order; the first that applies wins.

| Status | When | Who fixes it |
| --- | --- | --- |
| `NOT WRITTEN` | no content folder, no `article.md`, no `metadata.md`, or no Meta title or Meta description in it | Content, seo-content-writer |
| `NO TEMPLATE` | written, but not listed in any page-type section (or the homepage has no homepage design brief) | Design, page-type-design-briefs (or homepage-design-brief) |
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

## Design Assets

Only when `design/<slug>/<slug>-design-qa-devprep.md` exists: its `## Asset Checklist` section, copied line for line (images, icon set, fonts, colour palette, spacing, interactive elements).

## Blocking and result

`## Blocking` lists each reason for `NO-GO` with its owner and skill:

- the sitemap report has no `URL map`, or there is none;
- the Week 2 handoff is missing or its last line is not `GO`;
- the page-type briefs are missing;
- the URL inventory is missing or its header is not `url,title,page_type,status,source`;
- the design QA file exists and does not end `RESULT: PASS`;
- a `Build` page is `NOT WRITTEN` or `NO TEMPLATE`.

Below it, lines starting "Not blocking dev" count old URLs with `NO TARGET` (SEO picks a 301 target before launch) and name the held pages. A missing design QA file is not blocking: the index can be built before Design finishes the QA, and the next run adds the assets.

The last line is `GO` or `NO-GO`.
