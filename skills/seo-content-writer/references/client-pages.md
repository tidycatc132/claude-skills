# About, Contact and Location pages

Load this when the brief's page type or format is `about`, `contact` or `location` (`about-page`, `contact-page` and `location-page` count), or its page URL is `/about/`, `/about-us/`, `/contact/` or `/contact-us/`. Like the homepage, these pages replace the article layout in `output-spec.md` for `article.md` with a fixed section map; `metadata.md`, `qa_report.md`, `article.html` and `handoff.md` keep their specs, with the changes under "Other files". The writing rules still apply: question headings, answer-first sentences, one name per entity, a source for every figure.

## The client-fact rule applies in full

These pages are mostly client facts, so the client-fact rule in `homepage.md` decides most outcomes here too (read that one section; the rest of `homepage.md` is the homepage's own layout): every credential, license or registration number, certification, membership, award, rating, review count, testimonial, person's name and role, street address, phone number, email address and opening hour comes from the brief or a client file, copied exactly, or it is a `[NEEDS INPUT: ...]` flag in the place it belongs (a brief's `[CLIENT INPUT NEEDED #n: ...]` slots are copied as they are). Read that section before drafting. On top of it:

- A person is named only when a file names them, with the role the file gives. No invented crew, team size, "our experienced technicians" or years of combined experience. If the files name only the owner, the Team section says who the owner is and flags the rest.
- An owner is not a founder unless a file says so; "owns" and "founded in 2012" stay two facts.
- Values and mission come from the files, in their words and order. Write no value, promise or guarantee of your own.
- An address, phone, email or hours line is copied character for character. A client with no public office says so only when a file does.
- Directions, parking, landmarks, highway exits, neighborhoods, local regulations and local conditions are facts too: state them only when the brief or a file does.
- A testimonial or review belongs to the place the file gives. On a location page, a quote from a customer in another town is either left out or attributed to that town, never presented as local.

## Section maps

`article.md` carries these sections, in this order, each opened by its marker comment on its own line, as on the homepage. The marker names the section for `check_draft.py`, for `make_html.py` (a `data-section` attribute) and for whoever designs the page template; the heading under it is written for visitors as a question, except the Hero's H1. A section may hold more than one question H2 when the brief's outline puts several there. An FAQ (`<!-- section: FAQ -->`) may go just before Final CTA when the brief asks for one; `## Sources` goes last, with no marker, when the page states a figure.

### About page

| # | Marker | What it does |
| --- | --- | --- |
| 1 | `<!-- section: Hero -->` | H1 naming the client, then 1-2 sentences on who they are, what they do and where |
| 2 | `<!-- section: Company Story -->` | how and when the business started and what it does now, from the files |
| 3 | `<!-- section: Mission and Values -->` | the mission and values the files state, as bullets |
| 4 | `<!-- section: Team -->` | the people the files name, with their roles; everyone else is a flag |
| 5 | `<!-- section: Credentials -->` | certifications, licenses, insurance, memberships, awards: only what the files state, else the flags |
| 6 | `<!-- section: Final CTA -->` | the next action and contact route |

### Contact page

| # | Marker | What it does |
| --- | --- | --- |
| 1 | `<!-- section: Hero -->` | H1 ("Contact <client>"), then one sentence on the fastest way to reach them |
| 2 | `<!-- section: Contact Form -->` | what the form is for, then each form field as a bullet, from the brief (else a flag for the field list) |
| 3 | `<!-- section: Phone and Email -->` | the phone and email from the files, else flags |
| 4 | `<!-- section: Address and Hours -->` | the street address and opening hours from the files, else flags |
| 5 | `<!-- section: Map -->` | one sentence naming the address the map shows; the map itself is a build item in `handoff.md` |
| 6 | `<!-- section: Final CTA -->` | what happens after the visitor gets in touch, from the brief |

### Location page

| # | Marker | What it does |
| --- | --- | --- |
| 1 | `<!-- section: Hero -->` | H1 with the service and the place ("Tree Service in Spokane Valley"), 1-2 sentences, primary call to action |
| 2 | `<!-- section: How We Serve -->` | how the client serves this place (office there, or crews that travel there), from the files |
| 3 | `<!-- section: Local Services -->` | the services offered there, one bullet each, linking to its service page from the brief |
| 4 | `<!-- section: Local Proof -->` | jobs, results, reviews or testimonials from this place, only as the files state them, else flags |
| 5 | `<!-- section: Directions -->` | the address and any directions the files give; with no office there, the towns served and how to book |
| 6 | `<!-- section: Final CTA -->` | the next action, the contact route and what happens after |

A content brief's location outline may carry extra local H2s (permits, local conditions); place each in the section it fits (usually How We Serve or Local Services), keep its evidence, and never write the same page as another location with the town swapped.

## Layout notes

- No byline, no `Key Takeaways` section and no "Updated" date.
- Lengths unless the brief gives a range: About 400 to 800 words, Contact 150 to 400, Location 500 to 900.
- The per-section statistic rule is relaxed as on the homepage: use the brief's figures where they fit (Company Story, Credentials, Local Proof) and add no `[NEEDS SOURCE]` flags just to give a section a number.
- Link every internal link the brief lists; the conversion link goes in the Hero or Final CTA.

## Other files

- `metadata.md`: same eight rows. `Primary question` is the visitor's question ("Who is Copperleaf Tree Care?", "How do I contact Copperleaf Tree Care?", "Who offers tree service in Spokane Valley?"). `Key takeaways` are 3-5 facts from the page.
- `handoff.md`: every client-fact flag under `## Open Flags`, with "client" as who resolves it. In the build checklist, replace the byline line with "Every client fact (names, phone, email, address, hours, credentials, reviews) matches the client's records and Google Business Profile." Contact page: add "Build the form with the fields listed; send submissions to the address the client confirms" and "Embed the map for the address shown". Contact and Location pages: add a LocalBusiness structured data line as a separate job, matching the visible contact details.
- `article.html`: `make_html.py` turns each marker into a `data-section` attribute and never prints it.

## QA

Run `check_draft.py` with `--page-type about`, `contact` or `location` (it switches on its own from the brief's page type, format or URL) and `--client-dir client-reference/<client-slug>/` when that folder exists, plus `--facts <file>` for each other client file you used. As on the homepage, the byline check is skipped, the per-section statistic and the keyword repetition count are WARNs (an About or Contact keyword is often the client's name, which the one-name rule repeats), and the client-fact check runs (emails included). It adds:

| Check | FAIL means | Fix |
| --- | --- | --- |
| `<Page> sections in order` | A marker is missing, repeated or out of order | Add or move the section |
| `Credentials section carries proof or a flag` (About), `Local Proof section carries proof or a flag` (Location) | The section has no quote, figure or flag | Add the files' proof, or flag what is needed |
| `Contact form lists its fields` (Contact) | Fewer than 3 bulleted fields in Contact Form | List each field as a bullet |
| `Contact details given or flagged` (Contact) | No phone, email, address or hours, and no flag for it | Copy it from the files or flag it |
| `Final CTA gives a route` | No link, phone or flag in Final CTA | Add the conversion link or phone |

`scripts/selftest_client_pages.py` checks these rules and the batch script on small cases; run it after changing either script.
