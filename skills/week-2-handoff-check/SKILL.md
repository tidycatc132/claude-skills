---
name: week-2-handoff-check
description: Go/no-go gate on a website build's Week 2 deliverables. Use when the AM or PM asks for the Week 2 handoff or end-of-week checklist, whether Week 2 is done or anything from it is missing, or if Week 3 can begin. A script confirms Week 1 cleared, finds the competitor report, Growth Blueprint and briefing, the deck with a zero-hit compliance file, the page-type design briefs and the send-out, and compares the sitemap's pages with the briefs and written pages, naming any page not written. It writes handoff/[slug]/[slug]-week-2-handoff.md ending in GO or NO-GO and never waits on the client's answer. Do NOT use for producing what it checks, such as Week 1's check (use week-1-handoff-check), the Blueprint (use growth-blueprint), the deck (use blueprint-deck), missing briefs (use content-brief) or pages (use seo-content-writer), design briefs (use page-type-design-briefs), client emails (use week-2-client-email or week-1-client-email), the client's reply (use client-feedback) or ClickUp (use clickup-progress-sync).
---

# Week 2 handoff check

At the end of Week 2 the team needs one answer: can Week 3 start? This skill gets it from the files, not from memory. A script looks for every Week 2 deliverable in the client's working folder, compares the sitemap's pages with the briefs and the written pages, and writes a short report that ends in `GO` or `NO-GO`. The client's reply to the Week 2 email is listed but never holds Week 3 up.

## Input

The client's working folder (the folder that holds `kickoff/`, `blueprint/`, `content/` and the rest). `<slug>` is the folder name under `kickoff/`; the script finds it when there is only one client, else pass `--slug`. If there is no `kickoff/<slug>/<slug>-context.md`, this is not a client working folder: say so and stop.

What the script reads, in report order (the full rules are in `references/checklist.md`):

| Item | Path |
|---|---|
| Week 1 handoff | `handoff/<slug>/<slug>-week-1-handoff.md`, last line `GO` |
| Competitor report | the last-named `seo-reports/competitor-analysis/*.md` |
| Growth Blueprint | `blueprint/<slug>/<slug>-growth-blueprint.md` |
| AM Briefing | `blueprint/<slug>/<slug>-am-briefing.md` |
| Blueprint deck | `blueprint/<slug>/<slug>-growth-blueprint-deck.pptx` |
| Deck compliance | `blueprint/<slug>/<slug>-deck-compliance.md` |
| Sitemap report | the last-named `seo-reports/site-structure-optimizer/*.md` with a `countable pages N / SOW cap M` line and a `| Page | URL |` URL map |
| One row per sitemap page | its brief in `research/content-briefs/` (matched by `page_url`) and its page in `content/<url-slug>/`: `article.md`, `metadata.md`, `article.html`, `qa_report.md`, `handoff.md` |
| Page-type design briefs | `design/<slug>/<slug>-page-type-design-briefs.md` |
| Week 2 client email | `emails/<slug>/<slug>-week-2-email.md` |
| Client feedback (not required) | the last `feedback/<slug>/*-feedback.md` with a `Week: 2` line, or a `*-week-2-nudge.md` |

## Output

`handoff/<slug>/<slug>-week-2-handoff.md`:

```
Client: <client>
Checked: <YYYY-MM-DD>

# Week 2 handoff check for <client>

| Item | Required | Status | Path | Note |
|---|---|---|---|---|
| ... one row per item, one row per sitemap page as `Page: <page name>` ... |

## Blocking
- <item> (<status>): <note>          (or "- None. Every required item is present.")

## Not blocking
- <item> (<status>): <note>          (or "- None.")

GO                                    (or NO-GO)
```

Status is `present`, `missing`, `stale` or `n/a`. A required row that is `missing` or `stale` makes the result `NO-GO`. The note of a failing row names who fixes it and with which skill.

## Steps

1. **Run the check** from the client's working folder, as one plain command with the paths as arguments (no `cd`, no `&&`, no pipes):
   `python3 <skill-folder>/scripts/week2_handoff.py run . --date <today YYYY-MM-DD>`
   `<skill-folder>` is the folder this SKILL.md is in; write its real path. Add `--slug <slug>` when there are several clients. If the command is denied, run the same plain command once more; never work the checks out by hand or write the report yourself. The script exits 0 on `GO`, 1 on `NO-GO` (both are normal results) and 2 on a usage error.
2. **Answer** in chat with the result line (`GO` or `NO-GO`), the path of the report, every blocking row with its note (each names the owner), and the non-blocking rows in one line. When a page row is missing, name the page. Read `references/checklist.md` first if the person asks why a row failed or what would make it pass.

## Rules

- **Report, never fix.** The check reads and writes only its own report. Do not write a missing page, rebuild the deck, edit a brief or touch any other file to turn a row green; name the owner and the skill instead, and let the person decide.
- **The script's verdict stands.** Copy statuses and notes from the report; do not soften a `NO-GO` or upgrade a row because the file "looks fine".
- **The client's reply never blocks.** Client feedback is `Required: no`. A reply with strategy items held for SEO is reported, not waited for; no reply after the reply-by date points to the nudge (client-feedback).
- **Status, not content.** The answer carries what the report says; do not add facts read from the Blueprint, the deck or the pages.

## References

- `references/checklist.md`: what each row checks, when it is `missing` or `stale`, and the owner named in its note. Load it when explaining a failing row or when the person asks what the check covers.
