# Brief intake: read the brief like a checklist

Do this before writing a word of the page. Write the result as a short working list; it goes into `handoff.md` under `## Intake`, one line per item, each marked `from brief`, `built` or `FLAG`.

## The eight intake items

| # | Item | If the brief has it | If the brief lacks it |
| --- | --- | --- | --- |
| 1 | Primary question, phrased as a person or an AI Overview would ask it | Use it as the H1 or the first question answered | Build it from the target keyword and intent. Mark `built` |
| 2 | 5-8 sub-questions | Use them, each becomes its own heading | Build to at least 5 (see "Building sub-questions"). Mark `built` |
| 3 | 8-15 related entities | Use them in natural prose | Build the list from the topic. Mark `built` |
| 4 | Primary name per key entity (product, service, brand, condition, regulation) | Commit to it; note any aliases the brief bans | Pick the most common, specific name and keep it everywhere |
| 5 | Evidence per section (named statistics, expert quotes, credible sources) | Map each item to the section it supports | Research with WebSearch/WebFetch if available and cite; otherwise `[NEEDS SOURCE: ...]` in that section. Never fill from memory |
| 6 | Named author, credentials, bio URL | Byline with name, credentials, link to bio | `[NEEDS INPUT: author name, credentials and bio URL]` in the byline line. Never "Staff Writer", "Admin" or a made-up person |
| 7 | First-hand experience (numbers from real work, named cases, original photos, mistakes seen) | Plan where each goes | `[NEEDS INPUT: one first-hand example from the client]` in the most relevant section |
| 8 | Internal links (pillar, sub-topic, siblings) with planned anchor text | Plan the sentence each link sits in | Link only to URLs the brief or the user gave; ask in `handoff.md` for the rest. Never invent a URL |

Also take from the brief: page type and format directives (table, FAQ, word range), search intent, CTA wording and target, client name and location, and anything marked approved or banned.

## Evidence comes before drafting

Gather the evidence for every section first, then draft around it. Do not draft first and hunt for proof later; that is how unsupported numbers get in. For each number you will use, note its exact wording and source. A number that is in the brief's approved evidence pack is verified; any number from your own research needs the source page named in `## Sources`.

What counts as a source: a named organization, publication, study, dataset, government page, manufacturer document, or the client's own records (cited as such, for example "Harbor & Pine service records, 2025"). A named, quoted expert from the brief counts. "Industry data", "experts" and your own memory do not.

## Building sub-questions

When the brief has fewer than 5 sub-questions, add real ones until it has 5-8. Sources, in order: People Also Ask and related searches if you can search; the brief's secondary keywords; the variants a customer asks on the phone:

- **how much** (cost, price, amount, size)
- **how often / how long** (frequency, duration, lifespan)
- **why** (cause, reason)
- **what if** (edge case, failure, change of plans)
- **vs** (the familiar alternative)

Add a question only when it helps the reader of this page. No headings that exist only to hold a keyword.

## Client reference files

When `client-reference/<client-slug>/` exists, read before drafting:

- `voice.md`: tone, do and don't phrasing. Match it.
- `style.md`: product names, lexicon, banned words, English variant, number and date style. These override the brief's wording only where the brief is silent.
- `compliance.md`: approved claims, required disclaimers, review triggers. A claim not on the approved list is a flag, not a sentence. Required disclaimers go on the page.
- `brand.md`, `audience.md`: offers, CTAs and the reader's vocabulary.

## When there is no brief

If the user gives only a topic or keyword, recommend running the brief step first. If they want the page anyway, fill this intake table yourself, mark every row `built` or `FLAG`, and title the section in `handoff.md` "Working brief (not approved)".

## Briefs from the content-brief step

A content brief from the brief step is one markdown file, usually `research/content-briefs/<id>.md`: YAML front-matter, then fixed sections. Pass the file itself to `check_draft.py --brief`; the script reads `primary_keyword`, `client` and the "Links from this page" table from it.

Status: `status: DONE` or `DONE_WITH_CONCERNS` means write the page (read Concerns first; each carries its fallback instruction). There is never a file for a NEEDS_INPUT or BLOCKED row.

The intake items are already done in this brief. Map them instead of rebuilding:

| Intake item | Where it is in the brief |
| --- | --- |
| 1 Primary question | the `# Content Brief:` title and Answer Target |
| 2 Sub-questions | Outline: every `### H2:` is a sub-question; write them as the page's H2s in that order |
| 3 Entities and 4 primary names | Entities and Naming table ("Use this name", "Never call it") |
| 5 Evidence | Evidence table (`E1`, `E2`...; each Outline section lists its ids). These are the only figures; a section marked `none verifiable` follows its concern's fallback, with no number |
| 6 Author | Author, Experience and Trust (`- Author:`, `- Reviewer:` on YMYL pages) |
| 7 First-hand material | Author, Experience and Trust (`- First-hand experience to include:`) |
| 8 Internal links and anchors | Internal Links, "Links from this page" (place these); "Links to this page" is for the site editor, not this draft |

Writing from it:
- Each Outline section's `- First sentence must state:` is the fact the section's first sentence states; write it as a complete answer in the writer's own words, with its source named.
- `[CLIENT INPUT NEEDED #n: ...]` slots are copied onto the page in exactly that form wherever the brief places them. They count as open flags, so the verdict is NEEDS_INPUT until the client answers. Never fill one from memory and never renumber it.
- Voice and Style: when the source is `client`, read the named `voice.md` / `style.md`; when it is a default, the directives are embedded in the brief and are the voice to follow.
- Format Requirements, Title and Meta Direction and the Writer QA Checklist apply on top of this skill's own rules; where they conflict, the brief's compliance and claim restrictions win.

Front-matter keys (all present in every brief): `id`, `brief_version`, `status`, `date`, `client`, `client_domain`, `market`, `language`, `page_url`, `mode`, `existing_url`, `primary_keyword`, `secondary_keywords`, `intent`, `funnel`, `format`, `format_embedded`, `format_source`, `metrics`, `geo_candidate`, `geo_answer_format`, `cluster`, `pillar_url`, `ymyl`, `local`, `cannibalization`, `voice_source`, `style_source`, `word_range`, `client_inputs_open`, `source_report`. The ones that change the writing: `primary_keyword` and `secondary_keywords` (keyword use), `intent` and `funnel` (depth and CTA), `format`, `format_embedded` and `format_source` (which format rules apply), `geo_candidate` and `geo_answer_format` (the opening answer's shape), `ymyl` (credentials first, compliance review in handoff.md), `local` (name the service area), `page_url`, `pillar_url` and `cluster` (links), `word_range`, `voice_source` and `style_source`, `client_inputs_open` (open slots at the start), `cannibalization` (a `risk` value comes with a concern saying how this page must differ). `id`, `brief_version`, `status`, `date`, `client`, `client_domain`, `market`, `language`, `mode`, `existing_url`, `metrics` and `source_report` are bookkeeping; `metrics` is keyword data, never a figure for the page.
