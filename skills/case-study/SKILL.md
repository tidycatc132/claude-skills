---
name: case-study
description: Writes the WISE case study narrative and the showcase design brief for a launched website build, from the build's own files. A script counts pages built by type, words written, keywords targeted and old URLs redirected, fills the snapshot, stats, screenshot list, before and after pairs and brand colours, and checks that every number matches a count or a source file, that a client quote is used only when approved for public use, and that Results waits for 90-day metrics. Use when the AM or PM asks for a case study, showcase write-up, portfolio piece or success story for a client whose site has launched, the design brief behind the showcase assets, or a refresh of a case study with 90-day results. Do NOT use for the Growth Blueprint (use growth-blueprint) or its deck (use blueprint-deck), design briefs for the site itself (use homepage-design-brief or page-type-design-briefs), the close-out package or transition email (use project-close-out), or the go-live email (use week-6-go-live-email).
---

# Case study

After launch, WISE tells the story of the build: what the client's old site lacked, what we chose to do, what we built, and (90 days later) what changed. Every fact is already in a file the build saved. The script `scripts/case_study.py` counts and copies; you write the prose around its numbers, in WISE's voice, and the script checks it. Finish only on `RESULT: PASS`.

## Inputs

Paths are relative to the client's working folder. `<slug>` is the client's folder name under `kickoff/` and `handoff/`; `<client-slug>` is the folder under `client-reference/` (found automatically when there is only one).

| Path | Required | Used for |
|---|---|---|
| `handoff/<slug>/<slug>-dev-handoff-index.md` | yes | dev-handoff-index: pages by type (`Homepage`, `Service Pages`, `Location Pages`, `About Page`, `Contact Page`, `Resource Pages`, `Pages Without a Template`), each page's `Page`, `URL`, `Content file` and `Priority`; the `### Redirects` table (`Old URL`, `New URL`); the design `### Colour palette` when the kit has no colours |
| `kickoff/<slug>/<slug>-context.md` | yes | new-build-kickoff / client-context-update: `Client:`, the `## Snapshot` lines (`Website`, `Service area`, `Primary contact`), Business Overview and Website Today |
| `content/<url-slug>/article.md` | per page | seo-content-writer: the words written, for every `Build` page named in the index |
| `kickoff/<slug>/<slug>-url-inventory.csv` | no | new-build-kickoff: the old site (`url`, `title`) for the old page count and before shots |
| `kickoff/<slug>/<slug>-quote-bank.md` | no | kickoff-call-processing: `| # | Quote | Speaker | Timestamp | Use for |`. A quote is used only when the approvals file lists its `#` |
| `blueprint/<slug>/<slug>-growth-blueprint.md` | no | growth-blueprint: the challenge (Business and Market Overview), positioning and strategy (Strategic Positioning, Growth Strategy), the 90-day measures (Measurement and Next Steps) |
| newest `research/keyword-research/*.md` with a `targets:` block | no | keyword-research: the primary keywords targeted |
| `client-reference/<client-slug>/brand.md` and `style.md` | no | client-reference-kit: positioning and differentiators to draw on, and every colour line with a hex value; lines marked `Retired, do not use` (or retired) are listed as colours not to use |
| `case-study/<slug>/<slug>-approvals.md` | no | the AM's record of feature consent and approved quotes |
| `case-study/<slug>/<slug>-metrics.md` | no | the 90-day re-run figures |
| `emails/<slug>/<slug>-go-live-email.md`, newest `qa/<slug>/<slug>-launch-check-<date>.md` | no | the launch date (its `Launch:` line) when none is given; the live address (its `Live:` line), else the context's `Website` |

The approvals and metrics formats, and exactly what is read from each file: [Input Formats](references/input-formats.md). Read it when the AM gives consent, approved quotes or 90-day figures, so you can save them in the right file first.

## Outputs

Both in `case-study/<slug>/`, scaffolded by the script, prose by you:

