# Input formats

What `case_study.py` reads from each file, and the two files the AM's decisions go in.

## Files from earlier skills

- **Dev handoff index** (`handoff/<slug>/<slug>-dev-handoff-index.md`). Each `##` page-type group (`Homepage`, `Service Pages`, `Location Pages`, `About Page`, `Contact Page`, `Resource Pages`, `Pages Without a Template`) and, in each `###` page block, the lines `- Page:`, `- URL:`, `- Content file:`, `- Template:`, `- Priority:`, `- Status:`. A page counts as built when its `Priority` is `Build` and its `Content file` exists. `Post-Launch` pages are left out of every count. From `### Redirects`, the table `| Old URL | New URL | Note |`: a row counts as redirected when its `New URL` is a path (starts with `/`); `NO TARGET` rows are not counted and are not before/after pairs. When the kit has no colour, the hex lines under `### Colour palette` (the design asset checklist) are used.
- **Article** (`content/<url-slug>/article.md`). Words are counted after dropping HTML comments and tags and keeping only the anchor text of links: every whitespace-separated token with a letter or digit counts.
- **URL inventory** (`kickoff/<slug>/<slug>-url-inventory.csv`, columns `url`, `title`, `page_type`, `status`, `source`). Each data row is one old page; `title` names the old page in the before/after table.
- **Quote bank** (`kickoff/<slug>/<slug>-quote-bank.md`). The table `| # | Quote | Speaker | Timestamp | Use for |`; `#` is the number the approvals file refers to. `Quote` is copied word for word; `Timestamp` and `Use for` are read but not printed.
- **Keyword research** (the last-named `research/keyword-research/*.md` that has a `targets:` block). Each distinct `primary_keyword` in the block is one keyword targeted.
- **Reference kit** (`client-reference/<client-slug>/`: `brand.md`, then `style.md`). Every line with a hex value (`#1E4D7B` or `` `#1E4D7B` ``) is a colour: the text before the hex is its name, the text after it is its use, and a trailing `[internal] ...` source tag is dropped. A line that says retired, `Retired, do not use`, do not use or no longer is listed under the brief's colours as not to use.
- **Client context** (`kickoff/<slug>/<slug>-context.md`). `Client:`; under `## Snapshot`, `- Website:`, `- Service area:` and `- Primary contact:` (the name before the first comma is who the AM asks for a quote).
- **Launch date.** `--launch YYYY-MM-DD`, else the first `YYYY-MM-DD` on the `Launch:` line of `emails/<slug>/<slug>-go-live-email.md`. With neither, the scaffold refuses and writes nothing: ask the PM for the date.
- **Live address.** The `Live:` line of the newest `qa/<slug>/<slug>-launch-check-<date>.md`, else `https://` plus the context's `Website`.

## Approvals file

`case-study/<slug>/<slug>-approvals.md`, written when the AM reports the client's answer. Four lines:

```
Client: Kestrel Garage Doors
Featured: yes
Approved quotes: 3, 8
Approved by: Mira Halvorsen, 2026-11-24
```

- `Featured:` is `yes`, `no` or `not asked`. With `no` the script writes nothing and the check fails: the client declined.
- `Approved quotes:` lists quote-bank numbers, or `none`.
- `Approved by:` is who approved and the date.

Quote approval and feature consent are separate answers: approved quotes are used even while `Featured:` is `not asked`, and the `> AM:` note stays until consent is confirmed.

Without the file, consent is `not confirmed` and no quote is approved.

## Metrics file

`case-study/<slug>/<slug>-metrics.md`, for the 90-day re-run. The figures come from the AM or SEO (Search Console, GA4, call tracking); never fill it with estimates.

```
Client: Kestrel Garage Doors
Measured: 2027-02-18
Compared: the 90 days after launch (2026-11-18 to 2027-02-15) with the 90 days before it
Source: Google Search Console and GA4

| Metric | Before | After |
|---|---|---|
| Organic clicks | 412 | 1,038 |
| Phone calls from the site | 37 | 96 |
```

Every figure in Results must be one of the table's figures (or a date in the file). A Quick Stats bullet may lead with one.
