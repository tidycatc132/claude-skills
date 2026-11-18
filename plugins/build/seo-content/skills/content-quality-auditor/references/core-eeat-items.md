# CORE-EEAT Item Catalog (80 items, catalog 20.1.0)

The complete, authoritative item list for this skill. Every audit evaluates all 80 stable IDs below. Item IDs never change; show them qualified (`CORE-EEAT-C01`) whenever they appear outside a single CORE-EEAT table.

**8 dimensions x 10 items = 80 criteria.** CORE (C, O, R, E) primarily evaluates the content body and drives the GEO view; EEAT (Exp, Ept, A, T) primarily evaluates author, organization, and site credibility and drives the SEO view. The two halves are not independent (citations, authorship, disclosure, and editorial controls cross the boundary): give each item one scoring owner, never double-count, but keep the dependency visible in findings.

| Abbr | Dimension | Core question |
|---|---|---|
| C | Contextual Clarity | Does the content clearly answer the user's intent? |
| O | Organization | Is the content structured for both humans and machines? |
| R | Referenceability | Can AI and readers verify and cite the claims? |
| E | Exclusivity | Does the content offer something unavailable elsewhere? |
| Exp | Experience | Does the author demonstrate real-world experience? |
| Ept | Expertise | Does the author demonstrate professional expertise? |
| A | Authority | Is the author/org recognized as an authority? |
| T | Trust | Does the site meet trust and safety standards? |

Priority tags: **GEO-first** = critical for AI-engine citation; **SEO-first** = critical for traditional ranking; **Dual** = both.

## Quick index

| C | O | R | E | Exp | Ept | A | T |
|---|---|---|---|---|---|---|---|
| C01 Intent Alignment (veto) | O01 Heading Hierarchy | R01 Data Precision | E01 Original Data* | Exp01 First-Person Narrative* | Ept01 Author Identity | A01 Backlink Profile | T01 Legal Compliance |
| C02 Direct Answer | O02 Summary Box | R02 Citation Density | E02 Novel Framework* | Exp02 Sensory Details* | Ept02 Credentials Display | A02 Media Mentions | T02 Contact Transparency |
| C03 Query Coverage | O03 Data Tables* | R03 Source Hierarchy | E03 Primary Research* | Exp03 Process Documentation | Ept03 Professional Vocabulary | A03 Industry Awards | T03 Security Standards |
| C04 Definition First | O04 List Formatting | R04 Evidence-Claim Mapping | E04 Contrarian View* | Exp04 Tangible Proof* | Ept04 Technical Depth | A04 Publishing Record | T04 Disclosure Statements* (veto) |
| C05 Topic Scope | O05 Schema Markup* | R05 Methodology Transparency | E05 Proprietary Visuals* | Exp05 Usage Duration* | Ept05 Methodology Rigor | A05 Brand Recognition | T05 Editorial Policy |
| C06 Audience Targeting | O06 Section Chunking | R06 Timestamp & Versioning | E06 Gap Filling | Exp06 Problems Encountered | Ept06 Edge Case Awareness | A06 Social Proof | T06 Correction & Update Policy |
| C07 Semantic Coherence | O07 Visual Hierarchy | R07 Entity Precision | E07 Practical Tools | Exp07 Before/After Comparison* | Ept07 Historical Context | A07 Knowledge Graph Presence* | T07 Ad Experience |
| C08 Use Case Mapping | O08 Anchor Navigation | R08 Internal Link Graph | E08 Depth Advantage | Exp08 Quantified Metrics | Ept08 Reasoning Transparency | A08 Entity Consistency | T08 Risk Disclaimers* |
| C09 FAQ Coverage | O09 Information Density | R09 HTML Semantics | E09 Synthesis Value | Exp09 Repeated Testing* | Ept09 Cross-domain Integration | A09 Partnership Signals | T09 Review Authenticity |
| C10 Semantic Closure | O10 Multimedia Structure* | R10 Content Consistency (veto) | E10 Forward Insights* | Exp10 Limitations Acknowledged | Ept10 Editorial Process | A10 Community Standing | T10 Customer Support |

`*` = conditional item (may be `na` only under its stated condition). Every other item is unconditional: it is `pass`, `partial`, `fail`, or `unknown`, never `na`.

## The 18 conditional items (the only items that may be `na`)

| ID | Applies only when | Typical `na` reason |
|---|---|---|
| O03 | the artifact contains comparable structured data | "no specs or comparable attributes to tabulate" |
| O05 | the artifact is an indexable web page eligible for structured data | "internal PDF / email / non-indexable draft format" |
| O10 | multimedia is part of the declared artifact | "text-only artifact by design" |
| E01 | original data is part of the content promise | "piece does not promise first-party data" |
| E02 | the content claims a novel framework | "no framework claimed" |
| E03 | primary research is part of the content promise | "no study/experiment promised" |
| E04 | the content takes a contrarian position | "no contrarian stance taken" |
| E05 | original visuals are needed to support the artifact | "visual explanation not needed for this artifact" |
| E10 | the content makes forward-looking claims | "no predictions or trend claims" |
| Exp01 | first-person experience is claimed or required by the profile | "reference FAQ; no experience claimed or required" |
| Exp02 | sensory observation is material to the subject | "software/abstract subject" |
| Exp04 | the artifact claims hands-on use | "no hands-on claim" |
| Exp05 | usage duration is material | "duration irrelevant to the claim" |
| Exp07 | a before/after claim is made | "no change/improvement claim" |
| Exp09 | repeat testing is claimed | "no repeated-test claim" |
| A07 | knowledge-graph presence is material to the audit objective | "objective is a single article, entity presence not material" |
| T04 | a material connection, paid placement, or affiliate relationship exists | "no affiliate links, sponsorship, free product, or paid placement found" |
| T08 | the artifact makes YMYL or other material-risk claims | "non-YMYL topic, no health/money/legal/safety claims" |

