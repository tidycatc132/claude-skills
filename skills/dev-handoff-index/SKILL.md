---
name: dev-handoff-index
description: Builds a website's dev handoff index and says which pages dev can start. Copies each sitemap page's URL, content file, template, meta tags and internal links from the sitemap report, written pages and page-type design briefs, sets each page's status (READY, WAITING ON CLIENT CHANGES, NOT WRITTEN) from the latest feedback, adds analytics, sitemap.xml, robots.txt and a 301 redirect table from the URL inventory, and ends in GO or NO-GO (the Week 3 gate). Use when Dev or the PM asks for the dev handoff index or package, whether the site is ready for dev, what dev can start building, or which old URLs need 301s at handoff. Do NOT use for the Week 2 check (use week-2-handoff-check), checking the designed templates (use design-qa-dev-prep), writing pages (use seo-content-writer), planning the sitemap (use site-structure-optimizer), template briefs (use page-type-design-briefs), sorting a client reply (use client-feedback), a migration or technical audit (use technical-seo-checker), or JSON-LD (not in the process).
---

# Dev handoff index

Every field dev needs already sits in a file the earlier weeks saved. This skill copies them into one index, page by page, so nobody retypes a meta title or a URL, and says which pages dev can build now. The script does all of it; your job is to run it and report what it found. The index is format-agnostic: it names no page builder or theme.

## Input

All paths are relative to the client's working folder. `<slug>` is the client's folder name under `design/`, `handoff/`, `feedback/` and `kickoff/`.

| Path | Required | What the script takes from it |
| --- | --- | --- |
| `seo-reports/site-structure-optimizer/YYYY-MM-DD-*.md` | yes | site-structure-optimizer's saved architecture report, the newest that has a `URL map` table (`Page`, `URL`, `Parent`, `Nav location`, `Priority`) and its `Redirect map` table (`Old URL`, `New URL`, `Note`). The `-targets.csv` beside it is not needed |
| `content/<url-slug>/metadata.md` and `article.md` | per page | seo-content-writer's page: `Meta title`, `Meta description`, `H1`, `URL slug` from the metadata table; internal links (`[anchor](/path/)`), `tel:` and `mailto:` links and a `<!-- section: Contact Form -->` marker from the article |
| `design/<slug>/<slug>-page-type-design-briefs.md` | yes | page-type-design-briefs: each page file listed under a page-type section's `### Pages` gives that page its template. `## Page Types` names the sections |
| `design/<slug>/<slug>-homepage-design-brief.md` | for the homepage | its existence gives the homepage its template |
| `design/<slug>/<slug>-design-qa-devprep.md` | no | design-qa-dev-prep: the `## Asset Checklist` section, copied whole, and the `RESULT: PASS` or `RESULT: FAIL` line |
| `feedback/<slug>/YYYY-MM-DD-feedback.md` | no | client-feedback: only the latest one. Its `## Feedback Items` rows whose Impact is not `none` hold back the page in a `page: <url-slug>` Affects, and any page named in the Impact's `pages` list |
| `kickoff/<slug>/<slug>-url-inventory.csv` | yes | new-build-kickoff's old URLs, columns `url`, `title`, `page_type`, `status`, `source` (header only means no existing site) |
| `handoff/<slug>/<slug>-week-2-handoff.md` | yes | week-2-handoff-check: its last line, `GO` or `NO-GO` |

## Output

`handoff/<slug>/<slug>-dev-handoff-index.md`, written by the script and regenerated in full on every run. Layout, every rule and how each value is found: [Index Spec](references/index-spec.md). Read it when someone asks why a page has its status, why the result is NO-GO, or how a field was filled.

In short: a header naming every source file, a summary line `Pages: n READY, n WAITING ON CLIENT CHANGES, n NOT WRITTEN, n NO TEMPLATE`, one `##` group per page type (`Homepage`, `Service Pages`, `Location Pages`, `About Page`, `Contact Page`, `Resource Pages`, `Pages Without a Template`) with one `###` block per sitemap page (`Page`, `URL`, `Content file`, `Template`, `Meta title`, `Meta description`, `H1`, `Internal links`, `Priority`, `Status`), then `## Global` (analytics and tracking, sitemap.xml, robots.txt, `Structured data: not in the current process`, and the redirect table `| Old URL | New URL | Note |`), the design assets when the QA file exists, `## Blocking`, and a last line `GO` or `NO-GO`.

Statuses: `READY` (written, has a template, not held), `WAITING ON CLIENT CHANGES` (the latest feedback file holds it and its `article.md` is not newer than that file), `NOT WRITTEN` (no folder, or no `metadata.md` with a meta title and description), `NO TEMPLATE` (written but in no page-type section of the briefs). Priority is `Post-Launch` when the URL map's Priority cell says post-launch, phase 2 or after launch, else `Build`.

`GO` when the Week 2 handoff ends `GO`, the page-type briefs exist, the URL inventory exists, a design QA file (if there is one) ends `RESULT: PASS`, and every `Build` page is `READY` or `WAITING ON CLIENT CHANGES`. Old URLs with `NO TARGET` and held pages are listed under Blocking as not blocking dev.

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
| `scripts/dev_index.py sitemap`, `content`, `briefs`, `feedback`, `inventory`, `devprep` | Print, as JSON, what the script reads from one source file (`--validate` checks such a JSON file); the contracts use them |
| `scripts/selftest_dev_index.py` | Cases for the statuses, holds, redirects and GO rule on temporary folders; run after changing `dev_index.py` |

The fixed lines of the Global section live in `assets/global-requirements.md`; change the agency standard there, never in a generated index. Standard-library Python 3 only.
