# Brief template

Fill every part. Section order is fixed, with two conditional moves: when `ymyl: true`, `## Author, Experience and Trust` comes first (right after the title) and does not appear again later; when `mode: refresh`, `## Refresh Audit` comes right after `## Page Goal`. `scripts/check_brief.py` enforces this shape.

The brief speaks to "the writer". Never name a tool, skill, model or system that will write the page.

## Front-matter

```
---
id: how-long-does-a-tankless-water-heater-last
brief_version: 1
status: DONE_WITH_CONCERNS
date: 2026-10-16
client: Harbor & Pine Plumbing
client_domain: harborpineplumbing.com
market: en-us, Portland, Oregon metro
language: en
page_url: /blog/how-long-does-a-tankless-water-heater-last/
mode: new
existing_url: N/A
primary_keyword: how long does a tankless water heater last
secondary_keywords: [tankless water heater lifespan, tankless vs tank water heater lifespan]
intent: Informational
funnel: TOFU
format: explainer
format_embedded: [faq]
format_source: explainer + FAQ
metrics: {volume: 1600, kd: 19, source: Measured}
geo_candidate: true
geo_answer_format: direct answer
cluster: Water heaters
pillar_url: /water-heaters/
ymyl: false
local: true
cannibalization: clear
voice_source: default/home-services
style_source: client
word_range: 1200-1800
client_inputs_open: 2
source_report: research/keyword-research/2026-10-14-water-heaters.md
---
```

Front-matter keys, all required, in this order: `id`, `brief_version`, `status`, `date`, `client`, `client_domain`, `market`, `language`, `page_url`, `mode`, `existing_url`, `primary_keyword`, `secondary_keywords`, `intent`, `funnel`, `format`, `format_embedded`, `format_source`, `metrics`, `geo_candidate`, `geo_answer_format`, `cluster`, `pillar_url`, `ymyl`, `local`, `cannibalization`, `voice_source`, `style_source`, `word_range`, `client_inputs_open`, `source_report`.

Field rules: `status` is `DONE` or `DONE_WITH_CONCERNS` (a `NEEDS_INPUT` or `BLOCKED` row has no file). `format` and `format_embedded` use the enum in input-contract.md; `format_source` is the row's original text. `metrics` is copied from the row. `cannibalization` is `clear`, `clear (unverified)`, `clear (no site)` or `risk`. `voice_source` and `style_source` are `client`, `default/<industry-slug>` or `default/generated`. `client_inputs_open` equals the number of items in Client Inputs Needed. `source_report` is the report path or `none`.

## Body