Rules: `na` needs a written reason tied to the condition. If you cannot tell whether the condition holds (e.g. you cannot see whether links are affiliate links), the item is `unknown`, not `na`. Product-review and testimonial profiles normally require first-person experience, so Exp01 applies to them.

## Veto items

| Veto ID | Dimension | What a verified Fail means |
|---|---|---|
| `CORE-EEAT-C01` | Contextual Clarity | Clickbait: the title/promise materially mismatches what the page delivers |
| `CORE-EEAT-R10` | Referenceability | Two parts of the artifact make materially incompatible factual or numerical claims (an isolated broken link is NOT this veto; it is a Partial) |
| `CORE-EEAT-T04` | Trust | A material connection exists and the required disclosure is absent or materially obscured (no relationship = `na`, not Partial) |

A veto triggers only on a verified `fail`. Missing access or unobserved evidence makes the veto item `unknown`, never `fail`. Veto arithmetic (59 cap, BLOCK) lives in [scoring-rules.md](scoring-rules.md).

## Item definitions and scoring anchors

Points: Pass 10 · Partial 5 · Fail 0. Use the anchor that best matches the evidence; when torn between two anchors, pick the lower one and say why.

## C — Contextual Clarity

### C01 — Intent Alignment (Dual) — **VETO**
- **ID:** `CORE-EEAT-C01` · **Standard:** Title promise = content delivery
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Title promise fully delivered; intent type clear.
- **Partial (5):** Mostly aligned with minor drift.
- **Fail (0):** Clickbait; content doesn't match title.

### C02 — Direct Answer (GEO-first)
- **ID:** `CORE-EEAT-C02` · **Standard:** Core answer in first 150 words
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** First 150 words contain clear definition or conclusion (directly citable by AI).
- **Partial (5):** Answer within first 300 words with lengthy preamble.
- **Fail (0):** Answer buried in middle or end.

### C03 — Query Coverage (Dual)
- **ID:** `CORE-EEAT-C03` · **Standard:** Covers ≥3 query variants (synonyms, long-tail)
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Covers ≥3 query variants; appropriate entity density.
- **Partial (5):** 1–2 variants.
- **Fail (0):** Single exact query only.

### C04 — Definition First (GEO-first)
- **ID:** `CORE-EEAT-C04` · **Standard:** Key terms defined on first use
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** All key terms defined on first use.
- **Partial (5):** Most terms defined.
- **Fail (0):** Terms used without definition.

### C05 — Topic Scope (GEO-first)
- **ID:** `CORE-EEAT-C05` · **Standard:** Explicitly states what is and isn't covered
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Explicitly states "This covers X, not Y"; meets AI completeness threshold.
- **Partial (5):** Implied boundaries.
- **Fail (0):** Scope unclear; content sprawls.

### C06 — Audience Targeting (Dual)
- **ID:** `CORE-EEAT-C06` · **Standard:** States "this article is for..."
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Explicitly states target reader; language matches audience.
- **Partial (5):** Implied through difficulty.
- **Fail (0):** Audience unclear; inconsistent difficulty.

### C07 — Semantic Coherence (GEO-first)
- **ID:** `CORE-EEAT-C07` · **Standard:** Logical flow between paragraphs, no jumps
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Logical connectors between paragraphs; no semantic jumps.
- **Partial (5):** Mostly coherent with occasional jumps.
- **Fail (0):** Frequent logic breaks.

### C08 — Use Case Mapping (GEO-first)
- **ID:** `CORE-EEAT-C08` · **Standard:** Decision framework: when to choose A vs B
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Clearly states applicable/inapplicable scenarios; decision framework provided.
- **Partial (5):** Some scenarios mentioned.
- **Fail (0):** No use case guidance.

### C09 — FAQ Coverage (GEO-first)
- **ID:** `CORE-EEAT-C09` · **Standard:** Structured FAQ covering long-tail follow-ups
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Structured FAQ with FAQPage Schema covering long-tail follow-ups.
- **Partial (5):** Q&A content but not structured.
- **Fail (0):** No FAQ or Q&A.

### C10 — Semantic Closure (Dual)
- **ID:** `CORE-EEAT-C10` · **Standard:** Conclusion answers the opening question + next steps
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Conclusion answers opening question + provides next steps.
- **Partial (5):** Conclusion but doesn't loop back.
- **Fail (0):** No conclusion or unrelated.


## O — Organization

### O01 — Heading Hierarchy (Dual)
- **ID:** `CORE-EEAT-O01` · **Standard:** H1→H2→H3, no level skipping
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Single H1; H2→H3 nested; no level skipping.
- **Partial (5):** Minor skipping but clear.
- **Fail (0):** Chaotic hierarchy, multiple H1s.

### O02 — Summary Box (GEO-first)
- **ID:** `CORE-EEAT-O02` · **Standard:** Has TL;DR or Key Takeaways section
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Prominent TL;DR or Key Takeaways box.
- **Partial (5):** Summary but not prominent.
- **Fail (0):** No summary.

### O03 — Data Tables (GEO-first)
- **ID:** `CORE-EEAT-O03` · **Standard:** Comparisons and specs presented in tables
- **Applicability:** Conditional — applies only when the artifact contains comparable structured data; otherwise `na` with reason
- **Pass (10):** HTML tables for comparisons/specs with clear headers.
- **Partial (5):** Tables but unclear.
- **Fail (0):** Prose where tables would be better.