- `<slug>-case-study.md`: header lines `Client:`, `Launch:`, `Written:`, `Feature consent:`, `Approved quotes:`, `Metrics:`; a `> AM:` note to confirm the client agrees to be featured; one `# ` headline; then `## Client Snapshot`, `## The Challenge`, `## The Approach`, `## What We Built`, `## Results`, `## In Their Words`, `## Quick Stats` (4 to 6 bullets, each led by a count), in that order.
- `<slug>-case-study-design-brief.md`: header lines `Client:`, `Case study:`, `Live site:`, `Colours from:`; then `## Pages to Screenshot` (`| Page | Page type | Live URL |`), `## Before and After` (`| Old page | Old URL | New page | Live URL |`, the old homepage plus every redirect with a target), `## Brand Colours` (`| Colour | Hex | Use | Source |`), `## Callout Stats` (3 to 6 of the Quick Stats), `## Layout Suggestion`.

## Running the script

`<skill-folder>` is the folder this SKILL.md is in; write its real path. Run each command from the client's working folder as one plain `python3` command with nothing chained before or after it (no `cd`, `&&` or pipes). If a call is denied, send the same plain command again; never count or copy by hand what the script does. Read files with the file tool.

## Steps

1. **Consent and approvals first.** If the AM says the client agreed to be featured, approved quotes, or gave 90-day figures, save them in the approvals or metrics file (format in the reference) before scaffolding. Never mark a quote approved on your own judgement.
2. **Scaffold.** `python3 <skill-folder>/scripts/case_study.py scaffold --slug <slug> --launch <YYYY-MM-DD>` (leave out `--launch` when the go-live email has the date; add `--client-slug` when there are several kits). It prints the inputs found, the counts and any warning, and writes both files with every count, table and colour filled and `[WRITE: ...]` slots for the prose. It writes nothing when the client declined (`Featured: no`) or there is no launch date (ask the PM), and it will not overwrite existing files without `--force`; to refresh a case study for 90-day results, use `--force` and rewrite the prose.
3. **Read** the inputs the scaffold names, then [Writing Guide](references/writing-guide.md).
4. **Write** each `[WRITE: ...]` slot in place, headline last. Do not edit the header, the script-made tables or the counts; reword the Quick Stats only around their numbers.
5. **Check.** `python3 <skill-folder>/scripts/case_study.py check --slug <slug> --launch <YYYY-MM-DD>` (same flags as the scaffold). Fix every `FAIL` row in the files and run it again until `RESULT: PASS`. [Checks](references/checks.md) says what each row tests and the usual fix.
6. **Answer** with the two paths, the check table and its `RESULT:` line exactly as printed, whether consent is confirmed, the quote used or the question suggested for the AM, and any warning the scaffold printed.

## Rules

- **Numbers come from the script or a source file.** Every figure in the narrative is a count the script printed, or appears in the context, Growth Blueprint, index, inventory, keyword report, kit, an approved quote or the metrics file. No sums, percentages or growth the files do not state.
- **Quotes need approval.** Use a quote-bank quote only when the approvals file lists its number, word for word. Otherwise leave the `QUOTE NEEDED:` line with one suggested question for the AM. Do not paraphrase an unapproved quote into the text either.
- **Results wait for data.** At launch, Results says it is too early and names what will be measured at 90 days. With a metrics file, report its figures exactly and say what period they compare.
- **WISE's voice.** Plain, specific sentences about this client: name the services, towns and pages. No hype words, no promises of rankings, traffic or leads. Client-facing: no internal terms (QA, BugHerd, SOW, tiers, file names).
- **No structured data, schema or rich result claims**, in either file.
- The `> AM:` consent note stays at the top until the AM publishes; the script never removes it.

## Scripts

| Command | Use |
|---|---|
| `scripts/case_study.py scaffold`, `check` | Write the two files; check them (exit 0 PASS, 1 FAIL or refused, 2 usage) |
| `scripts/case_study.py counts` | Print the counts and inputs as JSON without writing anything |
| `scripts/case_study.py index`, `quotes`, `kit`, `keywords`, `inventory` | Print, as JSON, what is read from a dev handoff index, a quote bank, a kit folder, a keyword report or a URL inventory (`--validate` checks such JSON); the contracts use them |
| `scripts/case_study.py contract <case-study.md>` | Print the narrative's header lines, headings and Quick Stats as JSON, for skills that read the case study |
| `scripts/selftest_case_study.py` | Cases on temporary copies of the Kestrel Garage Doors fixture; run after changing the script |

Standard-library Python 3 only.
