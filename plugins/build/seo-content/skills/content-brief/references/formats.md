# Formats: H2 skeletons and writing rules

Read "Common to every format", then the section for the row's `format_primary` and one for each `format_embedded`. The skeleton decides the H2 list; evidence is gathered per H2.

## Common to every format

- Every H2 and H3 is a question the reader would ask, in the market's language. Exceptions: the FAQ heading, numbered steps (`Step 3: Shut off the gas`) and numbered list items (`1. Rinnai RE199iN: best for two showers at once`).
- Every section's first sentence is the complete answer to its heading and names its subject. The brief states that answer for each section as **First sentence must state**: specific enough that two writers would open with the same fact.
- The page's key answer is in the first paragraph under the H1. When `geo_candidate` is true it is shaped as `geo_answer_format` and 40 to 60 words.
- Paragraphs of 2 to 4 sentences. A table wherever 3 or more comparable items or figures appear.
- Every figure carries its source in the same sentence. No "studies show", "experts say".
- One name per entity, as in the naming table; restate it at the start of paragraphs, list items and table rows instead of "it" or "this".
- Descriptive anchor text naming the destination; never "click here" or "learn more".
- A visible byline with a real name and verifiable credentials, and at least one first-hand experience marker from the client. A homepage, About, Contact or location page has no byline (see their sections below).
- Never prescribe an illustrative example with invented numbers, "typical industry" figures, schema markup or character counts in the brief.

## Primary formats

### explainer
Skeleton: answer paragraph; the core question restated (how long, how much, what causes); 4 to 6 follow-up question H2s (why, how often, what if, signs, vs); FAQ when embedded; CTA question H2. Word range 1,200 to 1,800.

### pillar-guide
Skeleton: answer paragraph; one H2 per cluster subtopic, each a short self-contained answer that links down to the cluster page; a comparison or decision table across subtopics; FAQ; CTA. Word range 2,500 to 4,000. Sub-questions map to cluster members.

### definition
Skeleton: H1 "What is X?"; first sentence is a one-sentence definition with the mechanism, not just a category, plus the contrast with the familiar alternative; H2s for how it works, how it differs from the alternative, how much or how long, what happens when, who it suits. Word range 1,000 to 1,600.

### how-to
Skeleton: answer paragraph with time, tools and cost; "What do you need?" H2 with a list; numbered steps as H3s starting with an imperative verb (Shut off, Attach, Flush); a **Safety:** line on every safety-critical step; "What if it does not work?" H2; "When should you call a professional?" H2. Word range 1,000 to 2,000.

### comparison
Skeleton: first sentence states the single most important difference, with figures, naming both options; a comparison table (header row names both options; one row per attribute; sourced cells); one H2 per decision factor; "Which should you choose?" H2 that says who each option suits, with the deciding numbers. Every comparative sentence names both options. Word range 1,500 to 2,500.

### listicle
Skeleton: answer paragraph naming the top pick and why; a summary table (item, best for, key spec, price); each item a numbered H3 naming the item and its specific differentiator or ideal use; each with at least one sourced spec or number; "How did we choose?" H2 with the criteria. Two items serving the same use are said to overlap, not given invented differences. Word range 1,500 to 3,000.

### cost-guide
Skeleton: first sentence gives the price range or starting price with its source; a cost table (item or scenario, range, source); H2s for what drives the cost, how to save, hidden costs, and when to pay more; the client's own pricing where `brand.md` approves it. Word range 1,200 to 2,000.

### buyers-guide
Skeleton: answer paragraph with the deciding criteria; one H2 per criterion with the threshold that matters (capacity, efficiency rating, warranty years); a decision table; "What mistakes do buyers make?" H2. Word range 1,500 to 2,500.

### troubleshooting
Skeleton: first sentence names the most likely cause; one H2 per symptom or cause ("Why does my water heater make a popping noise?"), each with what it means, what to check, and when to call a professional; **Safety:** lines where a step involves gas, electricity or water damage. Word range 1,000 to 1,800.