### O04 — List Formatting (GEO-first)
- **ID:** `CORE-EEAT-O04` · **Standard:** Parallel items use bullet or numbered lists
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** ~1–2 lists per 500 words; parallel items listed.
- **Partial (5):** Insufficient or excessive.
- **Fail (0):** Overused or absent.

### O05 — Schema Markup (GEO-first)
- **ID:** `CORE-EEAT-O05` · **Standard:** Appropriate JSON-LD (Article/FAQ/HowTo/etc.)
- **Applicability:** Conditional — applies only when the artifact is an indexable web page eligible for structured data; otherwise `na` with reason
- **Pass (10):** Correct JSON-LD matching content type.
- **Partial (5):** Schema but wrong type.
- **Fail (0):** No schema.

### O06 — Section Chunking (GEO-first)
- **ID:** `CORE-EEAT-O06` · **Standard:** Each section has single topic; paragraphs 3–5 sentences
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Each section single topic; paragraphs 3–5 sentences.
- **Partial (5):** Most clear; some too long.
- **Fail (0):** Mixed topics; walls of text.

### O07 — Visual Hierarchy (SEO-first)
- **ID:** `CORE-EEAT-O07` · **Standard:** Key concepts bolded or highlighted
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Important content bolded/highlighted; key concepts emphasized.
- **Partial (5):** Some emphasis.
- **Fail (0):** No visual hierarchy.

### O08 — Anchor Navigation (Dual)
- **ID:** `CORE-EEAT-O08` · **Standard:** Table of contents with jump links
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Table of contents with anchor links; breadcrumbs.
- **Partial (5):** TOC but no anchors.
- **Fail (0):** Long content without navigation.

### O09 — Information Density (GEO-first)
- **ID:** `CORE-EEAT-O09` · **Standard:** No filler; consistent terminology throughout
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** High information density; no filler; consistent terminology.
- **Partial (5):** Minor repetition.
- **Fail (0):** Significant filler.

### O10 — Multimedia Structure (Dual)
- **ID:** `CORE-EEAT-O10` · **Standard:** Images/videos have captions and carry information
- **Applicability:** Conditional — applies only when multimedia is part of the declared artifact; otherwise `na` with reason
- **Pass (10):** Images/videos have captions; positioned purposefully.
- **Partial (5):** Multimedia but lacks descriptions.
- **Fail (0):** No multimedia or decorative only.


## R — Referenceability

### R01 — Data Precision (GEO-first)
- **ID:** `CORE-EEAT-R01` · **Standard:** ≥5 precise numbers with units (%, $, ms)
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** ≥5 precise data points with units; directly extractable.
- **Partial (5):** 2–4 data points.
- **Fail (0):** No precise data; vague descriptions.

### R02 — Citation Density (GEO-first)
- **ID:** `CORE-EEAT-R02` · **Standard:** ≥1 external citation per 500 words
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** ≥1 external citation per 500 words; ≥3 source types.
- **Partial (5):** ≥1 per 1000 words; 2 types.
- **Fail (0):** Insufficient citations.

### R03 — Source Hierarchy (GEO-first)
- **ID:** `CORE-EEAT-R03` · **Standard:** Primary sources first; ≥3 Tier 1–2 sources
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Primary sources prioritized; ≥3 Tier 1–2 sources.
- **Partial (5):** 1–2 Tier 1–2.
- **Fail (0):** No authoritative sources.

### R04 — Evidence-Claim Mapping (GEO-first)
- **ID:** `CORE-EEAT-R04` · **Standard:** Every claim backed by evidence immediately after
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Every core claim immediately followed by evidence.
- **Partial (5):** Most claims backed.
- **Fail (0):** Multiple claims without evidence.

### R05 — Methodology Transparency (GEO-first)
- **ID:** `CORE-EEAT-R05` · **Standard:** Sample size, steps, and criteria documented
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Sample size, steps, criteria documented; reproducible.
- **Partial (5):** Partial methodology.
- **Fail (0):** No methodology.

### R06 — Timestamp & Versioning (Dual)
- **ID:** `CORE-EEAT-R06` · **Standard:** Last updated <1 year; version changes noted
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Updated <1 year; date visible; version notes.
- **Partial (5):** 1–3 years old.
- **Fail (0):** >3 years or no date.

### R07 — Entity Precision (GEO-first)
- **ID:** `CORE-EEAT-R07` · **Standard:** Full names for people/orgs/products; no "a company"
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Full names for entities; no vague references.
- **Partial (5):** Most precise; occasional vagueness.
- **Fail (0):** Frequent vague references.

### R08 — Internal Link Graph (SEO-first)
- **ID:** `CORE-EEAT-R08` · **Standard:** Descriptive anchor texts forming topic clusters
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Descriptive anchors forming topic clusters.
- **Partial (5):** Links but non-descriptive anchors.
- **Fail (0):** No internal links or "click here".

### R09 — HTML Semantics (GEO-first)
- **ID:** `CORE-EEAT-R09` · **Standard:** Uses `<article>`, `<figure>`, `<time>`, `<cite>`
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Correct semantic tags (`<article>`, `<figure>`, `<time>`, `<cite>`).
- **Partial (5):** Some tags.
- **Fail (0):** Pure `<div>` markup.

### R10 — Content Consistency (Dual) — **VETO**
- **ID:** `CORE-EEAT-R10` · **Standard:** No material internal factual contradiction; isolated broken links are remediable findings
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Material facts and calculations are internally consistent; cited links resolve at the observation date; corrections are traceable.
- **Partial (5):** An isolated broken link, stale non-material reference, or wording inconsistency exists without changing the substantive conclusion.
- **Fail (0):** Two parts of the artifact make materially incompatible factual or numerical claims → **Veto triggered**.