```
# Content Brief: How long does a tankless water heater last?

## Page Goal
<2-3 sentences: the reader's job, what the page must make them able to decide or do, and why now (the row's why_now). Name the conversion: the next page or action.>

## Refresh Audit
<refresh mode only: current title, H1, H2s, word count, last updated, 3-month clicks/impressions/CTR/position with labels, and per sub-question keep | rewrite | new.>

## Reader and Search Intent
<Who searches this (from audience.md or the SERP), what they already know, what worries them; the intent and funnel; what the SERP rewards (format, depth), labeled Measured.>

## Answer Target
<The 40-60 word answer the page opens with, as the fact it must state (not finished copy), shaped as geo_answer_format, with its evidence id. Example: "State that a tankless water heater lasts more than 20 years (E1) against 10 to 15 for a tank water heater (E1), and that descaling is what decides it.">

## Outline
### H2: How long does a tank water heater last compared with a tankless one?
- First sentence must state: <the specific fact, with evidence ids>
- Cover: <2-4 points>
- Evidence: E1, E3
- Entities: tank water heater, tankless water heater
- Mode: new            (refresh briefs: keep | rewrite | new)
#### H3: <optional sub-question?>
- First sentence must state: <...>
### H2: <next question?>
...
### H2: Frequently Asked Questions        (when faq is embedded)
- Questions: <3-5 questions not answered above, each with the fact its answer must state>
### H2 (CTA): How do I book a <service> in <area>?      (the CTA section, also a question; always last)
- First sentence must state: <the action and route, from brand.md or a slot>

## Entities and Naming
| Entity | Use this name | Never call it |
|---|---|---|
<8-15 rows; the names the outline actually uses>

## Evidence
| # | Figure or quote | Source | URL | Date | Label | Section |
|---|---|---|---|---|---|---|
| E1 | most tankless water heaters last more than 20 years; storage tank heaters 10 to 15 | U.S. Department of Energy, "Tankless or Demand-Type Water Heaters" | https://www.energy.gov/energysaver/tankless-or-demand-type-water-heaters | 2024-05 | Measured | H2 1, Answer Target |
| E2 | 412 tank water heaters replaced in 2025, average age 11.6 years | Harbor & Pine service records | file: brand.md | 2025 | User-provided | H2 1 |

## Author, Experience and Trust
- Author: <name, credentials with license or certification numbers, years, bio URL from brand.md> or [CLIENT INPUT NEEDED #n: ...]
- Reviewer: <for YMYL: the named expert or compliance reviewer> or a slot
- First-hand experience to include: <numbers from real work, a named case, original photos, from brand.md> or a slot
- Trust elements: <licenses, warranties, reviews the client approves; never invented>

## Internal Links
### Links from this page
| URL | Anchor | Why | Status |
|---|---|---|---|
| /water-heaters/ | water heater installation and repair in Portland | pillar for the cluster | live |
### Links to this page
| From URL | Anchor | Status |
|---|---|---|
| /water-heaters/ | how long a tankless water heater lasts | live |

## Voice and Style
- Voice source: <client: voice.md | default/<slug>>. Style source: <client: style.md | default/<slug>>.
<client source: "Follow voice.md (project/voice.md)" / "Follow style.md (project/style.md)", naming the path where the file was found, plus 2-3 lines applying it to this topic. default source: the default's directives embedded in full, because the writer will not have them.>

## Format Requirements
<format and embedded formats; the skeleton rules from formats.md that apply; tables required; word range; local or YMYL requirements; compliance.md restrictions and required disclaimers.>

## Title and Meta Direction
- Title direction: <the H1 wording or close variant with the primary keyword, in the market's language>
- Meta description direction: <the answer plus what else the page covers>

## Client Inputs Needed
1. <what is needed> (why: <where the page uses it>)
2. ...
(or "None.")

## Concerns
- <each concern with the fallback instruction; or "None.">

## Writer QA Checklist
- [ ] Every H2 and H3 is a question the reader would ask (FAQ heading, numbered steps and list items excepted).
- [ ] Every section's first sentence states what this brief says it must state, and names its subject.
- [ ] Every section makes sense read on its own; no paragraph, list item or table row starts with "it", "this" or "they".
- [ ] Each entity uses the name in the naming table, every time.
- [ ] Every figure comes from the Evidence table and names its source in the same sentence; nothing else is quantified.
- [ ] Quotes are verbatim from the Evidence table, with attribution.
- [ ] Every [CLIENT INPUT NEEDED #n] slot is still visible until the client supplies it; no slot is filled from memory.
- [ ] The byline and first-hand experience match Author, Experience and Trust.
- [ ] Every "Links from this page" link is placed with its anchor, in a sentence that says why it is relevant.
- [ ] Format Requirements are met (tables, numbered steps, FAQ, word range, disclaimers).

## Research Log
- Tools available: <list>
- <date> <tool or source>: <what was looked up, what came back>
- Assumptions: <industry, format normalization, anything inferred>
```

## Link rules

- "Links from this page" URLs are root-relative paths on the client's site (`/water-heaters/`), never full URLs or slots.

## Outline rules

- 5 to 8 sub-question sections (`### H2:`), plus the optional FAQ (`### H2: Frequently Asked Questions`, with a `- Questions:` line) and one CTA section (`### H2 (CTA):`).
- Every `### H2:` and `### H2 (CTA):` section has `- First sentence must state:` and `- Evidence:` lines. The first-sentence instruction is always a fact the writer can state; a client-input slot may appear in it only beside that fact, never as the whole instruction. `- Evidence:` lists evidence ids (`E1, E3`) or says `none verifiable`, which must match a concern with its fallback instruction.
- H3s (`#### H3:`) are optional; they are questions too, or numbered steps or list items.

## Slots

A client fact the page needs and no file supplies is written inline as `[CLIENT INPUT NEEDED #3: <what>]` wherever the page needs it, and as item `3.` in Client Inputs Needed. Number from 1 with no gaps. Reuse the number when the same fact is needed again, always in the full bracket form. Slots are for facts only the client knows; never put a slot in a URL cell, and never use one for a statistic a public source could provide (that is a concern with a fallback).
