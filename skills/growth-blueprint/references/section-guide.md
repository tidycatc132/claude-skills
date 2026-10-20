# Section guide

What each section holds and where it comes from. The Blueprint is client-facing prose: confident, specific, short paragraphs, tables where they help. Every figure carries its source in the section's `Source:` line.

## Growth Blueprint

### Executive Summary (write last)
Three to five short paragraphs or bullets: the biggest opportunity, the competitive opening, what the new site does about it, and what happens next. Each point carries one figure from a named source. Name the files the figures came from on the `Source:` line (often the context, the keyword report, the sitemap report and the competitor report).

### Business and Market Overview
Who the client is, what they sell, where, to whom, and what they want from the site: from `<slug>-context.md` (Snapshot, Business Overview, Services, Customers and Service Area, Goals and Conversion) and the Blueprint Input Package (Services Priority, Audiences, Service Area Tiers, Goals and Success Measures). Market factors only when a source states them; regulated industries get one line from `compliance.md`. A client's own goal ("twenty more new patients a month") may be reported as their goal, attributed to them, never restated as a commitment.

### Competitive Analysis
From the saved competitor-analysis report: who the competitors are, the comparison table (client column first, figures copied with their labels such as estimates), what to learn from them and where the openings are. Name competitors the Blueprint Input Package lists that the report does not cover. With no report, the section is one `[NEEDS INPUT: a saved competitor-analysis report for <competitors from the package>]` line, the `Source:` line names the package (or `none`), and no competitor figure appears anywhere in the Blueprint.

### Strategic Positioning
Quote, then apply. From `brand.md` (`## Core Positioning`, `## Key Differentiators`, `## Approved Claims & Proof Points`), `voice.md` (`## Voice Dimensions`), `audience.md` (`## Key Personas`, `## Core Pain Points`) and the quote bank. Put the positioning statement and the client's own words in `> ` lines, verbatim. Then say what each means for the site: which differentiator leads the homepage, which proof points back which pages, what not to compete on. Do not write new voice rules, a new messaging hierarchy or new personas; those belong to the Reference Kit.

### Keyword Opportunity (copied)
Filled by the script from the scored CSV. Tier 1 is every scored keyword that is a build page's `primary_keyword` in the sitemap targets CSV, whatever its report tier, because the page is being built (or the report's `P0` keywords when there is no targets CSV); Tier 2 is the remaining `P0` and `P1` keywords; Tier 3 the remaining `P2`. Other `P3` (Monitor) and `N/A` keywords are left out. Each tier shows at most 15 rows in file order, with a line naming how many more are in the report. You may add one or two sentences above the tables on what the tiers mean for this client; never edit, re-order or re-tier the rows. To move a keyword between tiers, change the keyword report or the sitemap, then scaffold again.

### Site Architecture and Content Plan (copied)
Filled by the script: a `Page count:` line (the sitemap report's countable pages against the context's `SOW pages:`, with a sentence on which pages are not counted, since the table lists them too), the URL map table copied verbatim from the report and, when the targets CSV exists, a content plan table. You may add a sentence on how the structure serves the goals. If the client asked for more pages than the scope allows, say the sitemap follows the agreed scope; do not list the extra pages as planned.

### Growth Strategy
- `### Phase 1` (the build): what the new site establishes, tied to the Tier 1 keywords and the sitemap.
- `### Phase 2` (months 1 to 3): the Tier 2 keywords and the keyword report's content calendar.
- `### Phase 3` (months 4 to 6): the Tier 3 keywords and the authority gaps the competitor report shows (links, reviews, citations).
- `### Trajectory` at 3, 6 and 12 months: directional only. Say what should start to move and why, label it directional, and use no projected numbers.

### Measurement and Next Steps
What will be tracked (the context's primary conversion, rankings for the Tier 1 keywords, enquiries) and the next steps with an owner each (client, WISE). Open items the context or the package lists that the client owns (photos, access, approvals) belong here.

## AM Briefing (internal)

One page for the Account Manager who presents the Blueprint. Built from the finished Blueprint only: every figure in it must already be in the Blueprint.

- `## Executive Summary`: 3 to 5 bullets, the story in the order the AM will tell it.
- `## Key Strategic Bets`: 3 or 4 numbered bets, each with the reason and what would prove it wrong.
- `## Numbers the AM Should Know`: bullets, each a figure copied from the Blueprint with what it means.
- `## Anticipated Client Questions`: exactly 5, written as `1. Q: question?` with an indented `A: answer` line under each. Include the hard ones the sources predict: a page-count conflict, a timeline the client asked for, why the head keyword is not month one, what the client still owes.
- `## Calibration Framing`: how to set expectations. Which parts are directional, what depends on the client, and which client asks the scope does not cover (said plainly so the AM can redirect them).
