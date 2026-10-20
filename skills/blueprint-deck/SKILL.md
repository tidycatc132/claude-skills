---
name: blueprint-deck
description: Builds the branded WISE Growth Blueprint deck (16:9 PowerPoint with speaker notes) from a finished Growth Blueprint and the kickoff quote bank, and writes a compliance file that lists every figure by slide. Use when SEO or the AM asks for the Blueprint deck, slides or presentation for a client, to rebuild it after the Blueprint changed, or to re-check a deck someone edited by hand. A script copies the competitor table, keyword tiers and page count from the Blueprint, renders the deck and fails the build on any em-dash, any form of prescribe, any figure not in the Blueprint or any quote not word for word in the quote bank. Do NOT use for writing or changing the Blueprint itself or the AM Briefing (use growth-blueprint), benchmarking competitors (use competitor-analysis), a prospect audit for Sales (use prospect-digital-audit), or the quote bank from the Kickoff Call (use kickoff-call-processing).
---

# Blueprint deck

The deck is what the client forwards to a partner or a board member who was on none of the calls, so every slide has to stand on its own and every number has to match the Blueprint. The markdown Blueprint stays the record; the deck is the client deliverable and exports to PDF from PowerPoint.

You write the words in a JSON slide plan. The script copies the tables, renders the `.pptx` in WISE branding and runs the checks on the finished file. The checks are the script's, never your own report about the deck.

## Inputs and outputs

Paths are relative to the client's working folder; `<slug>` is the kickoff folder name.

| File | Path | Notes |
|---|---|---|
| Growth Blueprint (input) | `blueprint/<slug>/<slug>-growth-blueprint.md` | From growth-blueprint. Read by its `##` sections: `Executive Summary`, `Business and Market Overview`, `Competitive Analysis`, `Strategic Positioning`, `Keyword Opportunity`, `Site Architecture and Content Plan`, `Growth Strategy`, `Measurement and Next Steps`. |
| Quote bank (input) | `kickoff/<slug>/<slug>-quote-bank.md` | From kickoff-call-processing: a `Call date:` line and a table with `Quote` and `Speaker` columns. |
| Client context (optional input) | `kickoff/<slug>/<slug>-context.md` | Only used to confirm team names. Extra files that name people: `--source FILE`. |
| Brand | `assets/brand.json` and `assets/wise-logo.png` in this skill | WISE colours, Montserrat, logo. |
| Slide plan (you write it) | `blueprint/<slug>/<slug>-deck-plan.json` | |
| Deck (output) | `blueprint/<slug>/<slug>-growth-blueprint-deck.pptx` | 19 slides: the cover, 15 content slides and 3 section dividers. |
| Compliance file (output) | `blueprint/<slug>/<slug>-deck-compliance.md` | Check table, `RESULT:` line, every figure with its slide number, every hit. |

From the Blueprint the script reads the first table in `Competitive Analysis`, the `### Tier N` tables in `Keyword Opportunity`, and the `Page count: N` line and the table with a `URL` column in `Site Architecture and Content Plan`.

## Running the script

Run each command as its own plain `python3` command with paths as arguments: no `cd`, no `&&`, no pipes. If a command is denied, retry that exact plain command once before doing anything else; never hand-compute what the script does or write the compliance file yourself. Read files with the file-reading tool. `<skill-folder>` is this skill's own folder (where this SKILL.md is); write its real path into the command. Run from the client's working folder, or pass `--root <working folder>`. The script needs only the Python standard library.

## Workflow: build a deck

1. **Scaffold.** `python3 <skill-folder>/scripts/deck.py scaffold --slug <slug> --date <YYYY-MM-DD>` writes the plan with every slide in order, the cover filled in, the competitor table, keyword table, page count, page list and team names copied, and `[WRITE: ...]` placeholders for the rest. It prints `NEEDS INPUT` for any slide the Blueprint cannot fill. It will not overwrite a plan without `--force`.
2. **Read** the Blueprint and the quote bank in full, then `references/slide-guide.md` for what each slide holds and the plan's fields.
3. **Fill the plan.** Replace every `[WRITE: ...]`. Leave the copied tables, the page count and any `needs_input` line as they are. Fix a page's `type` if the guess is wrong.
4. **Build.** `python3 <skill-folder>/scripts/deck.py build --slug <slug>` checks the plan, renders the deck, re-reads the finished `.pptx` and writes the compliance file. A `FAIL` writes no deck; a deck already in the folder from an earlier build is left untouched, so never send it until a build passes. Fix the plan, never the check, and build again. `references/checks.md` says what each row tests and how to fix it.
5. **Answer** with the deck and compliance paths, the final `RESULT:` line copied exactly (`RESULT: PASS`, `RESULT: NEEDS_INPUT` or `RESULT: FAIL`), every open `[NEEDS INPUT: ...]` with who can supply it, and a reminder that the SEO checks slide 2 (one constraint) and the competitor figures before the AM sends it.

## Workflow: re-check an edited deck

When someone changed the `.pptx` by hand, run `python3 <skill-folder>/scripts/deck.py check --slug <slug>` (or `--pptx <path>`). It reads the slide and notes XML, runs the em-dash, prescribe, figure and quote checks, rewrites the compliance file and never edits the deck. Report the hits by slide; fix them only if asked, and then in the plan with a rebuild, or tell the person which slide to change by hand.

## Rules

- **Figures come from the Blueprint.** Every number on a slide or in the notes (counts of 10 and up, decimals, money, percentages) must appear in the Blueprint as written there. No rounding, sums, restating or new targets. If a number is not in the Blueprint, leave it out.
- **Quotes are word for word** from the quote bank: a whole `Quote` cell, with that row's speaker and the bank's call date. Do not tidy grammar or trim mid-sentence. If a quote contains an em-dash, pick another quote.
- **No em-dashes** anywhere, notes included. Use a period, comma or colon. En-dashes in ranges are fine.
- **Never any form of "prescribe"** (prescribed, prescriptive, prescription). Say recommend, our recommendation, the plan.
- **Headlines state conclusions.** "Nobody in Boise owns emergency dental search yet", never "Competitive Landscape". The slide's topic is its `eyebrow`, which the script sets.
- **One idea per slide.** Slide 2 names one constraint, not a list.
- **Missing input stays visible.** No competitor report means both competitor slides show the Blueprint's `[NEEDS INPUT: ...]` line and no competitor figure appears anywhere in the deck. A team member no file names is `[NEEDS INPUT: name of ...]`.
- **Directional only.** The measurement slide says what should move, never a promised number; the script labels the targets directional.
- **No technical-foundation slide** while the schema baseline and ADA review are outside the build process.

## References

- `references/slide-guide.md`: read at step 2. Every slide in order with its plan fields, what it says and where in the Blueprint it comes from, and the speaker-notes fields.
- `references/checks.md`: read at step 4, or whenever a row fails. Every check, its rule and the usual fix, and how figures and quotes are recognised.