## E — Exclusivity

### E01 — Original Data (GEO-first)
- **ID:** `CORE-EEAT-E01` · **Standard:** First-party surveys, experiments, or statistics
- **Applicability:** Conditional — applies only when original data is part of the content promise; otherwise `na` with reason
- **Pass (10):** First-party data; dataset is citable.
- **Partial (5):** Some original data.
- **Fail (0):** All data from others.

### E02 — Novel Framework (GEO-first)
- **ID:** `CORE-EEAT-E02` · **Standard:** Named, citable original framework or model
- **Applicability:** Conditional — applies only when the content claims a novel framework; otherwise `na` with reason
- **Pass (10):** Named, citable original framework.
- **Partial (5):** Innovates on existing.
- **Fail (0):** No framework innovation.

### E03 — Primary Research (GEO-first)
- **ID:** `CORE-EEAT-E03` · **Standard:** Original experiments/surveys with documented process
- **Applicability:** Conditional — applies only when primary research is part of the content promise; otherwise `na` with reason
- **Pass (10):** Documented research process (conditions, metrics, controls).
- **Partial (5):** Some primary research.
- **Fail (0):** No primary research.

### E04 — Contrarian View (GEO-first)
- **ID:** `CORE-EEAT-E04` · **Standard:** Challenges consensus with evidence
- **Applicability:** Conditional — applies only when the content takes a contrarian position; otherwise `na` with reason
- **Pass (10):** Challenges consensus with data/logic.
- **Partial (5):** Some differentiated views.
- **Fail (0):** Entirely follows convention.

### E05 — Proprietary Visuals (Dual)
- **ID:** `CORE-EEAT-E05` · **Standard:** ≥2 original infographics, charts, or diagrams
- **Applicability:** Conditional — applies only when original visuals are needed to support the artifact; otherwise `na` with reason
- **Pass (10):** ≥2 original infographics/charts/visualizations.
- **Partial (5):** 1 original.
- **Fail (0):** No original visuals.

### E06 — Gap Filling (GEO-first)
- **ID:** `CORE-EEAT-E06` · **Standard:** Covers questions competitors don't
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Covers niche questions competitors miss.
- **Partial (5):** Partially fills gaps.
- **Fail (0):** Highly similar to competitors.

### E07 — Practical Tools (Dual)
- **ID:** `CORE-EEAT-E07` · **Standard:** Downloadable templates, checklists, or calculators
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** ≥1 downloadable template/checklist/calculator.
- **Partial (5):** Examples but not actionable.
- **Fail (0):** No practical tools.

### E08 — Depth Advantage (GEO-first)
- **ID:** `CORE-EEAT-E08` · **Standard:** Deeper than competing content on same topic
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Depth clearly exceeds competitors.
- **Partial (5):** Comparable depth.
- **Fail (0):** Shallower than competitors.

### E09 — Synthesis Value (GEO-first)
- **ID:** `CORE-EEAT-E09` · **Standard:** Cross-domain knowledge combination (A+B=C)
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Cross-domain knowledge producing new insights.
- **Partial (5):** Some cross-domain but not novel.
- **Fail (0):** Single domain only.

### E10 — Forward Insights (GEO-first)
- **ID:** `CORE-EEAT-E10` · **Standard:** Data-backed predictions and trend analysis
- **Applicability:** Conditional — applies only when the content makes forward-looking claims; otherwise `na` with reason
- **Pass (10):** Data-backed predictions with clear reasoning.
- **Partial (5):** Some forward-looking.
- **Fail (0):** Only past/present.


## Exp — Experience

### Exp01 — First-Person Narrative (SEO-first)
- **ID:** `CORE-EEAT-Exp01` · **Standard:** Contains "I tested" or "We found" + action verbs
- **Applicability:** Conditional — applies only when first-person experience is claimed or required by the profile; otherwise `na` with reason
- **Pass (10):** First-person + action verb combinations.
- **Partial (5):** Only one of the two.
- **Fail (0):** Entirely third-person.

### Exp02 — Sensory Details (SEO-first)
- **ID:** `CORE-EEAT-Exp02` · **Standard:** ≥10 sensory words (smooth, heavy, bright)
- **Applicability:** Conditional — applies only when sensory observation is material to the subject; otherwise `na` with reason
- **Pass (10):** ≥10 sensory words.
- **Partial (5):** 5–9.
- **Fail (0):** <5.

### Exp03 — Process Documentation (Dual)
- **ID:** `CORE-EEAT-Exp03` · **Standard:** Step-by-step process with timeline
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Detailed process with steps, timeline, decision points.
- **Partial (5):** Partial process.
- **Fail (0):** None.

### Exp04 — Tangible Proof (SEO-first)
- **ID:** `CORE-EEAT-Exp04` · **Standard:** ≥2 original photos/screenshots with timestamps
- **Applicability:** Conditional — applies only when the artifact claims hands-on use; otherwise `na` with reason
- **Pass (10):** ≥2 original images with timestamps/context.
- **Partial (5):** 1 original.
- **Fail (0):** None.

### Exp05 — Usage Duration (SEO-first)
- **ID:** `CORE-EEAT-Exp05` · **Standard:** States "after X months of use..."
- **Applicability:** Conditional — applies only when usage duration is material; otherwise `na` with reason
- **Pass (10):** Explicitly states testing/usage duration.
- **Partial (5):** Implied.
- **Fail (0):** None.

