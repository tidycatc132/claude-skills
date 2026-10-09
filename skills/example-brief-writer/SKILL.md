---
name: example-brief-writer
description: Turn a topical-map CSV (columns topic, keyword, page_type, priority) into one markdown content brief per page, with a target keyword, an outline matched to the page type, and a word-count target. Use when the user has a topical map CSV, or the output of example-topic-map, and asks for content briefs or writer briefs. Do NOT use to build the map from seed topics (use example-topic-map) or to write the finished article.
---

# Example brief writer

Consumes the CSV produced by `example-topic-map` and writes one brief per row. A worked example for the skills harness.

## Input contract
A CSV whose header is exactly `topic`, `keyword`, `page_type`, `priority`, in that order.

- `page_type` must be one of `service`, `location`, `blog`.
- `topic` and `keyword` must be filled on every row.
- `priority` is `1` to `3`; briefs are numbered in priority order.

If the header or values do not match, stop and tell the user what is wrong. Do not guess or repair the CSV; send them back to `example-topic-map`.

## Output
One markdown file per row in `briefs/`, named `<priority>-<slug>.md`, each containing: title, target keyword, page type, priority, word-count target, outline (H2s chosen by `page_type`), and a closing checklist.

## Steps
1. Confirm the CSV exists and the header matches the input contract.
2. Run `python3 scripts/make_briefs.py <topic_map.csv> --out-dir briefs` (add `--stdout` to preview instead of writing files).
3. Read `references/brief-template.md` if the user wants to change an outline or a word-count target; it explains the template per page type.
4. Report how many briefs were written per `page_type` and list the file names. Do not paste every brief into the chat.

## Rules
- One brief per row, no merging or skipping rows.
- Do not invent facts, statistics or quotes in a brief. Briefs describe what to cover, not the content itself.
