---
name: dev-handoff-index
description: Builds a website's dev handoff index and says which pages dev can start. Copies each sitemap page's URL, content file, page type, meta tags and internal links from the sitemap report and written pages, sets each page's status (READY, WAITING ON CLIENT CHANGES, NOT WRITTEN) from the latest feedback, adds analytics, sitemap.xml, robots.txt and a 301 redirect table from the URL inventory, and ends in GO or NO-GO (the Week 3 gate). Use when Dev or the PM asks for the dev handoff index or package, whether the site is ready for dev, what dev can start building, or which old URLs need 301s at handoff. Do NOT use for the Week 2 check (use week-2-handoff-check), writing pages (use seo-content-writer), planning the sitemap (use site-structure-optimizer), staging QA (use staging-site-qa), sorting a client reply (use client-feedback), GA4 or GTM tracking setup (use ga4-event-tracking), a migration or technical audit (use technical-seo-checker), or JSON-LD (not in the process).
---

# Dev handoff index

Every field dev needs already sits in a file the earlier weeks saved. This skill copies them into one index, page by page, so nobody retypes a meta title or a URL, and says which pages dev can build now. The script does all of it; your job is to run it and report what it found. The index is format-agnostic: it names no page builder or theme.

## Input

All paths are relative to the client's working folder. `<slug>` is the client's folder name under `handoff/`, `feedback/` and `kickoff/`.

| Path | Required | What the script takes from it |
| --- | --- | --- |
| `seo-reports/site-structure-optimizer/YYYY-MM-DD-*.md` | yes | site-structure-optimizer's saved architecture report, the newest that has a `URL map` table (`Page`, `URL`, `Parent`, `Nav location`, `Priority`) and its `Redirect map` table (`Old URL`, `New URL`, `Note`). The `-targets.csv` beside it is not needed |
| `content/<url-slug>/metadata.md` and `article.md` | per page | seo-content-writer's page: `Meta title`, `Meta description`, `H1`, `URL slug` from the metadata table; internal links (`[anchor](/path/)`), `tel:` and `mailto:` links and a `<!-- section: Contact Form -->` marker from the article |
| `research/content-briefs/*.md` | no | content-brief's `page_url` and `format` front matter (matched to the URL map's URL), used for a page's type when its section markers name none, including pages not written yet |
| `kickoff/<slug>/<slug>-context.md` | no | its first line, `Client: <name>`, for the client name (else the slug) |
| `feedback/<slug>/YYYY-MM-DD-feedback.md` | no | client-feedback: only the latest one. Its `## Feedback Items` rows whose Impact is not `none` hold back the page in a `page: <url-slug>` Affects, and any page named in the Impact's `pages` list |
| `kickoff/<slug>/<slug>-url-inventory.csv` | yes | new-build-kickoff's old URLs, columns `url`, `title`, `page_type`, `status`, `source` (header only means no existing site) |
| `handoff/<slug>/<slug>-week-2-handoff.md` | yes | week-2-handoff-check: its last line, `GO` or `NO-GO` |

## Output

`handoff/<slug>/<slug>-dev-handoff-index.md`, written by the script and regenerated in full on every run. Layout, every rule and how each value is found: [Index Spec](references/index-spec.md). Read it when someone asks why a page has its status, why the result is NO-GO, or how a field was filled.

In short: a header naming every source file, a summary line `Pages: n READY, n WAITING ON CLIENT CHANGES, n NOT WRITTEN`, one `##` group per page type (`Homepage`, `Service Pages`, `Location Pages`, `About Page`, `Contact Page`, `Resource Pages`, `Pages Without a Template`) with one `###` block per sitemap page (`Page`, `URL`, `Content file`, `Template`, `Meta title`, `Meta description`, `H1`, `Internal links`, `Priority`, `Status`), then `## Global` (analytics and tracking, sitemap.xml, robots.txt, `Structured data: not in the current process`, and the redirect table `| Old URL | New URL | Note |`), `## Blocking`, and a last line `GO` or `NO-GO`.

Each page's type, and so its group and `Template` line, comes from the page itself: its seo-content-writer section markers, else its content brief's `format`, else its URL (`/services/...`, `/about/`, `/blog/...`). A page none of them names goes under `Pages Without a Template` and is noted as not blocking: Dev picks the closest template.

Statuses: `READY` (written, not held), `WAITING ON CLIENT CHANGES` (the latest feedback file holds it and its `article.md` is not newer than that file), `NOT WRITTEN` (no folder, or no `metadata.md` with a meta title and description). Priority is `Post-Launch` when the URL map's Priority cell says post-launch, phase 2 or after launch, else `Build`.

`GO` when there is a sitemap report with a `URL map`, the Week 2 handoff ends `GO`, the URL inventory exists with its exact header, and every `Build` page is `READY` or `WAITING ON CLIENT CHANGES`. Old URLs with `NO TARGET`, held pages and written `Build` pages of no recognised type are listed under Blocking as not blocking dev.

## Running the script

The script is `scripts/dev_index.py` in this skill's folder (`<skill-folder>` below is the folder this SKILL.md is in; write its real path). Run it from the client's working folder as one plain command, nothing chained before or after it (no `cd`, `&&`, pipes or loops):

```
python3 <skill-folder>/scripts/dev_index.py run --slug <slug>
```

Leave out `--slug` when there is only one client folder. If the call is denied, send the same single `python3` command again (use `python` if `python3` is missing); a denied `ls` or `cat` says nothing about `python3`. Use the file tools to look at files. Never write or edit the index yourself: if the script cannot run, say so and stop. It exits 0 on `GO`, 1 on `NO-GO` (both normal) and 2 on a usage error.

## Workflow

1. **Run** the command above. It prints the summary line, the pages ready to build now, the pages waiting on client changes, the count of old URLs with no target, the blocking items and `GO` or `NO-GO`.
2. **Answer** in chat in a few lines: `GO` or `NO-GO`; the index path; the pages dev can start now; each blocking item with the owner and skill the script names; held pages and which feedback row holds them; old URLs with `NO TARGET` for SEO to decide. Copy page names, URLs and statuses from the script's output; do not soften a `NO-GO`.
3. **To release a held page**, Content rewrites its `article.md` (seo-content-writer); then run the skill again. Only statuses move between runs.

## Rules

- The script's statuses stand. Do not mark a page ready because its file "looks fine", and do not hand-fix the index.
- Do not add structured data, accessibility notes or page-builder instructions; they are not in the process.
- When there are several client folders and the person named none, ask which client. That is the only question this skill asks.

## Scripts

| Script | Use |
| --- | --- |
| `scripts/dev_index.py run` | Writes the index and prints the result |
| `scripts/dev_index.py sitemap`, `content`, `pagetype`, `feedback`, `inventory` | Print, as JSON, what the script reads from one source file or page folder (`--validate` checks such a JSON file); the contracts use them |

The fixed lines of the Global section live in `assets/global-requirements.md`; change the agency standard there, never in a generated index. Standard-library Python 3 only.