### checklist
Skeleton: answer paragraph with how often and how long; the checklist as a numbered list grouped under question H2s (before, during, after; or by season); each item a complete action with its interval. Word range 800 to 1,500.

### service-page
Skeleton: first sentence states the service, the area and a starting price or "starting at" figure where the business model allows; H2s for what is included, how much it costs, how long it takes, service area, why choose this provider (proof from `brand.md`), FAQ, booking. Availability, area and eligibility as explicit facts. Word range 700 to 1,200.

### location-page
Skeleton: as service-page, plus H2s on the local specifics (neighborhoods served, local regulations or permits, local conditions such as water hardness or climate) with local sources. Not a copy of another location page with the city name swapped. Word range 700 to 1,200.

The writer builds a location page from a fixed section map, so each `### H2:` block carries a `- Section:` line, in this order: How We Serve (how the client serves this place: an office there or crews that travel there, plus the local specifics), Local Services (the services offered there, each with its service page in Links from this page), Local Proof (jobs, reviews or testimonials from this place, only as a client file states them, else a slot), Directions (the address and directions a file gives; with no office there, the towns served and how to book). An embedded FAQ goes after Directions with `- Section: FAQ`; the `### H2 (CTA):` block carries `- Section: Final CTA`. Several H2s may share a section (permits and local conditions both sit under How We Serve; what is included, cost and how long it takes sit under Local Services), as long as the sections stay in order. `- Author: none (a location page has no byline)`. Run the gate with `--client-dir` or `--facts`: it traces the phone, email, address, hours, quotes and proof claims in Local Proof, Directions and Final CTA to the client files. `- Evidence: none needed` is allowed for Local Services, Directions and Final CTA. A testimonial from another town is never presented as local.

### product-page
Skeleton: first sentence states what the product is, who it is for and the price; specs table; H2s for how it works, how it compares with the alternative, warranty, availability. Word range 500 to 1,000.

### faq-page
Skeleton: answer paragraph; 8 to 15 question H2s grouped by theme, each with a 2 to 4 sentence complete answer containing a specific; links to the deeper page for each theme. Word range 1,200 to 2,000.

### homepage
The client's home page (`page_url: /`). The writer builds it from eight fixed sections, so the Outline maps onto them and each `### H2:` block carries a `- Section:` line naming its section. The Answer Target is the Hero: what the client does, for whom and where, then the primary call to action; Title direction gives the H1. Then, in this order:

| `- Section:` | `### H2:` (a question) | First sentence must state |
|---|---|---|
| Why Us | why people in the area choose the client | the main reason, from the client's positioning; 3-5 reasons under Cover |
| Services Overview | what the client offers | the services in the client's lead order, each with its service page in Links from this page |
| Proof | why the client can be trusted | only proof a client file states (reviews with their exact count and qualifier, quoted testimonials word for word with the name given, credentials, results); everything else is a slot |
| About Snapshot | who runs the business | the owner or team and since when, from the client files |
| Service Area | where the client works | the towns the client files list, core first; no "surrounding areas" |
| Process | what happens after the first contact | the client's steps from first contact to finished job |

An embedded FAQ goes after Process with `- Section: FAQ`. The `### H2 (CTA):` block carries `- Section: Final CTA` and names the next action and the phone, address and hours, each from a client file or a slot (a client with no public address says so).

Rules that differ from other formats:
- Client facts (phone, street address, hours, credentials, licenses, memberships, awards, ratings, review counts, testimonials, warranties, founding year) come only from client files: `brand.md`, the client folder, or files the user names. Copy them exactly, qualifiers included ("about 47 reviews" stays "about 47"). Anything a file lists as not yet available, pending or not to publish is a slot, never a fact. Where the business is located is a client fact too: say it serves the towns the files list ("serving Bend, Redmond and Sisters") unless a file says where it is based. Run the gate with `--client-dir` or `--facts` so it checks this.
- No statistic per section: `- Evidence:` may say `none needed` for Services Overview, Service Area, Process and Final CTA. Why Us, Proof and About use the client's own evidence (`file:` rows) where it exists.
- Author, Experience and Trust: `- Author: none (a homepage has no byline)`; the trust elements are the Proof facts.
- Every planned or live service page is in Links from this page; Links to this page is the site navigation (every page links home), so one row `| site navigation | <client name> home | planned |` is enough.
- Cannibalization: on a live site the current homepage is this page, not a conflict (refresh mode); with no site, `clear (no site)`.
- `ymyl` describes the page, not the industry: a homepage that describes services and gives no advice is `false` even for a tax firm or a clinic (say so in one line); it is `true` when the page itself explains a rate, risk, dose or legal right.
- Word range 450 to 900 unless the client asks otherwise. `geo_answer_format` is `direct answer`.

