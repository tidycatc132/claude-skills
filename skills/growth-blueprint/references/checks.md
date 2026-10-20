# Checks

`python3 scripts/blueprint.py check --slug <slug>` prints `| Check | Result | Detail |` and a final `RESULT:` line. A row is `pass`, `FAIL` or `needs input`. `RESULT: FAIL` if any row fails (exit 1); otherwise `NEEDS_INPUT` if any row needs input; otherwise `PASS` (exit 0 for both).

| Check | Rule | Usual fix |
|---|---|---|
| input context, package, quotes, Reference Kit | the Week 1 files exist | `needs input` only; name the missing file in the answer |
| sections and order | the eight `##` sections, exactly, in order, no others | rename or move the heading; put extra material under a `###` |
| no [WRITE] placeholders left | every `[WRITE: ...]` replaced | write the section |
| Source: line per section, files exist | the last non-empty line of each section is `Source: a; b` and it is the section's only `Source:` line, each path exists relative to the working folder; `Source: none` only with a `[NEEDS INPUT: ...]` line | fix the path or add the file actually used |
| keyword tiers match the keyword report | the rows under `### Tier 1/2/3` equal what the script derives from the scored CSV and targets CSV | restore the copied table; scaffold again with `--force` if it was edited |
| sitemap copied from the sitemap report | every row of the report's URL map table appears in the section; `needs input` when the report has no URL map and the section says so | restore the table; for a missing URL map, ask SEO to re-save the sitemap report with it |
| page count within the scope cap | `Page count: N` equals the report's countable pages, and N is at most the context's `SOW pages:` | if over the cap, the sitemap report must change (site-structure-optimizer); `needs input` when the context has no number |
| every figure appears in a named source | each figure in a section is found in a file on its `Source:` line or in the two copied sections | add the source file that holds it, copy the figure exactly as the source gives it, or remove it |
| quoted lines are verbatim from their sources | each `> ` line (or the quoted part of it) appears word for word in a `Source:` file | copy the exact words; quotes are never tidied |
| Growth Strategy has Phase 1, 2, 3 and Trajectory | `### Phase 1`, `### Phase 2`, `### Phase 3`, `### Trajectory` in that order | restore the subheadings |
| no internal jargon in client prose | outside tables: no `AM` (times such as `7 AM` are fine), `TOFU`/`MOFU`/`BOFU`, `P0` to `P3`, `slug`, `NEEDS_INPUT`, `SE Ranking` | say it in plain words |
| open [NEEDS INPUT] flags | lists them | report them; they are not errors |
| briefing checks | sections in order, 3 to 5 summary bullets, 3 or 4 bets, at least one number, 5 `Q:` lines each with an `A:` line, framing present, at most 500 words, every figure in the Blueprint | edit the briefing |

## What counts as a figure

A number token, with `$`, `%`, commas and decimals. Not counted: single digits 0 to 9 written bare (counts and ordinals), numbered-list markers, ISO dates, numbers in headings and in `Source:` lines, numbers inside `[NEEDS INPUT: ...]`, inline code, web addresses, `.md` and `.csv` file names and paths starting with `/`, and time labels such as `Phase 2`, `Tier 1`, `months 1 to 3`, `3, 6 and 12 months`, `Week 4`. Matching ignores commas, `$` and trailing decimal zeros, so `9,900` matches `9900`; a percentage only matches a source percentage (`54%` matches `54.0%` or `54 percent`).

A figure the sources do not hold, such as a total you added up, a percentage you worked out or a target, fails the check. Write the claim without the number, or name a source that states it.
