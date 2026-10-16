# Building the brief's judgment fields

The keyword report gives the target. Everything else in the brief is either copied from a source file or built by the method below.

## Primary question

Turn the primary keyword into the question a person types or asks an assistant: "how long does a tankless water heater last" becomes "How long does a tankless water heater last?"; "heloc vs home equity loan" becomes "What is the difference between a HELOC and a home equity loan?".

## Sub-questions (5-8)

Sources, in order of preference:
1. People Also Ask and related searches for the primary keyword, if WebSearch is available.
2. The target's `secondary_keywords`, each rewritten as a question.
3. Questions in the client notes or sales and support material ("questions customers ask on the phone").
4. The variants a reader asks next: **how much** (cost, amount), **how often / how long** (frequency, duration), **why** (cause), **what if** (failure, change of plans), **vs** (the familiar alternative), **what are the signs**.

Keep a question only if this page should answer it. If another target in the same report owns it as its primary keyword, leave it out and add a `notes` line telling the writer to link there instead (this stops two pages competing).

## Entities (8-15)

List the primary name of every thing the page must name for a reader and an AI system to place it: the product or service, its parts or mechanisms, the familiar alternative, organizations and regulators, places in the service area, brands the client works with, and formal terms with their abbreviation ("loan-to-value ratio (LTV)"). Use the client's own names where `style.md` or the notes give them. Put tempting wrong names in `banned_aliases`.

## Evidence

Gather evidence before the brief is final, so the writer never drafts first and hunts for proof later.

- **From files:** client notes, client-reference kit (`client-reference/<client-slug>/brand.md`, `compliance.md`), saved research. Copy figures exactly with their source.
- **From the web (only if WebSearch or WebFetch is available):** government, regulator, manufacturer and standards pages first; then established trade or academic sources. Save each page's key text to `briefs/<id>/sources.md` with its URL so `build_brief.py --sources` can trace the figures.
- **Otherwise:** a `needs` gap for each sub-question without evidence. Never fill a gap with a "typical" or "industry average" figure from memory, and never prescribe an illustrative example with made-up numbers.

## Author, first-hand material, CTA

Copy them from client notes or the kit. If more than one author is approved, pick the one whose credentials match the topic and name the other as `reviewer` when the topic is YMYL. Missing ones are gaps.

## Internal links

- The target's `pillar_url` is always a `pillar` link (unless this page is the pillar).
- Add live pages from the client's page list: the service the page sells, sibling pages in the same `cluster`, and the booking or contact route.
- Planned pages from the report's calendar that are not live yet go in `notes` ("link to /blog/tankless-vs-tank-water-heater/ once it is published"), not in `internal_links`.
- Anchors name the destination topic; never "click here" or "learn more".

## YMYL

Set `ymyl` to true for health, finance, legal or safety topics. Then: name the `reviewer` if the client files give one (else the script adds a reviewer gap), make every lending, medical or legal figure a sourced item or a gap, and add a `notes` line listing disclosures the client's compliance team must supply.

## Word range

Base it on the format: definitions and explainers 1,200-1,800 words, comparisons and guides 1,500-2,500, service pages 700-1,200. Use competitor page lengths instead when the report or your SERP research gives them.
