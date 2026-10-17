# Homepage page type

Load this when the brief's page type or format is `homepage` (or the page URL is `/`). It replaces the article layout in `output-spec.md` for `article.md`; `metadata.md`, `qa_report.md`, `article.html` and `handoff.md` keep their specs, with the changes below. The writing rules still apply: question headings, answer-first sentences, one name per entity, a source for every figure.

A homepage is the page a client looks at hardest, so it is where invented proof does the most harm. The rule that decides most homepage outcomes is the client-fact rule below.

## The client-fact rule

Every credential, license or registration number, certification, membership, award, rating, review count, warranty, guarantee, testimonial, street address, phone number and opening hour on the page must be stated in the brief or in a client file (`client-reference/<client-slug>/`, or the client files the user names). Anything else is a `[NEEDS INPUT: ...]` flag in the place the fact belongs, for example `[NEEDS INPUT: contractor registration number and any manufacturer certifications]`.

- Copy what the files state exactly: the phone digits, the address, a testimonial word for word with the name the file gives. Never shorten or polish a quote, and never write a quote, initial-only name ("R. C.") or review the files do not contain.
- A transcript or call note that states a fact counts as a file. Keep its qualifier: "about 47 Google reviews" in the source stays "about 47", never "47 five-star reviews".
- "Licensed", "insured", "certified", "award-winning", "top-rated", "since <year>" and "<n> years of experience" are credentials. Write them only when a file says so.
- The client's services, area, process and positioning come from the brief. Describe a service in plain terms of what it is, but add nothing about how this client delivers it (scope, options, speed, "with or without" terms) that the brief does not say, and name only the towns the brief lists: no "surrounding area", region name or "and beyond".

## Section map

`article.md` has these eight sections, in this order, each opened by its marker comment on its own line. The marker names the section for the design brief and for `check_draft.py`; the heading under it is written for visitors.

| # | Marker | What it does | Heading |
| --- | --- | --- | --- |
| 1 | `<!-- section: Hero -->` | H1, then 1-2 sentences saying what the client does, for whom and where, then the primary call to action as a link or the phone | the H1 |
| 2 | `<!-- section: Why Us -->` | 3-5 reasons to choose the client, each from the brief's positioning or evidence | question H2, e.g. "Why do Boise homeowners choose Juniper Ridge Roofing?" |
| 3 | `<!-- section: Services Overview -->` | one bullet or table row per service, in the brief's lead order, each linking to its service page from the brief | question H2 |
| 4 | `<!-- section: Proof -->` | testimonials, review rating, case results, credentials: only what the files state, else the flags | question H2 |
| 5 | `<!-- section: About Snapshot -->` | who runs the business and since when, with the link to the about page if the brief gives one | question H2 |
| 6 | `<!-- section: Service Area -->` | the towns the brief lists, core first, as explicit facts | question H2 |
| 7 | `<!-- section: Process -->` | the steps from first contact to finished job, as a numbered list | question H2 |
| 8 | `<!-- section: Final CTA -->` | the exact next action, the contact route, hours and address (or their flags), and what happens after | question H2 |

An FAQ (`## Frequently Asked Questions`, the format rules for FAQs) may go between Process and Final CTA when the brief asks for one; give it the marker `<!-- section: FAQ -->`. `## Sources` goes last, with no marker, when the page states a figure.

## Layout

```
<!-- section: Hero -->
# <H1: what the client is, with the target keyword's terms, e.g. "Roofing Company in Boise for Repairs and Replacements">

<1-2 sentences: what, for whom, where, with one sourced specific if the brief has one.>

[<primary CTA wording>](<conversion URL from the brief>) or call <phone from the files, else the flag>

<!-- section: Why Us -->
## <Question?>

<answer-first sentence naming the client, then 3-5 bullets>

... sections 3 to 8 ...

## Sources

1. <Client> job records, <year>. <What it supports>
```

- No byline, no `Key Takeaways` section and no "Updated" date: a homepage is not an article.
- Keep it scannable: 450 to 900 words unless the brief gives a range. Bullets and short paragraphs over long prose.
- The "statistic per section" rule is relaxed: use the brief's figures where they fit (Why Us, Proof, About), and do not add `[NEEDS SOURCE]` flags just to give Process or Service Area a number.
- Link every internal link the brief lists; services link from Services Overview, the about page from About Snapshot, the conversion page from Hero and Final CTA.

## Other files

- `metadata.md`: same eight rows. `Primary question` is what a searcher wants answered ("Which roofing company in Boise should I call?"). `Key takeaways` are the Why Us reasons. `Article summary` describes the business in 3-4 sentences, in the page's voice.
- `handoff.md`: under `## Open Flags`, every client-fact flag, with "client" as who resolves it. In the build checklist, replace the byline line with "Every client fact (phone, address, hours, credentials, reviews) matches the client's records and Google Business Profile." Add a line for LocalBusiness structured data as a separate job; it must match the visible contact details.
- `article.html`: `make_html.py` turns each marker into a `data-section` attribute and never prints it.

## QA

Run `check_draft.py` with `--page-type homepage` (it also switches on its own when the brief says `Page type: homepage`, `format: homepage` or `URL: /`) and `--client-dir client-reference/<client-slug>/` when that folder exists, plus `--facts <file>` for any other client file you used. Homepage mode skips the byline check, makes the per-section statistic a WARN, and adds:

| Check | FAIL means | Fix |
| --- | --- | --- |
| Homepage sections in order | A marker is missing, repeated or out of order | Add or move the section |
| Client facts trace to the brief or client files | A phone, address, hours, quoted testimonial, rating, review count, founding year, warranty, guarantee or credential word is on the page but in no file. Open slots, flags, a file's prohibited or banned lists, and a brief's Client Inputs Needed, Concerns, Format Requirements, Writer QA Checklist and Research Log sections do not count as stating a fact | Delete it or replace it with a `[NEEDS INPUT: ...]` flag |
| Proof section carries proof or a flag | The Proof section has no quote, figure or flag | Add the files' proof, or flag what is needed |
| Final CTA gives a route | The Final CTA section has no link, phone or flag | Add the conversion link or phone |

`scripts/selftest_homepage.py` checks this rule on small cases; run it after changing `check_draft.py`.
