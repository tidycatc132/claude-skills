# Getting the inputs

Load this when you need rankings, an indexed page count, or a page list and the user has not handed them over.

## Page list

- Live site: `--sitemap https://site/sitemap.xml` follows sitemap indexes; `--urls urls.txt` takes one URL per line (`#` comments allowed). Cap with `--max-pages` (default 500) and pace with `--delay` (default 0.5 s).
- Saved HTML (pre-migration crawl, a staging export, a `wget -p` mirror): put the files in one folder with a `manifest.csv` of `url,file[,status]`. `status` defaults to 200; give the real code for error pages so the diff treats them as outages rather than content changes.
- Choose a representative set rather than everything on a huge site: homepage, every money page, top 20 to 50 organic landing pages, one template example per content type. Keep the same list between runs; a URL missing from the current run is reported as `page` high.
- Sites that render titles, canonicals or JSON-LD with JavaScript will snapshot as missing those fields. Say so to the user and either snapshot with a rendering crawler export (saved HTML from the browser) or exclude those fields from the verdict.

## Rankings (`rankings.csv`: `keyword,url,position`)

Any rank tracker export works once reduced to those three columns. Extra columns are ignored; column names are matched case-insensitively.

- A rank tracker (its MCP tools or a CSV export): write one row per keyword with the ranking URL and position; blank position for not ranking.
- Google Search Console (directly, or through a connector that exposes Search Console performance data): use the Queries report with average position over the same 7-day window for both snapshots, and the Pages dimension for `url`. Average positions are noisier than tracked positions; expect more `low` rows.
- Keep search engine, location and device constant between baseline and current. If you track several locations, write one rankings file per location and snapshot each as its own series (for example `seo-drift/denver/` and `seo-drift/boulder/`).

## Indexed page count (`--indexed-count N`)

- Preferred: Search Console, Pages report, "Indexed" total for the property.
- Fallback: `site:example.com` result count in Google. It is an estimate; only large swings mean anything, which is why drops under 10% are `low`.
- Leave it out rather than guess; the index rules only run when both snapshots carry a number.

## When to snapshot

- Baseline immediately before a change (deploy, CMS upgrade, migration, plugin change) and again right after it goes live, then once more a week later when rankings have reacted.
- Routine monitoring: weekly or monthly, same URL list, same rankings source. Name snapshots by date (`seo-drift/2026-10-12.json`) and keep the one approved baseline as `seo-drift/baseline.json`.
