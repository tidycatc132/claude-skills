# Slide guide

The plan is `blueprint/<slug>/<slug>-deck-plan.json`: `client`, `date` (YYYY-MM-DD, shown on the cover), `agency`, and `slides`, a list in this fixed order. Slide numbers below are the deck's page numbers (the compliance file uses them too).

| # | `id` | Slide |
|---|---|---|
| 1 | `cover` | Cover |
| 2 | `diagnosis` | The Diagnosis |
| 3 | `cost` | What This Costs You |
| 4 | `told-us` | What You Told Us |
| 5 | `divider` | Section 01 |
| 6 | `stand-today` | Where You Stand Today |
| 7 | `competitors` | Who You're Up Against |
| 8 | `threats` | Which Competitors Actually Matter |
| 9 | `keywords` | What You'll Rank For |
| 10 | `top-keyword` | Why Your Top Keyword Isn't Month One |
| 11 | `divider` | Section 02 |
| 12 | `positioning` | How You'll Be Positioned |
| 13 | `site` | The Site We're Building |
| 14 | `not-doing` | What We're Not Doing |
| 15 | `divider` | Section 03 |
| 16 | `has-to-be-true` | What Has To Be True |
| 17 | `measure` | How We'll Measure This |
| 18 | `team` | Your Team |
| 19 | `next` | What Happens Next |

## Fields every content slide has

- `eyebrow`: the slide's topic, set by the scaffold. Leave it.
- `headline`: the conclusion, one full sentence of 4 or more words, at most 100 characters, not a question. Write it as what the client should take away.
- `notes`: `say` (what the AM says, two to four sentences), `emphasise` (the one number or point to land, copied from the Blueprint), `pushback` (the doubt or objection the client is likely to raise on this slide, such as "why not the head term first?", and a one-line answer; not a simple lookup question). Every slide needs all three, cover and dividers included. The script joins them as `Say:`, `Emphasise:` and `Likely pushback:` lines.

A stat is `{"value": "1,300", "caption": "monthly searches for emergency dentist boise"}`: the value as written in the Blueprint (at most 12 characters), a caption of at most 70. Aim for 5 to 8 stats across the deck (`diagnosis`, `cost`, `stand-today`, `top-keyword`, `site`).

## Slide by slide

**`cover`**: `title`, `prepared_for`, `by` are filled; write only the notes.

**`diagnosis`**: the primary constraint as the headline, without its figure (the figure is the stat below it): the one thing holding the client back today, stated as a problem ("New patients searching for emergency care in Boise cannot find you"), not the opportunity it opens (that belongs on later slides). One clause: do not join a competitor comparison or a second problem with "while" or "and". `stats`: exactly one, the figure that proves that constraint (not a figure about a different problem). `body`: at most two short lines that explain the same constraint; a second problem belongs on slide 3. Draw from the Executive Summary and the biggest gap in Competitive Analysis or Keyword Opportunity.

**`cost`**: the consequence in business terms. `stats`: 2 or 3. `body`: optional, at most one line. From Competitive Analysis (traffic share, gaps) and Business and Market Overview (goals, conversions).

**`told-us`**: `quotes`: 3 or 4, each `{"text", "speaker", "date", "drives"}`. `text` is a whole `Quote` cell copied word for word (the script adds the quotation marks; part of a quote fails), `speaker` is that row's `Speaker`, `date` is the bank's `Call date:`, `drives` is what the quote shapes in a few words (priority, positioning, what to avoid); any figure in it is checked like the rest of the slide. Pick quotes that explain a decision in the plan.

**`divider`**: `number` and `headline` are set ("Where you stand today", "The plan", "Making it work"). You may sharpen the headline; write the notes.

**`stand-today`**: current presence as 2 or 3 stats: site page count, indexed pages, structured data, Google rating and review count, top-10 keywords, but only the ones the Blueprint states. `body`: optional, at most two lines.

**`competitors`**: `table` is the Blueprint's competitor table, copied cell for cell with the client column first. Do not edit it. `caption`: one line, such as which figures are estimates. With no competitor report the slide has `needs_input` instead of a table; keep it.

**`threats`**: `items`, one per competitor in the table: `name`, `grade` (exactly `Real threat`, `Overstated` or `Not a competitor`) and `why` (one line, at most 220 characters). Be direct about the ones that only look intimidating. With no competitor report this slide also carries `needs_input`, and no grades.

**`keywords`**: `table` is copied from the Blueprint's tiers (Tier 1 up to 8 rows, Tier 2 up to 4, Tier 3 up to 3) with `Keyword`, `Monthly searches`, `Difficulty`, `Intent`, `Tier`, `Time to result`. Do not edit it. The deck has no current-rank column because the Blueprint carries none. `caption` says how many more keywords the Blueprint lists.

**`top-keyword`**: the client's most aspirational keyword (often the highest-volume Tier 2 or Tier 3 row). `keyword`, `tier` (its tier and timing in words), `stats`: one (its monthly searches or difficulty), `points`: 2 to 4 plain-language lines on the trade-off, from Growth Strategy. This slide prevents a hard conversation in month three.

**`positioning`**: headline is the primary differentiator. `points`: 2 or 3 proof points from Strategic Positioning (approved claims, differentiators). `message`: the primary message line the homepage will carry, from Strategic Positioning (positioning statement or the homepage lead), at most 150 characters.

**`site`**: `stats` holds the page count copied from the Blueprint's `Page count:` line; leave the value. `pages` is copied from the URL map; set each `type` to `home`, `service`, `location`, `about`, `contact`, `resource` or `other`. The deck colours pages by type.

**`not-doing`**: `items`: 2 to 5, each `what` (a declined service, channel or client ask, at most 60 characters; style rules such as no superlatives are not items), `why` (the full reason in a sentence, at most 220) and `revisit` (the event that would make it worth revisiting, such as a scope change or a milestone, at most 120; never "not planned"). From the scope notes, Growth Strategy and any client ask the Blueprint says the scope does not cover. This is the credibility slide: keep the reasoning.

**`has-to-be-true`**: `client` and `wise` lists, each item `item`, `owner` (a name or the business), `blocks` (what it holds up), `needed_by` (a date when a source gives one, otherwise a named moment such as "before content review"). From Measurement and Next Steps and open items. Client-owned and WISE-owned items are drawn in separate panels.

**`measure`**: `table` columns are fixed: `Metric`, `Baseline today`, `3 months`, `6 months`, `12 months`, at least 2 rows. Baselines come from the Blueprint (or "Not tracked yet"); the three target columns are directions in words, never a number the Blueprint does not hold. The script adds the "Targets are directional" label.

**`team`**: `people`, each `name`, `side` (`client` or `wise`), `role`, `owns`. The scaffold fills names from the quote bank's speakers and `Agency speakers:`. Every name must appear in the Blueprint, quote bank, context or a `--source` file; otherwise write `[NEEDS INPUT: name of the WISE account manager]`. Up to four per side. Roles come from the same files or are `[NEEDS INPUT: ...]` too. The pushback here is a doubt about ownership or speed (who signs off, what happens if someone is away), not "who do we call".

**`next`**: `actions`: 5 to 7, each `action` (a verb first, at most 100 characters), `owner` (a name), `timing`. Actions, not a summary; the first is what happens on Monday. From Measurement and Next Steps.
