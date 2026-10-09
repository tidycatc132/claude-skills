# Persona deliverable template

Produce `<domain>-personas.md` with exactly this structure. Headings are fixed so the SEO team
can skim any client's personas the same way. Prose inside each section is yours; keep it
concrete, tied to the site evidence, and free of filler. Every field here has a matching key in
`personas-schema.json`, so write the markdown and the JSON from the same facts.

---

```markdown
# Search Personas: {Brand name}

Source: {URL} · Generated: {YYYY-MM-DD} · Site profile: {ok | partial | unreachable}
Personas: {N} · Service area: {from profile or user, else "not stated"}

## Brand & services snapshot
**What they sell:** one or two sentences in plain words.
**Who they serve:** segments the site actually addresses (homeowners, clinics, SaaS teams…).
**Where:** cities / regions / "national" / "online only".
**Proof points:** bullets of credibility signals found on the site (reviews, certifications, years, awards).
**Services found:** bullet list, one per service, named the way the site names them.

**Assumptions:** bullets for anything stated below that the site did not confirm. Omit if none.

---

## Persona 1: {Alliterative name that encodes the motivation, e.g. "Emergency Erin"}
> {One-liner: who they are and why they are searching, 25 words max.}

| | |
|---|---|
| **Role** | {household role or job title} |
| **Age range** | {e.g. 35-55} |
| **Location** | {where they are, relative to the service area} |
| **Device** | {mobile / desktop and the context} |
| **Funnel stage** | awareness / consideration / decision / mixed |
| **Confidence** | high / medium / low |

**Situation.** 2-4 sentences. What is happening in their life or business that leads to search.

**Goals**
- 2-4 bullets. Outcomes, not tasks.

**Pain points**
- 2-4 bullets. What has gone wrong before or what they fear.

**Trigger moments**
- 2-4 bullets. The specific event that makes them open a search box.

### How they search
**Informational** (learning): 3-5 queries, lower-case, as typed.
**Commercial** (comparing): 3-5 queries.
**Transactional** (ready to act): 3-5 queries.
**Questions they ask**: 3-5 natural-language questions (feed PAA / FAQ / AEO).
**SERP features they use**: local pack, reviews, PAA, video, shopping, AI overviews…
**Modifiers**: near me, cost, best, vs, emergency, for small business…

**Decision criteria**
- 2-4 bullets. What makes them pick one provider over another.

**Objections**
- 1-3 bullets. Why they might not convert.

**Content that wins them**
- 2-4 bullets. Page types or topics, each tied to a stage.

**Services matched:** comma-separated, using the names from "Services found".
**Evidence:** 1-3 bullets citing the page / heading / schema that supports this persona.

---

(repeat for Persona 2 and 3)

---

## How the SEO team should use this
| Persona | Target pages (existing or new) |
|---|---|
| {name} | {page, page, page} |

**Content gaps:** bullets. Pages or topics no persona can currently land on.
**Priority persona:** {name} and one sentence on why (volume, revenue, or ease).
```

---

## Section guidance

- **Name.** Alliteration plus motivation ("Planning Pat", "Portfolio Priya"). It should tell a
  writer the intent at a glance. Never use a real customer name from the site.
- **Funnel stage.** Pick the stage where this persona *mostly* enters search. Use "mixed" only
  for personas that genuinely research and buy in the same session (B2B buyers, emergencies that
  still compare).
- **Confidence.** `high` when two or more site pages or schema items support the persona.
  `medium` when one does. `low` when it rests on category knowledge or user notes only; say so
  in Assumptions.
- **Queries.** Write them as a person would type, lower case, no quotes. Mix head terms with
  long-tail. Include the service area in some commercial and transactional queries when the
  business is local. Do not repeat the same query across buckets.
- **Evidence.** Point at something concrete: `Homepage H2 "Emergency AC & Furnace Repair"`,
  `JSON-LD areaServed: Bayport, Sayville`, `Services page: "Manual J load calculations"`.
- **Content that wins them.** Prefer page types the team can actually build: service page,
  city page, comparison guide, cost guide, FAQ block, case study.
