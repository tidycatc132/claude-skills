---
name: search-persona-generator
description: Research a client's website from its URL and produce 1-3 search personas for the SEO team, each describing who searches for the brand's services, why, at what funnel stage, with sample queries by intent, the SERP features they use, and the pages that would convert them. Use whenever a user gives a website URL and asks for personas, audience profiles, buyer or customer personas, ICPs, "who searches for this", "who are we writing for", "who is their customer", or "profile their audience", even if they don't say the word persona. Also use when a URL is pasted with "build personas", "audience research", or "who is this site for". Do NOT use for keyword research, topical maps, content briefs, article writing, brand audits, or competitor analysis; those take personas as input and have their own skills.
---

# Search Persona Generator

Turn a website URL into 1-3 personas of the people who would search for that business's
services, written for an SEO strategist: situation, trigger moments, funnel stage, queries by
intent, SERP features, decision criteria, and the pages that should capture them.

## Inputs

| Input | Required | Default |
|---|---|---|
| Website URL | yes | - |
| Service area (city / region / "national") | no | taken from the site profile, else "not stated" |
| Persona count | no | up to 3, fewer if the site supports fewer |
| Client notes (audience hints, exclusions, priorities) | no | none |

Never hardcode or assume client details. Everything about the brand comes from the fetched site
profile, the user's notes, or is labeled as an assumption.

## Outputs

All files go in `./personas/` (create it). `<domain>` is the host with `www.` stripped and dots
replaced by dashes.

| File | Purpose |
|---|---|
| `<domain>-site-profile.json` | raw evidence from `scripts/fetch_site_profile.py` |
| `<domain>-personas.md` | the deliverable, structured per `references/persona-template.md` |
| `<domain>-personas.json` | same content, machine-readable, conforming to `references/personas-schema.json` |

## Workflow

### 1. Fetch the site profile

```bash
python3 scripts/fetch_site_profile.py "<url>" --out personas/<domain>-site-profile.json
```

The script fetches the homepage, follows the most relevant same-host links (services, about,
pricing, locations, FAQ; 12 pages max), and extracts titles, meta descriptions, headings,
JSON-LD, CTAs, contact details, service areas and a service list. It never raises; read the
`status` field:

- `ok` - proceed.
- `partial` - few pages or no clear services page. Proceed, but keep the service list to what
  the pages actually show, lean on user notes, and lower persona confidence.
- `unreachable` - the site blocked or timed out (exit code 2). Ask the user to paste the
  homepage text or a service list. If they cannot, build personas from the URL, the business
  category and their notes, set `profile_status: unreachable`, mark every persona `low`
  confidence, and list the assumptions. Do not invent proof points.

Read the JSON fully before writing anything. `organization`, `services`, each page's `h1`/`h2`
and `text_excerpt`, and `ctas` are the evidence base for every claim below.

### 2. Write the brand and services snapshot

In plain words: what they sell, who they serve, where, and the proof points the site offers
(reviews, certifications, years in business, guarantees). List services using the site's own
names; these exact strings are what `services_matched` must reference later. Drop nav items that
are not services (Home, Contact, Blog).

### 3. Decide the personas

Follow section 1 of `references/search-behavior-guide.md`: split by motivation and buying
situation, not demographics; cap at three; merge near-duplicates; one or two is correct for a
single-service brand. Apply the user's persona count or notes if given.

### 4. Write each persona

Fill every section of `references/persona-template.md`. Use the guide's sections 2-6 for the
"How they search" block: 3-5 queries per intent bucket, lower case, no duplicates across
buckets, service area in local queries, question queries that an FAQ answer could satisfy, named
SERP features and modifiers.

Ground each persona in the profile and cite it in **Evidence** (a heading, a schema field, a
page). Confidence is `high` with two or more evidence items, `medium` with one, `low` when it
rests on category knowledge or notes. Anything not confirmed by the site goes in
**Assumptions**.

### 5. Write the SEO usage section

Map each persona to existing pages (from the profile's `pages[].url`) or to pages that should be
created, list content gaps, and name one priority persona with a one-sentence reason.

### 6. Write both files and validate

Write `<domain>-personas.md` and `<domain>-personas.json` from the same facts, then:

```bash
python3 scripts/validate_personas.py personas/<domain>-personas.json
```

Fix every `FAIL` line and re-run until it prints `OK`. Common failures: a `services_matched`
entry that is not in `brand.services`, a query repeated across intent buckets, fewer than three
queries in a bucket, `persona_count` not matching the personas array.

### 7. Report

Tell the user: the profile status, how many pages were read, the persona names with one line
each, the priority persona, and the three file paths. Flag any assumptions or an unreachable site
up front.

## Done criteria

- Site profile written, or an explicit unreachable fallback with assumptions listed.
- 1-3 personas, every template section filled, no placeholder text.
- Every brand claim traceable to the profile, user notes, or the Assumptions list.
- `validate_personas.py` prints `OK` for the JSON file.
- The markdown and JSON agree on names, services, queries and the priority persona.

## Quality bar

- Persona names encode motivation ("Emergency Erin"), never real customer names from the site.
- Queries read as a person types them; a strategist can paste them into a keyword tool as-is.
- Content recommendations name page types the team can build (service page, city page, cost
  guide, comparison, FAQ block, case study), not vague "create engaging content".
- Keep the deliverable under roughly 1,500 words for three personas; density over length.

## References

- `references/persona-template.md` - exact markdown structure and per-section guidance.
- `references/search-behavior-guide.md` - persona selection, intent buckets, modifiers, SERP
  features, funnel stages, persona-to-page mapping.
- `references/personas-schema.json` - JSON contract for `<domain>-personas.json`.
- `evals/files/sample-personas.json` - a complete, valid example to pattern-match against.
