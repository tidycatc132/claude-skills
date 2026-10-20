# Checks

`build` prints one table and writes it to `<slug>-deck-compliance.md`. The first five rows come from reading the finished `.pptx`; `check` runs only those five on any deck. `FAIL` anywhere means `RESULT: FAIL` and no deck is written; an open `[NEEDS INPUT: ...]` with no failures means `RESULT: NEEDS_INPUT` and the deck is written; `WARN` does not change the result.

## Deck checks (read from the .pptx)

| Row | Rule | Usual fix |
|---|---|---|
| `em-dashes` | No U+2014 (or the two- and three-em dashes) on any slide or in any notes. The count is in the detail; each hit is listed under Hits with slide and shape. | Rewrite the sentence with a period, comma or colon. |
| `prescribe` | No word starting with `prescri`, any case. | Use recommend, our recommendation, the plan, what we'd do first. |
| `figures` | Every figure is in the Blueprint (see below). Each one is listed under Figures by slide with yes or no. | Copy the figure exactly as the Blueprint writes it, or drop it. Never round 1,300 to "over a thousand" to dodge the check; leave it out instead. |
| `quotes` | A quote card holds one whole `Quote` cell from the quote bank, word for word. Any other quoted run must be a whole quote or whole sentences of one. A line the Blueprint quotes from the Reference Kit is not a client quote. | Copy the quote bank cell exactly, or drop the quotation marks from a line that is not the client's. |
| `speaker notes` | Every slide has notes. | Fill `notes.say`. |
| `needs input` | Lists slides that show a `[NEEDS INPUT: ...]` line. | Not an error: name who can supply each item in your answer. |

**What counts as a figure.** Any number of two or more digits, any decimal, any amount with `$`, any percentage. Single digits, page numbers, the footer, the cover date, divider numbers, ISO dates (`2026-10-09`) and timeline labels (`3 months`, `months 4 to 6`, `12-month`, `Tier 2`, `Phase 1`: 1 to 12, 18 or 24 before months or weeks) are not figures. Other durations are (`90 days`, `40 years`). A figure matches when the same number, ignoring thousands commas, appears in the Blueprint outside a date; money only matches money and a percentage only a percentage.

**What counts as a quote.** In a deck built by this script, the text of each quote card. In any deck, also any run of six or more words inside quotation marks, on a slide or in the notes.

## Plan checks (build only)

| Row | Rule | Usual fix |
|---|---|---|
| `date`, `slide order` | `date` is YYYY-MM-DD; the 19 `id`s are in the order of `slide-guide.md`. Either failing stops the build before rendering. | Scaffold again with `--force` and copy your text across. |
| `placeholders` | No `[WRITE: ...]` left. The detail names the fields. | Write them. |
| `headlines` | Each content slide's headline is 4 or more words, not the slide's label, not a question. | State the conclusion. |
| `notes fields` | `say`, `emphasise`, `pushback` on every slide, cover and dividers included. | Fill them. |
| `diagnosis: one stat`, `diagnosis: two lines at most`, `cost: 2 to 3 stats`, `stand today: 2 to 3 stats`, `told us: 3 to 4 quotes`, `not doing: 2 to 5 items`, `next steps: 5 to 7 actions`, `positioning: 2 to 3 proof points` | Counts per slide. A slide with a `needs_input` line is exempt. | Add or cut items. |
| `quote attribution` | Each quote's `speaker` is the quote bank row's speaker and `date` is the bank's `Call date:`. | Copy both from the quote bank. |
| `competitor table` | The slide's table equals the Blueprint's first `Competitive Analysis` table cell for cell. `NEEDS_INPUT` when the Blueprint has none and the slide keeps its `needs_input` line. | Scaffold again; never edit the table. |
| `threat grades` | Every competitor graded `Real threat`, `Overstated` or `Not a competitor`. | Use one of the three exactly. |
| `keyword table` | Every row's keyword, monthly searches, difficulty and tier are in the Blueprint's tier tables. | Scaffold again. To change tiers, change the Blueprint first. |
| `page count` | The site slide's stat equals the Blueprint's `Page count:` number. | Copy it back. |
| `page types` | Each page `type` is one of the seven types. | Fix the type. |
| `measure table` | Fixed columns and at least 2 metrics. | Add a metric. |
| `has to be true` | At least one client item and one WISE item, each with `item`, `owner`, `blocks`, `needed_by`. | Fill the missing fields. |
| `next steps: owner and timing` | Every action has both. | Fill them. |
| `team names` | At least one client and one WISE person, every name found in the Blueprint, quote bank, context or a `--source` file. | Use the name as a file writes it, pass the file that names them with `--source`, or write `[NEEDS INPUT: ...]`. |
| `big numbers` | 5 to 8 stats across the deck; `WARN` only. | Add a stat on stand-today or cost, or drop one. |
| `fits the slides` | Text fields stay under their character limits (headline 100, caption 70, quote 220, point 150, action 100, message 150, and others listed in the detail). | Shorten the field; never shrink the font. |
