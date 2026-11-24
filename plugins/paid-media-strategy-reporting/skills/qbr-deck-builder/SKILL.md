---
name: qbr-deck-builder
description: Plan and build a quarterly business review (QBR) deck for a paid media client, with a narrative arc from goals to results, what drove them, learnings, the strategy for next quarter, budget and forecast, and the decisions needed, using computed quarter-over-quarter and year-over-year data and delivered as a slide deck. Use whenever the user asks for a QBR, quarterly review, quarterly business review, quarterly strategy presentation, or a client presentation covering a quarter of paid media, even if they only say we need slides for the client meeting.
---

# QBR Deck Builder

A quarterly review is where a client decides whether to keep investing, change direction, or raise the budget. The deck should tell one story across the quarter, prove it with data the client can trust, and end with a clear plan and decisions. It is a conversation guide, not a data dump.

## Principle: story first, slides second
Settle the narrative and the numbers before opening a slide tool. Each slide makes one point, titled as the conclusion ("Cost per lead fell 18% after the landing page rebuild"), supported by one visual.

## Inputs
- Three months of platform and analytics data, prior quarter and prior year for comparison
- Monthly reports from the quarter, change log, test log, goals and economics
- `clients/<slug>/context.md`, brand assets for the deck
- Upcoming plans: budget proposals, launches, seasonality

## Process
1. **Build the numbers first** in code: quarter totals, quarter-over-quarter and year-over-year changes, trends by month, results by campaign and channel, funnel from spend to revenue, efficiency against the allowable CPA. Reconcile to platform totals. Save to a data workbook.
2. **Write the story in five sentences:** where we started, what we set out to do, what happened, why, and what we propose next. Every slide serves one of these.
3. **Outline the slides** (about 12 to 15, plus appendix):
   1. Title and agenda
   2. Goals and executive summary: outcome versus goal
   3. Quarter scorecard
   4. Trend by month, with annotations of key changes
   5. What drove results (volume, efficiency, conversion rate effects)
   6. Channel and campaign performance
   7. Wins and what we learned (from the test log)
   8. Problems and what we did about them
   9. Audience, creative, or landing page insights
   10. Competitive and market context (auction insights, trends)
   11. Next quarter strategy and priorities
   12. Test roadmap
   13. Budget and forecast with scenarios
   14. Risks and dependencies
   15. Decisions needed and next steps
   Appendix: definitions, detailed tables, methodology.
4. **Design the visuals:** one chart per slide, titled with the takeaway, labeled axes, comparison periods, no clutter. Use the dataviz guidance for chart choices and color.
5. **Write speaker notes** for each slide: the point, the evidence, and likely client questions with answers.
6. **Check the deck:** every number on a slide matches the workbook, comparisons use consistent periods, slide titles read as a story when read alone, and bad news is shown plainly with a plan.
7. **Build the deck** in the format the user asks for (an editable slide artifact by default, or a .pptx file when named), and deliver with the data workbook.

## Output
`clients/<slug>/outputs/YYYY-Qn/qbr-deck` (the deck), `qbr-data.xlsx`, and `qbr-notes.md` with the narrative and speaker notes.
```
Narrative summary (five sentences).
Slide outline with titles.
The deck, speaker notes, data workbook.
Open items needing client input before the meeting.
```

## Rules
- Never present a number that is not traceable to the data workbook.
- Show misses and what is being done; a QBR that hides problems loses trust.
- Keep forecasts as ranges with stated assumptions.
- Ask for the deck format only if it affects the build; otherwise default to an editable slide artifact.
