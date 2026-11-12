---
name: industry-restrictions-matrix
description: Build or update a per-client matrix of advertising restrictions by platform and geography for the client's industry (for example legal, healthcare, financial, home services, education, real estate, supplements, alcohol, cannabis, gambling), covering certifications, required disclosures, prohibited claims, targeting limits, and special ad categories, with source links and verification dates, saved to the client's context for other skills to use. Use whenever a client is in a regulated or restricted industry, before first launch, when expanding to a new platform or state, when the user asks what they can and cannot advertise, or when asked for a compliance reference for a vertical.
---

# Industry Restrictions Matrix

Restrictions are the part of paid media that quietly kills campaigns: a missing certification, a banned targeting option, a claim that cannot be made. This skill researches them once per client and platform, records them with sources, and lets every other skill (copy, audience builder, policy precheck, launch checklist) reuse the result.

## Principle: sourced and dated, never remembered
Policies vary by platform, country, state, and change often. Every row cites a current source and the date it was checked. Anything unverified is marked as such. This is a working reference, not legal advice; legal and regulatory interpretation belongs to the client's counsel.

## Inputs
- Client industry, specific services, geographies (countries and states), platforms in use or planned
- `clients/<slug>/context.md` for licenses and prior disapprovals

## Process
1. **Classify** the client against each platform's restricted or sensitive categories (including special ad categories such as housing, employment, credit, and social issues).
2. **Research each platform's current policy** for the category and geography using official policy pages first. Record the policy name, URL, and date.
3. **Capture each requirement** in categories:
   - Prerequisites: certifications, verification, licenses, advertiser disclosure
   - Prohibited content and claims
   - Required disclosures and landing page elements
   - Targeting restrictions (audience, location, age, lookalike, retargeting)
   - Tracking and data limits (sensitive data in pixels, lead forms, remarketing)
   - Geographic or state-specific rules (including state bar or board advertising rules where relevant)
4. **Add the practical translation:** what this means for copy (do and avoid examples), audiences, landing pages, and tracking.
5. **Flag uncertainty:** where rules are ambiguous or enforcement is inconsistent, give the conservative reading and mark it for counsel or platform rep confirmation.
6. **Write to the client's context** as a compact summary linking to the full matrix, so other skills load it automatically. Set a review date (typically quarterly).

## Output
Save to `clients/<slug>/restrictions-matrix.md` (a persistent file, not a monthly output) and a short section appended to `clients/<slug>/context.md`.
```
Matrix: rows are requirements, columns are platforms (and geographies where they differ).
Each cell: rule in plain words, source link, date checked, confidence.
Practical guide: copy do and avoid, audience limits, landing page requirements.
Open questions for counsel or the platform rep.
Next review date.
```

## Rules
- Official platform and regulator sources only for the rule itself; commentary may support but never replace them.
- Mark unverified items; never fill a cell from memory.
- Do not advise ways around restrictions.
- Update rather than duplicate: if the matrix exists, revise changed rows and note what changed.
