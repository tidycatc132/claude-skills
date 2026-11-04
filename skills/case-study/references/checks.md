# Checks

`case_study.py check` prints one row per check and `RESULT: PASS` only when every row passes.

| Check | What it tests | Usual fix |
|---|---|---|
| `header` | The six header lines are first and match the sources (client, launch date, consent and approved quotes from the approvals file) | Re-run scaffold with `--force` if the approvals or launch date changed, then rewrite the prose |
| `consent note` | A `> AM:` line about being featured sits above the headline | Put the scaffold's note back |
| `sections` | One `# ` headline, then the seven `##` sections in order | Restore the heading names and order |
| `placeholders` | No `[WRITE: ...]` slot is left | Write the slot |
| `numbers` | Every number from the headline down is a script count, 90, or appears in a source file | Use the script's count, or remove the figure |
| `counts by noun` | A number written next to what it counts (`<n> service pages`, `<n> location pages`, `<n> keywords`, `<n> words`, `<n> old URLs redirected`, `<n> pages`) equals the script's count for that thing (bare pages may also be the old site's count or a context figure) | Use the count the scaffold printed for that noun |
| `what we built` | What We Built states the pages built and words written | Keep the script's bullets |
| `quick stats` | 4 to 6 bullets, each led by a count (or a metrics figure) | Lead each bullet with one of the counts printed by scaffold |
| `results` | At launch: "too early", 90 days, no other figure, no percentage. With metrics: at least one metrics figure and no figure outside the file | Follow the Results slot in the writing guide |
| `quote` | No unapproved quote-bank quote appears anywhere; with approvals, one approved quote is used word for word with its speaker; without, the `QUOTE NEEDED:` line has a question | Copy the approved quote exactly, or keep the placeholder |
| `no hype` | None of the script's hype words, and no promise or multiple wording (ranks first, will rise, doubled, 3x, guarantee), in either file | Say what was done, or quote the metrics file's figures |
| `no structured data` | No structured data, schema, JSON-LD or rich result wording, in either file | Remove it |
| `no internal terms` | No QA, BugHerd, SOW, tiers, ClickUp, file names or folder paths in the narrative | Rewrite in plain words |
| `length` | Narrative body at most 900 words | Cut the Challenge and Approach first |
| `brief layout` | Brief header lines and the five sections in order | Re-run scaffold with `--force` |
| `brief tables` | Pages to Screenshot, Before and After and Brand Colours equal what the script builds from the sources | Do not edit these tables; fix the source file and re-scaffold |
| `brief colours` | Every hex in the brief comes from the kit or the index palette | Use only the table's colours |
| `callout stats` | 3 to 6 bullets, each led by a Quick Stats figure | Copy from Quick Stats |
| `layout` | The Layout Suggestion is written | Write it |