### Exp06 — Problems Encountered (Dual)
- **ID:** `CORE-EEAT-Exp06` · **Standard:** Shares ≥2 real problems + solutions
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** ≥2 problems with solutions/workarounds.
- **Partial (5):** 1 problem.
- **Fail (0):** All positive.

### Exp07 — Before/After Comparison (SEO-first)
- **ID:** `CORE-EEAT-Exp07` · **Standard:** Shows change, improvement, or difference
- **Applicability:** Conditional — applies only when a before/after claim is made; otherwise `na` with reason
- **Pass (10):** Clear before/after or side-by-side comparison.
- **Partial (5):** Implied.
- **Fail (0):** None.

### Exp08 — Quantified Metrics (Dual)
- **ID:** `CORE-EEAT-Exp08` · **Standard:** Measurable experience data (time, cost, success rate)
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Quantified experience data.
- **Partial (5):** Some quantified.
- **Fail (0):** Purely subjective.

### Exp09 — Repeated Testing (SEO-first)
- **ID:** `CORE-EEAT-Exp09` · **Standard:** Multiple tests or long-term tracking
- **Applicability:** Conditional — applies only when repeat testing is claimed; otherwise `na` with reason
- **Pass (10):** Multiple tests or long-term tracking.
- **Partial (5):** Implied.
- **Fail (0):** Single test.

### Exp10 — Limitations Acknowledged (GEO-first)
- **ID:** `CORE-EEAT-Exp10` · **Standard:** States "we only tested X scenario"
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Explicitly states experience limitations.
- **Partial (5):** Partially acknowledges.
- **Fail (0):** None.


## Ept — Expertise

### Ept01 — Author Identity (SEO-first)
- **ID:** `CORE-EEAT-Ept01` · **Standard:** Byline + avatar + bio (>30 words)
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Byline + avatar + bio (>30 words).
- **Partial (5):** 1–2 of these.
- **Fail (0):** No author info.

### Ept02 — Credentials Display (SEO-first)
- **ID:** `CORE-EEAT-Ept02` · **Standard:** Relevant degrees, certs, years of experience
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Relevant professional qualifications displayed.
- **Partial (5):** Weak relevance.
- **Fail (0):** None.

### Ept03 — Professional Vocabulary (Dual)
- **ID:** `CORE-EEAT-Ept03` · **Standard:** Accurate industry jargon, no misuse
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Accurate industry jargon; no misuse.
- **Partial (5):** Moderate.
- **Fail (0):** Too simple or misused.

### Ept04 — Technical Depth (Dual)
- **ID:** `CORE-EEAT-Ept04` · **Standard:** Parameters, thresholds, examples are actionable
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Technical details accurate; parameters/thresholds actionable.
- **Partial (5):** Shallow.
- **Fail (0):** Superficial or errors.

### Ept05 — Methodology Rigor (GEO-first)
- **ID:** `CORE-EEAT-Ept05` · **Standard:** Analysis method is reproducible
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Methodology clear, reproducible, follows standards.
- **Partial (5):** Not rigorous enough.
- **Fail (0):** No methodology or flawed.

### Ept06 — Edge Case Awareness (Dual)
- **ID:** `CORE-EEAT-Ept06` · **Standard:** Discusses ≥2 exceptions or "when this doesn't apply"
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** ≥2 edge cases discussed.
- **Partial (5):** 1 edge case.
- **Fail (0):** None.

### Ept07 — Historical Context (SEO-first)
- **ID:** `CORE-EEAT-Ept07` · **Standard:** Shows knowledge of the field's evolution
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Demonstrates field's development history.
- **Partial (5):** Some background.
- **Fail (0):** No historical perspective.

### Ept08 — Reasoning Transparency (GEO-first)
- **ID:** `CORE-EEAT-Ept08` · **Standard:** "We chose A over B because..." with tradeoffs
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Explicit cause-effect and tradeoffs.
- **Partial (5):** Some reasoning.
- **Fail (0):** Conclusions without reasoning.

### Ept09 — Cross-domain Integration (Dual)
- **ID:** `CORE-EEAT-Ept09` · **Standard:** Connects knowledge across fields
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Cross-domain knowledge generating new perspectives.
- **Partial (5):** Some.
- **Fail (0):** Single domain.

### Ept10 — Editorial Process (SEO-first)
- **ID:** `CORE-EEAT-Ept10` · **Standard:** "Reviewed by" or "Fact-checked by" labels
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** "Reviewed by" or "Fact-checked by" labels visible.
- **Partial (5):** Review but no labels.
- **Fail (0):** None.


## A — Authority

### A01 — Backlink Profile (SEO-first)
- **ID:** `CORE-EEAT-A01` · **Standard:** Cited by authoritative sites (.edu, .gov, leaders)
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Cited by authoritative sites.
- **Partial (5):** Some backlinks.
- **Fail (0):** None notable.

### A02 — Media Mentions (SEO-first)
- **ID:** `CORE-EEAT-A02` · **Standard:** "Featured in" with media logos
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** "Featured in" with media logos.
- **Partial (5):** Minor mentions.
- **Fail (0):** None.

### A03 — Industry Awards (SEO-first)
- **ID:** `CORE-EEAT-A03` · **Standard:** Displays relevant industry awards or recognition
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Relevant industry awards.
- **Partial (5):** Weakly relevant.
- **Fail (0):** None.

### A04 — Publishing Record (SEO-first)
- **ID:** `CORE-EEAT-A04` · **Standard:** Conference talks, publications, patents
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Conference talks, publications, patents.
- **Partial (5):** Some.
- **Fail (0):** None.