### about-page and contact-page

The client's About page (`page_url` usually `/about/` or `/about-us/`) and Contact page (`/contact/` or `/contact-us/`). Like the homepage, the writer builds each from a fixed section map, so every `### H2:` block carries a `- Section:` line and the sections come in this order (several H2s may share one section). The Answer Target is the Hero: for About, who the client is, what they do and where; for Contact, the fastest way to reach them. Title direction gives the H1 ("About <client>", "Contact <client>").

About page:

| `- Section:` | `### H2:` (a question) | First sentence must state |
|---|---|---|
| Company Story | how the business started | how and when it started and what it does now, from the client files; an owner is not a founder unless a file says so |
| Mission and Values | what the client stands for | the mission and values a file states, in its words and order; never values of your own |
| Team | who does the work | the people a file names, with the role it gives; everyone else is a slot, never an invented crew or team size |
| Credentials | why the client can be trusted | certifications, licenses, insurance, memberships and awards a file states, else slots |

Contact page:

| `- Section:` | `### H2:` (a question) | First sentence must state |
|---|---|---|
| Contact Form | how to send a request | what the form is for; a `- Fields:` line lists each form field, comma-separated (at least three), from the client files or the request, else a slot for the field list |
| Phone and Email | how to call or email | the phone and email, from a client file or a slot |
| Address and Hours | where the client is and when they are open | the street address and opening hours from a client file or slots; a client with no public office says so only when a file does |
| Map | where the map points | the address the map shows (or the area served when a file says there is no public address) |

On both, an embedded FAQ goes after the last section with `- Section: FAQ`, and the `### H2 (CTA):` block carries `- Section: Final CTA`: the next action and its route (a path listed in Links from this page, the phone, or a slot), and what happens after the visitor gets in touch when a file says so.

Rules that differ from other formats:
- The homepage's client-fact rule applies in full, emails and people's names included: copy each from a client file exactly or slot it. Run the gate with `--client-dir` or `--facts`; it traces phones, emails, addresses, hours, quotes and proof claims, but not people's names, so check every name against the files yourself in Step 6.
- 4 to 8 sub-question sections (one per section at least), not 5 to 8.
- `- Evidence: none needed` is allowed for Mission and Values, Team and Final CTA on an About page and for every section of a Contact page. Company Story and Credentials use the client's own evidence (`file:` rows) where it exists.
- Author, Experience and Trust: `- Author: none (an About or Contact page has no byline)`; the trust elements are the Credentials facts.
- Links to this page is the site navigation, so one row `| site navigation | <anchor> | planned |` is enough; Links from this page holds the conversion page (the estimate or booking page) and, on About, the main service pages.
- `ymyl: false` (the pages describe the client, they give no advice). `geo_candidate` and `geo_answer_format` are copied from the row.
- Word range: About 400 to 800, Contact 150 to 400, unless the client asks otherwise.

## Embedded formats

### faq
An H2 "Frequently Asked Questions" with 3 to 5 H3 questions not already answered under their own H2, each a 2 to 4 sentence standalone answer with a specific. Never "Yes, we do."

### comparison-table
One table naming both options in the header, one row per attribute, sourced cells, placed in the section that compares them.

### steps
A numbered sequence inside the section it belongs to; imperative verb first; safety lines called out.

### checklist
A numbered checklist inside its section; each item an action with its interval.

### cost-table
A table of items or scenarios with ranges and sources, placed in the cost section.
