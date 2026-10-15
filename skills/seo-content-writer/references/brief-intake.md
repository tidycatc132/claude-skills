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