### A05 — Brand Recognition (Dual)
- **ID:** `CORE-EEAT-A05` · **Standard:** Brand has search volume
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Brand has search volume.
- **Partial (5):** Some awareness.
- **Fail (0):** Unknown.

### A06 — Social Proof (SEO-first)
- **ID:** `CORE-EEAT-A06` · **Standard:** Authentic user testimonials with real details
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Authentic reviews with real details.
- **Partial (5):** Uncertain credibility.
- **Fail (0):** None.

### A07 — Knowledge Graph Presence (Dual)
- **ID:** `CORE-EEAT-A07` · **Standard:** Has Wikipedia entry or Google Knowledge Panel
- **Applicability:** Conditional — applies only when knowledge-graph presence is material to the audit objective; otherwise `na` with reason
- **Pass (10):** Wikipedia entry or Knowledge Panel.
- **Partial (5):** Partially indexed.
- **Fail (0):** Not in any.

### A08 — Entity Consistency (GEO-first)
- **ID:** `CORE-EEAT-A08` · **Standard:** Brand/author info consistent across the web
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Brand/author consistent across web.
- **Partial (5):** Mostly consistent.
- **Fail (0):** Contradictions.

### A09 — Partnership Signals (SEO-first)
- **ID:** `CORE-EEAT-A09` · **Standard:** Shows partnerships with authoritative organizations
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Partnerships with authoritative orgs.
- **Partial (5):** Some signals.
- **Fail (0):** None.

### A10 — Community Standing (SEO-first)
- **ID:** `CORE-EEAT-A10` · **Standard:** Active and influential in professional communities
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Active and influential in communities.
- **Partial (5):** Some participation.
- **Fail (0):** None.


## T — Trust

### T01 — Legal Compliance (SEO-first)
- **ID:** `CORE-EEAT-T01` · **Standard:** Privacy Policy + Terms of Service present
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Privacy Policy + TOS present + bonus (Cookie, GDPR).
- **Partial (5):** Required only.
- **Fail (0):** Missing required.

### T02 — Contact Transparency (SEO-first)
- **ID:** `CORE-EEAT-T02` · **Standard:** Physical address or ≥2 contact methods
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Physical address or ≥2 contact methods.
- **Partial (5):** Email only.
- **Fail (0):** None.

### T03 — Security Standards (SEO-first)
- **ID:** `CORE-EEAT-T03` · **Standard:** Site-wide HTTPS, no security warnings
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Site-wide HTTPS; no warnings.
- **Partial (5):** Some pages insecure.
- **Fail (0):** HTTP.

### T04 — Disclosure Statements (Dual) — **VETO**
- **ID:** `CORE-EEAT-T04` · **Standard:** Material connections are clearly disclosed where present (conditional veto)
- **Applicability:** Conditional — applies only when a material connection, paid placement, or affiliate relationship exists; otherwise `na` with reason
- **Pass (10):** Every in-scope material connection is clearly and conspicuously disclosed in context.
- **Partial (5):** Disclosure is present and understandable but has a remediable contextual weakness that does not materially hide the relationship.
- **Fail (0):** A material connection exists and the required relationship is undisclosed or materially obscured → **Veto triggered**.
- **N/A:** No material connection or paid relationship exists; record the reason. Do not score Partial merely because the control is inapplicable.

### T05 — Editorial Policy (SEO-first)
- **ID:** `CORE-EEAT-T05` · **Standard:** Content standards and review process published
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Content standards and review process published.
- **Partial (5):** Some guidelines.
- **Fail (0):** None.

### T06 — Correction & Update Policy (Dual)
- **ID:** `CORE-EEAT-T06` · **Standard:** Has corrections page or changelog
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Corrections page, update principles, revision history.
- **Partial (5):** Update dates but no formal mechanism.
- **Fail (0):** None.

### T07 — Ad Experience (SEO-first)
- **ID:** `CORE-EEAT-T07` · **Standard:** Ads <30% of page; no intrusive popups
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Ads <30% of page; no intrusive popups.
- **Partial (5):** 30–50%.
- **Fail (0):** >50% or deceptive.

### T08 — Risk Disclaimers (Dual)
- **ID:** `CORE-EEAT-T08` · **Standard:** YMYL topics have necessary disclaimers
- **Applicability:** Conditional — applies only when the artifact makes YMYL or other material-risk claims; otherwise `na` with reason
- **Pass (10):** YMYL topics have disclaimers.
- **Partial (5):** Some coverage.
- **Fail (0):** YMYL with no disclaimers.

### T09 — Review Authenticity (Dual)
- **ID:** `CORE-EEAT-T09` · **Standard:** Reviews show authenticity signals
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Reviews show authenticity signals.
- **Partial (5):** Uncertain.
- **Fail (0):** Obviously fake or absent.

### T10 — Customer Support (SEO-first)
- **ID:** `CORE-EEAT-T10` · **Standard:** Clear return policy, complaint channels, response SLA
- **Applicability:** Always applicable (never `na`)
- **Pass (10):** Clear return policy, complaint channels, response SLA.
- **Partial (5):** Unclear.
- **Fail (0):** None.


### T04 scope note

Assess the applicable market and relationship. In the U.S., FTC endorsement guidance centers on disclosure of material connections in a clear and conspicuous manner; other markets may impose different requirements. This rubric is not legal advice. Judge the rendered experience in context:

- The disclosure is understandable to the intended audience and identifies the material nature of the relationship.
- It is prominent, unavoidable, and proximate enough that a reasonable user encounters it before relying on the endorsement or taking the commercial action.
- Contrast, size, placement, language, device, format, and repetition are assessed together; there is no universal viewport, font-size, or exact-word safe harbor.
- A hidden, ambiguous, or materially separated disclosure does not cure the endorsement.

