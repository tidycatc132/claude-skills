---
name: example-topic-map
description: Turn a plain-text list of seed topics into a topical-map CSV, i.e. a spreadsheet of pages to build with a page type and priority on each row. Use when the user provides seed topics or keywords and wants a page plan, site plan, or topical map as a CSV or spreadsheet. Do NOT use for writing content briefs from an existing map (use example-brief-writer) or for writing articles.
---

# Example topic map

Turns seed topics into the CSV that `example-brief-writer` consumes. This skill is a worked example for the skills harness: small on purpose, with a script doing the deterministic part.

## Input
A text file with one seed topic per line. Blank lines and lines starting with `#` are ignored.

## Output
A CSV with exactly these columns, in this order:

| Column | Meaning |
|---|---|
| `topic` | The seed topic, cleaned and title-cased |
| `keyword` | The lowercase search phrase for the page |
| `page_type` | One of `service`, `location`, `blog` |
| `priority` | `1` (build first) to `3` (later) |

## Steps
1. Confirm the seed file exists and has at least one topic. If it is empty, ask the user for seeds instead of inventing them.
2. Run the script, which classifies each topic deterministically:
   `python3 scripts/make_map.py <seeds.txt> > topic_map.csv`
3. Read `references/page-types.md` only if a topic is ambiguous or the user disagrees with a `page_type`; it explains how the script decides and how to override.
4. Show the user the first rows and the count per `page_type`. Fix individual rows by hand only if the user asks, keeping the columns and allowed values exactly as above.

## Rules
- Never rename, reorder or add columns; the downstream skill and its contract depend on them.
- Never add topics the user did not give you.
