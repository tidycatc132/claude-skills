# brief.json schema

`brief.json` is the brief. `scripts/build_brief.py` validates it and renders `brief.md`, the file seo-content-writer reads. Fill every key; use a `needs` object for a gap instead of guessing.

A **gap** is `{"needs": "<what is missing and who can supply it>"}`. It renders as a `[NEEDS SOURCE: ...]` flag inside `evidence` and as `[NEEDS INPUT: ...]` everywhere else. The writer carries these flags onto the page; never replace one with a value from memory.

## Keys

| Key | Type | Filled from | Rule |
| --- | --- | --- | --- |
| `id` | string | target `id` | unchanged |
| `client` | string or gap | client notes, kit, report title | "Name (domain), City, Region" |
| `page_url` | string or gap | report calendar row, client notes | path starting with `/` |
| `page_type` | enum | target `format` | blog article, explainer, guide, how-to, comparison, listicle, definition, FAQ page, service page, product page, location page, cost guide |
| `primary_keyword` | string | target `primary_keyword` | copied exactly |
| `secondary_keywords` | list | target `secondary_keywords` | copied; add none |
| `search_intent` | enum | target `intent` | copied |
| `funnel` | enum | target `funnel` | copied |
| `why_now` | string | target `why_now` | optional, copied |
| `metrics` | object | target `metrics` | copied exactly (volume, kd, source); these are keyword data for the team, not facts for the page |
| `primary_question` | string | built | the primary keyword as the question a person types or asks an assistant, ending in `?` |
| `sub_questions` | list of 5-8 | built (research.md) | each ends in `?`, none repeats the primary question |
| `entities` | list of 8-15 | built (research.md) | the primary name of each person, product, organization, place, regulation or concept the page must name |
| `banned_aliases` | list | client style rules, judgment | names the writer must not switch to; may be empty |
| `evidence` | list | sources only | items `{"source", "url" (optional), "claim", "supports"}` or `{"needs", "supports"}` |
| `expert_quotes` | list | client notes or interviews only | items `{"quote", "speaker", "context"}`; empty list when none are on file |
| `author` | object or gap | client notes or kit | `{"name", "credentials", "bio_url"}` |
| `reviewer` | string | client notes | optional; the named compliance or expert reviewer |
| `first_hand` | list | client notes | real cases or numbers from the client's own work, or a gap |
| `internal_links` | list | target `pillar_url`, client page list, report | items `{"role", "url", "anchor"}`; role is pillar, sub-topic, sibling, service or booking |
| `answer_format` | enum | target `geo_answer_format` | copied: direct answer, steps, comparison table, definition plus example, FAQ block, N/A |
| `format_directives` | list of strings | target `format`, judgment | what the page must contain (table, FAQ, scope limits), never invented example numbers, schema markup or character counts |
| `word_range` | string | judgment from format and competition | like `1400-1800` |
| `cta` | object or gap | client notes | `{"text", "route"}` |
| `ymyl` | boolean | topic | true for health, finance, legal or safety topics |
| `source_report` | string | input path | the keyword-research report path |
| `notes` | list | judgment | optional; scope warnings for the writer (cannibalization, planned sibling pages) |

## Evidence items

- `claim` copies the source's figure and qualifier exactly ("more than 20 years", "around 3 to 8 ppm"). Never round, combine or strengthen.
- `source` names the publisher and page, or the client record ("Harbor & Pine service records, 2025").
- `supports` names the sub-question(s) or section the item serves. Aim for one item (sourced or gap) per sub-question.
- A figure is allowed only if it appears in a file passed to `--sources`. The script fails the brief otherwise.
- A gap says what figure is needed and from what kind of source: `{"needs": "manufacturer documentation of failure signs for Rinnai or Navien units", "supports": "signs of failure"}`.

## Target fields used

From the keyword-research `targets:` row: `id`, `primary_keyword`, `secondary_keywords`, `intent`, `funnel`, `format`, `cluster`, `pillar_url`, `geo_candidate`, `geo_answer_format`, `metrics`, `why_now`. `cluster` and `geo_candidate` shape judgment (sibling links within the cluster; answer-first opening when `geo_candidate` is true) but are not copied.
