---
name: new-build-kickoff
description: Day 1 kickoff for a new WISE website build. Use when onboarding a newly closed website client from the Sales handoff, or someone says "kick off [client], [URL], [service area]", "start the new build for", "new build kickoff" or "spin up Week 1 for", with the Sales transcript(s) and signed Scope of Work (SOW), with or without a current website. Reads them, crawls the site, and writes kickoff/[slug]/ with a source-tagged client context quoting the SOW page count, a URL inventory CSV, 3 to 5 gap questions for the intake form, short Project Instructions, the Week 1 setup checklist, and a paid media brief only when the SOW includes paid media. Do NOT use for the brand, voice, style, audience or compliance files (use client-reference-kit), sitemap or page planning (use site-structure-optimizer), keyword research (use keyword-research), competitor benchmarking (use competitor-analysis), or later Week 1 steps such as the welcome email or processing the Kickoff Call transcript (not covered by this skill).
---

# New Build Kickoff

Turns what Sales hands over into the files a new client's Claude Project starts from. Everything is checked by `scripts/check_kickoff.py`; the run is done when it prints `RESULT: PASS`.

## Inputs

Required: client name, website URL or "no website", service area, at least one Sales call transcript, and the signed SOW. If the SOW or every transcript is missing, ask for it and stop; do not guess scope. Optional: competitor URLs, a Google Maps link, discovery notes, pre-sale audit findings.

## Output

Folder `kickoff/<slug>/` containing exactly:

- `<slug>-context.md`
- `<slug>-url-inventory.csv` (columns `url`, `title`, `page_type`, `status`, `source`)
- `<slug>-gap-questions.md`
- `<slug>-project-instructions.md`
- `<slug>-setup-checklist.md`
- `<slug>-paid-media-brief.md`, only when the SOW includes paid media

No brand brief (client-reference-kit builds the brand and voice files later in Week 1) and no review baseline. The exact layout of every file is in [File Specs](references/file-specs.md); read it before writing anything.

## Steps

Work from the working directory, where `kickoff/` is created. Call each script by its path inside this skill's folder, for example `python3 <skill-dir>/scripts/check_kickoff.py ...`, as one plain `python3` command with file paths as arguments. Never chain, pipe or `cd`, and do not explore with `ls` loops. If a Bash call is denied, run the same script again as a single plain `python3` command; do not stop or hand-write a script's output.

1. **Slug and scope.** `python3 <skill-dir>/scripts/check_kickoff.py --slug "<Client Name>"` gives the slug. `python3 <skill-dir>/scripts/check_kickoff.py --paid-media <sow file>` says whether the paid media brief is needed (it ignores anything listed under "Not included").
2. **Read the sources.** Every transcript in full, the SOW, any notes. For the site: if a saved copy is provided, read it and treat it as the crawl. Otherwise fetch the home, about, services and contact pages and `/sitemap.xml` with the web fetch tool; if no fetch tool is available, ask for a saved copy or a page list and stop. With no website, skip this and say so in the context.
3. **URL inventory.** Build it with `python3 <skill-dir>/scripts/make_inventory.py --out kickoff/<slug>/<slug>-url-inventory.csv --base <site URL>`, plus `--html-dir` for saved pages, `--sitemap` for a saved sitemap file, or `--urls` for a list you wrote from a live crawl (put that list outside `kickoff/<slug>/`). Use `--out ... --no-website` when there is no site. Fix a wrong page type with `--type URL=page_type`, never by editing the CSV.
4. **Context.** Write `<slug>-context.md` per the spec. Tag every fact with its source; write `GAP:` where nothing answers; write `CONFLICT:` where sources disagree, and follow the SOW on scope. The page count in `SOW pages:` comes from the SOW even when Sales said something else.
5. **Coverage and gap questions.** Assess R1 to R10 in [Week 1 Requirements](references/week-1-requirements.md) against the sources, fill the coverage table, and ask only about open items, 3 to 5 questions. Never ask what the intake form already collects (the list is in that file).
6. **Instructions, checklist, paid media.** Write `<slug>-project-instructions.md`, `<slug>-setup-checklist.md` from [Week 1 Sequence](references/week-1-sequence.md) (copy the step titles exactly), and the paid media brief if step 1 said `yes`.
7. **Check.** `python3 <skill-dir>/scripts/check_kickoff.py kickoff/<slug> --client "<Client Name>" --sow <sow file>` (add `--no-website` when there is no site). Fix every FAIL in the files and rerun until `RESULT: PASS`.

## Answer

In chat, give: the folder path and file list, the checker table and result line, the gap questions as written, any `CONFLICT:` bullets, and the next step for the AM: review the gap questions, then set up the Claude Project with these files, the transcript(s) and the SOW.