Human disclosure and link-markup hygiene are separate controls. `rel="sponsored"` or `rel="nofollow"` may matter for search-engine link treatment, but their presence does not replace human disclosure and their absence alone does not trigger this veto.

### Evidence that usually needs more than the article body

Most Authority items (A01-A10) and several Trust items (T01-T03, T05-T07, T10) need site- or organization-level evidence (about/author pages, policy pages, contact page, backlink and brand-search data, web mentions). When auditing a pasted draft or a single page without that context, these items are `unknown` (they are unconditional, so never `na`). Fetch the site pages, use a connected SEO data source, or ask the user for the site URL to resolve them.

---
## AI Engine Citation Preferences

### Engine-Specific Priorities

| Engine | Citation Style | Priority Items |
|--------|---------------|----------------|
| Google AI Overview | Snippet extraction from paragraphs, lists, tables, FAQs | C02, O03, O05, C09 |
| ChatGPT Browse | Conversational with links | C02, R01, R02, E01 |
| Perplexity AI | Multi-source synthesis + inline citations | E01, R03, R05, Ept05 |
| Claude | Precision-first with nuanced arguments | R04, Ept08, Exp10, R03 |

### Top 6 GEO-First Priority Items

| Rank | ID | Name | Why It Matters |
|------|----|------|----------------|
| 1 | C02 | Direct Answer | All engines extract from first paragraph |
| 2 | C09 | FAQ Coverage | FAQ structure directly matches user follow-ups |
| 3 | O03 | Data Tables | Comparison data is most extractable format |
| 4 | O05 | Schema Markup | JSON-LD helps AI understand content type |
| 5 | E01 | Original Data | AI prefers citing exclusive sources |
| 6 | O02 | Summary Box | Key Takeaways often first choice for AI summary |

---

## Schema by Content Type

| Content Type | Required Schema | Conditional Schema |
|-------------|----------------|-------------------|
| Blog (guides) | Article, Breadcrumb | FAQ, HowTo |
| Blog (tools) | Article, Breadcrumb | FAQ, Review |
| Blog (insights) | Article, Breadcrumb | FAQ |
| Alternative | WebPage (or ItemList), Breadcrumb, FAQ | — |
| Best-of | ItemList, Breadcrumb, FAQ | Review/AggregateRating per tool *(only with genuine first-party reviews — see note)* |
| Use-case | WebPage, Breadcrumb, FAQ | — |
| FAQ | FAQPage, Breadcrumb | — |
| Landing | SoftwareApplication, Breadcrumb, FAQ | WebPage |
| Testimonial | Review, Breadcrumb | FAQ, Person |

