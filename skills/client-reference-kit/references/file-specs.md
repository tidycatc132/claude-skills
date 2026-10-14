# File specs

Each file uses exactly these `##` headings, in this order, then ends with `## Sources`. `scripts/check_kit.py` matches the heading text (case, punctuation and accents ignored, so `Cliches` passes for `Clichés`), so keep the wording; extra `##` sections may follow the required ones and go before `## Sources`.

Open every file with one line: `Client: <legal or trading name> · Site: <domain> · Built: <YYYY-MM-DD>`.

## brand.md

| Heading | What goes in it |
| :--- | :--- |
| `## Core Positioning` | A one-sentence positioning statement (for whom, what, how it differs), the mission (quote the client's wording when it exists and cite it), and the UVP in one line. |
| `## Offer Architecture` | Every product, service, tier, package and add-on with the current price and what is included. Name the price source and date. List retired offers or prices under a `Retired, do not use` line. |
| `## Key Differentiators` | 3 to 6 tangible advantages: a feature, a process, a credential, a business-model choice. Each says what competitors do instead when the sources say so. |
| `## Approved Claims & Proof Points` | Table `| Claim | Exact approved wording | Source | Date checked |`. Only claims a source backs. Claims found but not approved go in a second table `| Claim | Why not to use | Source |`. Then one line per proof type the sources lack (statistics, ratings or reviews, awards, certifications, press), for example `GAP: no awards or press found in any source; ask the owner for awards, competition scores or coverage`. |
| `## Call-to-Action Library` | `### High intent` (book, buy, call, start), `### Mid intent` (free consult, quote, demo, trial), `### Low intent` (guide, newsletter, quiz). Each CTA is button text plus where it links. Build them from real offers. |

## voice.md

| Heading | What goes in it |
| :--- | :--- |
| `## Voice Dimensions` | 3 or 4 `###` traits written as "X, not Y" (for example `### Direct, not blunt`). Under each: an operational definition a writer can test a sentence against, and one sentence that passes. |
| `## Tone Matrix` | Table `| Context | Tone shift | Example line |` with 3 or more rows chosen from the client's real channels: landing page, blog or guide, email, social, support reply, technical or clinical doc, ad. |
| `## Do / Don't Examples` | Table `| Do | Don't | Why |` with 5 or more pairs. Each pair is about this client's offers, customers or claims, never a generic sentence. |
| `## Reading Level & Cadence` | Numeric targets: grade level (Flesch-Kincaid), average and maximum sentence length in words, active-voice share, paragraph length, how often to use second person. |

## style.md

| Heading | What goes in it |
| :--- | :--- |
| `## Grammar & Localization` | English variant, serial comma (yes or no), date format, time format, currency format, units. Take each from the client's own pages when they show one; say which page. |
| `## Formatting Conventions` | Heading case (sentence or title), list punctuation, bold and italics use, numbers (spell out below 10 or always digits), percentages, phone numbers and addresses. |
| `## Brand Lexicon` | Table `| Term | Use | Never |` for the company name, every product and program name, trademarks, credentials, acronyms and the industry words the client prefers. |
| `## Banned Words & Clichés` | Words and phrases the client rejects (quote who said so), then industry clichés to avoid, then each with a replacement. |
| `## Citation & Linking Rules` | When to link, which sources count as authoritative for this industry, anchor-text rules (descriptive, no "click here"), internal-link targets that matter (booking page, pricing), external links opening behaviour, `rel` rules for sponsored or affiliate links. |

## audience.md

| Heading | What goes in it |
| :--- | :--- |
| `## Ideal Customer Profile` | For B2B: company size, revenue, verticals, geography, tech stack. For B2C: age band, location or service area, life situation, budget, buying trigger. Add who NOT to target when the sources say so. |
| `## Key Personas` | 2 or 3 `###` personas, each with a name and role, goals and KPIs (or for consumers, what success looks like), a typical day or workflow, the trigger that makes them search, and the channel where they look. Merge segments that differ only by demographics. |
| `## Core Pain Points` | Operational, financial and emotional pain, each tied to the offer that solves it. |
| `## Objection Handling` | Table `| Objection | Counter-framing | Proof to cite |` with 4 or 5 rows. Each counter uses a client fact from brand.md. |

## compliance.md

| Heading | What goes in it |
| :--- | :--- |
| `## Regulatory Framework` | Table `| Body or law | Why it applies to this client | What it means for content |`. Use `references/regulatory-starters.md` to find candidates, then keep only the ones the client's industry, geography, channels and offers trigger. |
| `## Mandatory Disclaimers` | Exact boilerplate in quote blocks, each with where it must appear. Copy the client's own wording from terms, privacy or pricing pages when it exists and cite the page. Where the client has none and a rule requires one, write it and label it `Proposed, needs legal approval`. |
| `## Prohibited Claims` | Absolute guarantees, outcome promises, unapproved certifications, superlatives without proof, and every claim the client or the sources ruled out, each with a safe alternative. |
| `## Review Triggers` | Table `| Content type | Reviewer | Why |`. Name the person or role from the sources (owner, clinical director, legal, compliance officer). |

## Sources (every file)

List each source used for this file, one per line, with its tier: `[internal] project/kickoff-notes.md`, `[site] https://example.com/pricing`, `[search] <url> (query used)`. Under `### Conflicts resolved`, record every contradiction as `topic: kept X from <source>, dropped Y from <source>`.

## Gaps

A required fact the sources do not contain is written as a line starting `GAP:` naming what is missing and who can supply it, for example `GAP: no awards or certifications found; ask the practice manager`. A sensible default may follow it, labelled `Recommended`. The section stays, never empty and never filled with invented data.
