---
name: content-brief
description: Use when a saved keyword-research report must become a writer-ready content brief for one or more pages, the step between keyword research and seo-content-writer. Trigger on "create the content brief for target X", "brief the November calendar items", "turn the keyword research into briefs", "spec out the page for the writer", or a writing brief built from keyword research. Produces briefs/TARGET-ID/brief.json and brief.md (primary question, 5-8 sub-questions, 8-15 entities, sourced evidence, author, internal links, CTA), script-validated, with missing facts flagged as NEEDS SOURCE or NEEDS INPUT instead of guessed. Do NOT use for finding keywords (use keyword-research), writing the page from a brief (use seo-content-writer), a SERP teardown of one query (use serp-analysis), topics competitors cover that the site lacks (use content-gap-analysis), or the client voice and style kit (use client-reference-kit).
---

# Content Brief

Second step of the content pipeline: keyword-research, then this skill, then seo-content-writer. One keyword-research target becomes one brief that a writer, human or seo-content-writer, can work from with nothing else. The brief carries decisions and sourced facts; it does not pre-write the page.

## Inputs

- **Keyword report** (required): the saved keyword-research report, usually `research/keyword-research/YYYY-MM-DD-<topic-slug>.md`. Its last block is `targets:`, one row per page, with `id`, `primary_keyword`, `secondary_keywords`, `intent`, `funnel`, `format`, `cluster`, `pillar_url`, `geo_candidate`, `geo_answer_format`, `metrics` and `why_now`.
- **Which targets**: the target `id`s the user names, or the rows behind the calendar items they name ("the November pages"). If they name none, list the ids and ask which.
- **Client facts** (optional, as available): client notes in the project, `client-reference/<client-slug>/` files from client-reference-kit (slug = domain without `www.` and TLD), anything the user pastes. Live research with WebSearch or WebFetch only if available.

If the report has no `targets:` block (an older or unsaved report), say so and ask keyword-research to save the report with it; do not reconstruct targets from prose. If there is no keyword-research report at all, only a topic or keyword, say keyword-research runs first; a brief without measured keyword data and a target row is not this skill's output.

## Output

For each target, a folder `briefs/<id>/` (or under the folder the user names) with:

| File | Made by |
| --- | --- |
| `target.json` | `scripts/parse_targets.py` |
| `brief.json` | you, to the schema in `references/brief-schema.md` |
| `brief.md` | `scripts/build_brief.py`; the file seo-content-writer reads |
| `sources.md` | you, only when you used web research: the text and URL of each page cited |

`brief.md` starts with a `# Content Brief:` title, then the lines `Client:`, `Brief status: READY | NEEDS_INPUT | FIX`, `Approval:`, `Page type:` and `URL:`, then fixed sections: Target keyword (`- Primary:` line), Search intent, Primary question, Sub-questions, Entities to cover, Evidence pack, Expert quote, Author, First-hand experience, Internal links, Formatting directives, CTA, YMYL review (when `ymyl` is true), Notes for the writer (when `notes` has items), Open flags.

## Workflow

1. **Read the target.** `python3 <skill-folder>/scripts/parse_targets.py <report> --id <id> --out briefs/<id>/target.json`
2. **Read the client facts** listed under Inputs. Note every figure, quote, author, page URL and CTA with the file it came from.
3. **Build the judgment fields** with `references/research.md`: primary question, 5-8 sub-questions, 8-15 entities, evidence mapped to sub-questions, internal links, format directives, word range, YMYL.
4. **Write `brief.json`** to `references/brief-schema.md`. Copy target fields exactly (`primary_keyword`, `secondary_keywords`, `intent` as `search_intent`, `funnel`, `metrics`, `geo_answer_format` as `answer_format`). Every figure in `evidence`, `expert_quotes`, `first_hand`, `author` and `cta` must come from a source file. A fact you do not have is a `{"needs": "..."}` gap, never a "typical" figure and never an illustrative example.
5. **Validate and render**:
   `python3 <skill-folder>/scripts/build_brief.py briefs/<id>/brief.json --target briefs/<id>/target.json --sources <report> <each client file you used> [briefs/<id>/sources.md]`
   Fix every FAIL in `brief.json` and rerun until the verdict is `READY` or `NEEDS_INPUT`. Read each WARN and fix it or say why it stays.
6. **Answer in chat** with, per brief: the `VERDICT:`, the path to `brief.md`, the open flags quoted, and a handoff block:

```
status: DONE | NEEDS_INPUT
briefs: <paths to brief.md>
open_flags: <count and the ones a human must resolve first>
next_skill: seo-content-writer (write the page from brief.md once the brief is approved)
```

Run each script as a single plain `python3` command (use `python` where `python3` is not on the path) with paths as arguments. Do not chain commands with `&&`, `|`, `cd` or loops, and read files with the file-reading tool. If a command is denied, retry the plain form once before reporting that it could not run; never hand-write `brief.md`.

## What the brief leaves to the writer

The writer's skill owns heading wording, answer-first passages, keyword placement, meta title and description, key takeaways and the article summary. The brief does not prescribe them, does not set character limits, and does not specify schema markup (that is the structured-data skill's job after publishing). `format_directives` say what the page must contain, not how to word it.

## Reference files

| File | Load when |
| --- | --- |
| `references/brief-schema.md` | Step 4, always |
| `references/research.md` | Step 3, always |