> **Schema.org has no "Comparison" type.** A comparison/"X alternative" page is marked up as
> `WebPage` (or `ItemList` when it's a ranked set), plus `Breadcrumb` and `FAQPage`.
>
> **`Review` / `AggregateRating` only with real, first-party review content.** Adding self-serving
> `aggregateRating` to a page that has no genuine on-page reviews — or marking up ratings the
> publisher assigned to its own product — is structured-data spam under Google's review-snippet
> policy and can trigger a manual action. Never fabricate ratings to win a rich result.

---

## Content Type Decision Tree

```
What is the primary goal?
├── Teach users how to do something         → Blog (guides)
├── Your product vs one competitor           → Alternative
├── Objective comparison of 3+ products      → Best-of
├── Show product fits a persona              → Use-case
├── Show verified customer results           → Testimonial
├── Answer common questions                  → FAQ
├── Describe product features                → Landing
└── Share industry insights or trends        → Blog (insights)
```

This tree names page types. The scoring profile must still be exactly one of the nine profiles in [scoring-rules.md](scoring-rules.md): `product-review`, `how-to-guide`, `comparison`, `landing-page`, `blog-post`, `faq-page`, `alternative`, `best-of`, `testimonial`. If a page type maps to more than one profile (for example a use-case page), ask one blocking question; never pick the profile that scores highest.

---

## Calibration Examples

Calibration examples for the most subjective CORE items. Use these to anchor scoring consistency. EEAT items are excluded here as they tend to be more clear-cut.

### C — Contextual Clarity

**C05 (Topic Scope)** — Does the content explicitly state what is and isn't covered?

- **Pass**: "This guide covers on-page SEO for WordPress sites running WooCommerce. It does not cover technical server configuration, JavaScript-rendered SPAs, or paid search campaigns." Clear boundaries that set reader expectations and prevent scope creep.
- **Partial**: "We'll look at the main SEO factors for your website." Implies some boundary but never states what is excluded; a reader might expect technical SEO or paid search content.
- **Fail**: Article titled "Complete SEO Guide" that covers only title tags and meta descriptions with no mention of the limited scope. Reader expectation is violated.

**C07 (Semantic Coherence)** — Does the content flow logically between paragraphs?

- **Pass**: Article on database indexing moves from "what indexes are" to "how B-tree indexes work" to "when to add indexes" to "common indexing mistakes," with each section building on the previous. Transition sentences connect ideas explicitly.
- **Partial**: Article covers the same topics but jumps from B-tree internals to a marketing anecdote about database costs, then returns to technical content. The detour is brief but breaks the logical chain.
- **Fail**: Article alternates between beginner explanations and advanced query optimization with no transitions. A paragraph about "what is SQL" is followed by EXPLAIN ANALYZE output with no bridging context.

**C08 (Use Case Mapping)** — Does the content provide a decision framework for when to choose A vs B?

- **Pass**: "Use Redis for session caching and rate limiting where sub-millisecond latency matters and data loss on restart is acceptable. Use PostgreSQL for transactional data requiring ACID guarantees. Use both together when your application needs fast reads with durable writes." Explicit scenarios with selection criteria.
- **Partial**: "Redis is fast and PostgreSQL is reliable. Choose based on your needs." Mentions both options but provides no concrete selection criteria or scenarios.
- **Fail**: Article compares Redis and PostgreSQL features in a table but never states when to choose one over the other. The reader is left to infer applicability.

### O — Organization

**O04 (List Formatting)** — Are parallel items presented as bullet or numbered lists?

- **Pass**: Article on migration strategies presents the 5 steps as a numbered list, each with a bold label and one-sentence description. Comparison of 4 hosting providers uses a consistent bullet format with the same attributes for each.
- **Partial**: Three migration steps are in a numbered list, but two additional steps are buried in a prose paragraph. The reader must parse narrative text to find them.
- **Fail**: Seven distinct recommendations are written as a single run-on paragraph with semicolons separating them. No lists appear in a 2,000-word article despite multiple sequences of parallel items.

**O09 (Information Density)** — Is the content free of filler with consistent terminology?

- **Pass**: Every sentence either introduces a fact, provides evidence, or advances the argument. The term "conversion rate" is used consistently (never alternating with "conversion ratio" or "CR" without definition). No throat-clearing phrases like "It is important to note that."
- **Partial**: Content is mostly dense but includes a 150-word introductory paragraph restating what the reader already knows ("In today's digital landscape, SEO is more important than ever..."). Core terminology is consistent except for one section that switches from "bounce rate" to "exit rate" without clarifying the difference.
- **Fail**: Article pads sections with generic filler ("As we all know, content is king") and uses "CTR," "click-through rate," and "click rate" interchangeably across sections. Approximately 30% of the word count adds no new information.

### R — Referenceability

**R03 (Source Hierarchy)** — Are primary sources prioritized with sufficient Tier 1-2 sourcing?

- **Pass**: Article on search algorithm changes cites Google's official Search Central blog post (Tier 1), a peer-reviewed information retrieval paper (Tier 1), and Ahrefs' 11-million-URL study (Tier 2). Secondary commentary from industry blogs is clearly labeled as interpretation.
- **Partial**: Article cites one Google documentation page but primarily relies on screenshots from unnamed Twitter threads and a single blog post from a mid-tier SEO site. No peer-reviewed or primary research sources.
- **Fail**: All claims reference "experts say" or "studies show" without naming any source. The only link is to another article on the same site that also lacks primary sources.

**R05 (Methodology Transparency)** — Are sample size, steps, and criteria documented?

- **Pass**: "We analyzed 1,200 product pages across 45 e-commerce sites between January and March 2025. Pages were selected by filtering for >1,000 monthly organic sessions. We measured Core Web Vitals using the CrUX API and correlated LCP scores with conversion rates using Pearson's r." Reproducible by another researcher.
- **Partial**: "We looked at several hundred pages and found that faster sites convert better." States a finding but omits sample size, selection criteria, time period, and measurement method.
- **Fail**: "Our research proves that page speed impacts conversions." No methodology of any kind. The word "research" is used but nothing about the process is documented.

### E — Exclusivity

**E04 (Contrarian View)** — Does the content challenge consensus with evidence?

- **Pass**: "Contrary to the 'always convert everything to WebP' advice, AVIF now beats WebP on compression for photographic content, and a WebP-only pipeline drops the `<picture>` fallback path. Back a contrarian claim like this with *your own, real* evidence — e.g. a sampled WebP-vs-AVIF file-size comparison on your actual images, and your CDN logs for the browsers that regressed — and cite real sources. The Pass bar is specific, first-party, verifiable evidence; do not invent statistics or citations to fill it." *(The bracketed figures any model writes here MUST be measured, never fabricated.)*
- **Partial**: "Some people disagree with always using WebP, and there may be compatibility issues to consider." Acknowledges a different viewpoint exists but provides no evidence, data, or specific scenarios.
- **Fail**: No alternative viewpoints are presented. The article treats WebP adoption as universally beneficial without acknowledging any tradeoffs, edge cases, or dissenting perspectives.

**E06 (Gap Filling)** — Does the content cover questions that competitors miss?

- **Pass**: Competitor analysis shows the top 5 ranking articles on "Kubernetes autoscaling" all cover Horizontal Pod Autoscaler. This article additionally covers Vertical Pod Autoscaler, KEDA event-driven scaling, and cluster autoscaler interaction patterns — topics absent from competing content. Includes a decision matrix for choosing between scaling approaches.
- **Partial**: Article covers one subtopic (KEDA) that competitors miss, but the coverage is a single paragraph without enough depth to be useful as a standalone reference.
- **Fail**: Article covers the exact same subtopics as the top 5 competing articles with no additional angles, edge cases, or niche questions addressed.

**E09 (Synthesis Value)** — Does the content combine cross-domain knowledge to produce new insights?

- **Pass**: Article on SaaS pricing combines behavioral economics research (anchoring effect, loss aversion) with B2B sales cycle data and A/B test results from 3 SaaS companies to propose a pricing page framework. The intersection of psychology, sales data, and UX testing produces an insight none of the individual domains would yield alone.
- **Partial**: Article mentions that "psychology plays a role in pricing" and references one anchoring study, but does not synthesize it with domain-specific data or produce a novel framework. The cross-domain mention is surface-level.
- **Fail**: Article discusses SaaS pricing purely from a feature-comparison perspective. No knowledge from adjacent fields (psychology, economics, design) is incorporated.
