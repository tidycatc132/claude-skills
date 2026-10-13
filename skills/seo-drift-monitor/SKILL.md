---
name: seo-drift-monitor
description: Snapshot a site's SEO state and diff it against an earlier snapshot to catch regressions over time. Captures per-URL titles, meta descriptions, canonicals, robots/noindex directives, H1s, schema.org types, word count and HTTP status, plus keyword positions from a rankings CSV and an indexed page count, into one JSON file; a later run diffs two snapshots into a severity-rated drift_changes.csv and drift_report.md with a verdict. Use when the user wants to baseline their SEO, monitor SEO over time, check whether a redeploy, redesign, CMS update or migration broke SEO, compare SEO to last month, or asks what changed, why titles changed, or whether pages fell out of the index. Trigger on "SEO drift", "SEO monitoring", "SEO regression", "track SEO over time", "baseline my SEO", "after migration SEO". Do NOT use for a one-off audit of the current state (use technical-seo-checker), writing titles or schema, keyword research, or uptime and performance monitoring; this skill only compares two points in time.
---

# SEO drift monitor

Two points in time, one diff, one verdict. The scripts do the capturing and comparing; you choose the inputs, run them, and explain the result in terms of search visibility.

## Files

- `scripts/snapshot.py` captures the state into one JSON file.
- `scripts/diff_snapshots.py` diffs two snapshot files into `drift_changes.csv` and `drift_report.md`.
- `references/drift-rules.md`: every rule and threshold with its severity. Load it when asked why something was rated as it was, or to tune a threshold.
- `references/data-sources.md`: how to get a page list, `rankings.csv` and an indexed count when the user has not provided them, and how often to snapshot. Load it when an input is missing.

Both scripts are standard-library Python and take every path as an argument, so run each one as its own plain `python3 <skill>/scripts/... ` command from the working directory: no `cd`, no piping into other shell tools, no chaining. `<skill>` stands for the folder that holds this SKILL.md; use its real path. Inspect inputs with the file-reading tool, not shell commands.

## Inputs

Snapshot sources, any combination:

| input | format |
|---|---|
| saved pages | folder with `manifest.csv` columns `url,file[,status]` and the HTML files; pass `--html-dir DIR` |
| live pages | `--urls urls.txt` (one URL per line) or `--sitemap URL` |
| rankings | CSV `keyword,url,position`; pass `--rankings FILE`. Blank or 0 position = not ranking |
| indexed count | `--indexed-count N` from Search Console or a `site:` query |

Snapshot output: `--out PATH`, default `seo-drift/<YYYY-MM-DD>.json`. Keep the approved baseline at `seo-drift/baseline.json`. Keys: `schema_version`, `captured_at`, `site`, `indexed_count`, `page_count`, `pages` (URL to fields `status`, `title`, `meta_description`, `canonical`, `robots`, `noindex`, `nofollow`, `h1`, `schema_types`, `hreflang_count`, `lang`, `word_count`, `redirect_to`, `x_robots_tag`, or only `status` and `fetch_error` when the page could not be read), `rankings` (keyword to `url`, `position`).

## Outputs of a diff

- `drift_changes.csv` with columns `severity,category,subject,field,before,after,note`.
  - `severity`: `critical`, `high`, `medium`, `low`, `info`.
  - `category`: `ranking`, `index`, `status`, `title`, `meta_description`, `canonical`, `robots`, `schema`, `h1`, `content`, `page`.
  - `subject`: a URL, a keyword, or `*` for a site-wide finding (mass title rewrite, indexed count).
- `drift_report.md`: a `VERDICT:` line (`REGRESSION DETECTED`, `MINOR DRIFT` or `NO REGRESSION`), counts by severity, a "Likely causes" list, and one table per category.
- Exit code 3 with `--fail-on high` (or another severity) when that level occurred, for CI.

## Workflow

1. Work out which of the three jobs the user wants: set a baseline, compare against an existing baseline, or both at once (they have "before" and "after" material already). Say which you are doing.
2. Gather inputs. Saved HTML needs a `manifest.csv`; write one if the user gave files but no manifest, inferring URLs from file paths only when the mapping is obvious, otherwise ask. For rankings or an indexed count that the user has not given, read `references/data-sources.md` before pulling them from a tool; if neither is available, snapshot without them and say the diff will cover on-page fields only.
3. Snapshot:
   ```
   python3 <skill>/scripts/snapshot.py --html-dir before --rankings before/rankings.csv --out seo-drift/baseline.json
   python3 <skill>/scripts/snapshot.py --urls urls.txt --rankings rankings.csv --indexed-count 412 --out seo-drift/2026-10-12.json
   ```
   Read the one-line summary it prints (pages, noindex count, non-200 count, keywords). A baseline with many non-200 or noindex pages is already suspicious; mention it.
4. Diff, when there are two snapshots:
   ```
   python3 <skill>/scripts/diff_snapshots.py seo-drift/baseline.json seo-drift/2026-10-12.json --csv drift_changes.csv --report drift_report.md
   ```
5. Report. Lead with the verdict line, then the critical and high rows in plain language: what changed, on which URL, and what it does to search visibility (a noindex removes the page from Google; a canonical to staging hands the ranking to a URL that does not exist for users; a title rewrite to a CMS template loses the keywords the page ranked for). Quote the "Likely causes" from the report when it has any. Mention medium and low rows as a count, not a list, unless the user asked for everything. Do not add findings the CSV does not contain, and do not describe how the scripts work unless asked.
6. For a baseline-only run, finish by telling the user the exact `diff_snapshots.py` command to run after their next change, with the baseline path filled in.

## Judgement calls

- Ranking drops alone are not proof the deploy broke something; rankings move on their own. Call a ranking drop a regression when the same URL also has an on-page finding, otherwise report it as "moved, cause unclear".
- Intentional changes (a planned title rewrite, a page deliberately removed) still appear as drift. Ask whether a change was intended before calling it a regression when the user's message hints at planned work.
- A page that disappeared from the current snapshot (`page`, high) is either removed or simply not crawled this run. Check the input list before reporting it as a lost page.
- JavaScript-rendered sites snapshot without the fields the browser would inject. Warn when the baseline shows empty titles or schema across the board.
- Record a new approved baseline only when the user says the current state is the one to measure against from now on; otherwise keep diffing against the original.
