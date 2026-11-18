# Input contract: the keyword-research `targets:` block

The input is the `targets:` block at the end of a saved keyword-research report, one row per page. Read it with:

```
python3 scripts/parse_targets.py <report.md> --normalize [--id <id>] [--out <file>]
```

`--normalize` adds `format_primary`, `format_embedded`, `format_normalized`, `mode` and `problems` to each row. Without it the output is exactly what keyword-research wrote.

## Fields

| Field | Required | Rule |
|---|---|---|
| `id` | yes | Lowercase, hyphenated primary keyword. Never changes; it names the brief file. |
| `primary_keyword` | yes | Missing or empty: the row is `NEEDS_INPUT`. |
| `secondary_keywords` | yes | List, may be empty. Never add to it; new phrasing you find goes in sub-questions or entities. |
| `intent` | yes | Informational, Navigational, Commercial or Transactional. |
| `funnel` | yes | TOFU, MOFU or BOFU. |
| `format` | yes | Free text from keyword-research; normalized below. |
| `cluster` | yes | Cluster name or `none`. Siblings are the other rows and Topic Clusters members with the same cluster. |
| `pillar_url` | yes | Pillar path or `N/A`. When it equals this page's URL, the row is the pillar. |
| `geo_candidate` | yes | `true` means the page must open with an answer an AI system can quote. |
| `geo_answer_format` | yes | direct answer, steps, comparison table, definition plus example, FAQ block, or `N/A`. |
| `metrics` | yes | `{volume, kd, source}`; copy into the brief exactly, label included. |
| `why_now` | yes | Copy into Page Goal. |
| `existing_url` | no | Present and not `N/A`: `mode: refresh`. Absent or `N/A`: the script looks for the row's keyword in the report's Content Calendar (a page cell reading `/path/ refresh`) and Topic Clusters (`exists (/path/)`, or a `Pillar:` line marked `refresh`) and, when found, sets `existing_url` and `existing_url_source`; otherwise `mode: new`. |

## Format enum

Primary formats (one per page): `explainer`, `how-to`, `comparison`, `listicle`, `definition`, `cost-guide`, `buyers-guide`, `troubleshooting`, `checklist`, `service-page`, `location-page`, `product-page`, `faq-page`, `pillar-guide`, `homepage`, `about-page`, `contact-page`.

Embedded formats (zero or more, inside the primary): `faq`, `comparison-table`, `steps`, `checklist`, `cost-table`.

## Normalization (done by the script)

1. Lowercase, trim, and split combos on `+`, `,`, `/` or ` and `. The first part is the primary format; the rest are embedded.
2. Map aliases: blog post, article, blog article, guide, explainer -> `explainer`; ultimate guide, complete guide, pillar -> `pillar-guide`; vs, versus, comparison -> `comparison` (primary) or `comparison-table` (embedded); how-to, tutorial, step-by-step -> `how-to` or `steps`; best, top, list, roundup -> `listicle`; what is, definition, glossary -> `definition`; cost guide, pricing guide, price -> `cost-guide` or `cost-table`; buyer's guide -> `buyers-guide`; troubleshooting, problem, signs -> `troubleshooting`; checklist -> `checklist`; service page, service, landing page -> `service-page`; location page, city page -> `location-page`; product page -> `product-page`; faq, faq page, q&a -> `faq-page` or `faq`; homepage, home page, front page, home -> `homepage`; about, about us, about page -> `about-page`; contact, contact us, contact page -> `contact-page`.
3. A combo (more than one part) sets `format_normalized: true`: record the original value in the brief's front-matter `format_source` and list the normalization under Concerns. A plain alias ("blog post" -> `explainer`) is not a concern; still record `format_source`.
4. An unknown value (anything not mapped, for example "interactive calculator" or "webinar landing") is `NEEDS_INPUT`: write no brief and ask which format to use.

## Rows that cannot be briefed

A row is `NEEDS_INPUT` (no brief file) when: `primary_keyword` is missing; `format` is unknown; cannibalization comes back `conflict` (see research.md section 1); or `existing_url` is set but cannot be fetched. The script lists the first two in `problems`; the other two come from research.

## Report context to read alongside the rows

- The report's opening lines: market, language, location, client domain. They set the SERP location and the brief's `market` field.
- Content Calendar: month, page URL and primary keyword per row. The calendar URL is the page's URL when the row has none; month 1 items are the unattended default.
- Topic Clusters: pillar and members, with `exists (<url>)` or `new`. Members that exist are live sibling pages; `new` members are planned.
- The handoff block's `open_loops`: carry anything relevant into Concerns.
