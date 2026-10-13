# Humanizer / AI-Slop Checks (advisory)

Named anti-patterns that make writing read as machine-generated. Run as the last pass on the audited text. This is a voice/quality check, not an SEO tactic: no ranking effect is claimed.

**How this skill uses it:** a SOFT signal only. Findings may serve as evidence for non-veto items (mainly O09 Information Density, C07 Semantic Coherence, Ept03 Professional Vocabulary, and the Experience items Exp01/Exp08, where generic filler replaces first-hand detail). It never creates a veto; vetoes stay C01, R10, T04. Report the humanizer score separately as a diagnostic and flag the specific lines, not just a number.

## Slop vocabulary

| Word/phrase | Why it's slop |
|---|---|
| utilize, whilst, endeavour | inflated forms of "use", "while", "try" |
| underscore (verb), garner, bolster | thesaurus verbs for "show", "get", "strengthen" |
| transformative, groundbreaking, innovative, commendable, meticulous | empty praise adjectives |
| testament, profound, nestled, renowned | promotional puffery |
| "shed light on", "pave the way for", "a plethora of" | academic AI tells |
| "prior to / subsequent to", "in light of", "in terms of", "the fact that" | wordy connectors → "before/after", "because", "for", "that" |
| "that being said", "with that in mind", "at its core", "this begs the question" | filler transitions |

## Slop patterns

Tell = what to look for. Fix = rewrite with a concrete noun, number, or simple verb.

| # | Pattern | Tell | -pts | Before → After |
|---|---|---|---|---|
| 1 | Significance inflation | "stands as", "marks a pivotal moment", "underscores its importance" | 10 | "a pivotal moment in digital marketing" → "launched its first programmatic campaign in 2019" |
| 2 | Undue-notability claims | media-mention list with no substance | 5 | "featured in Forbes, Inc, and Entrepreneur" → "in a 2024 Forbes interview, argued most brand-awareness spend is wasted" |
| 3 | Shallow -ing analysis | trailing "highlighting / underscoring / ensuring / reflecting" | 8 | "grew 40% YoY, showcasing the team's commitment" → "grew 40% YoY, mostly from one referral loop built in Q2" |
| 4 | Promotional language | "boasts a", "rich" (figurative), "must-visit", "in the heart of" | 8 | "boasts a vibrant team with a commitment to results" → "45 employees; revenue grew 32%" |
| 5 | Vague attribution | "experts argue", "industry reports", "several sources" | 8 | "experts believe AI will transform marketing" → "a 2024 Gartner survey: 67% of CMOs plan more AI spend" |
| 6 | Formulaic "challenges/future" section | "Despite these challenges, continues to…", "Future Outlook" | 10 | "despite challenges, continues to thrive" → "churn hit 8% in Q3; they hired a retention team in October" |
| 7 | Negative parallelism | "not just X, it's Y", "not only…but" | 5 | "not just content, it's a lasting relationship" → "good content gets replies" |
| 8 | Copula avoidance | "serves as", "represents", "features", "offers" for plain "is/has" | 5 | "serves as a valuable resource" → "is a resource; 12K weekly opens" |
| 9 | Rule-of-three filler | forced triples of adjectives, nouns, or clauses | 8 | "keynotes, panels, and networking opportunities" → "talks and panels, plus time to network" |
| 10 | Elegant variation | synonym-cycling one subject (CEO → business leader → company head) | 5 | three labels for one person → name them once |
| 11 | False ranges | "from X to Y" where X/Y aren't on a scale | 5 | "from content to SEO to paid media, the field shifts" → "content, SEO, and paid media are all changing" |
| 12 | Em-dash-as-drama | >1 em dash per ~200 words; dash where a comma/period works | 5 | "this—unlike old methods—allows…" → "this, unlike old methods, allows…" |
| 13 | Sycophancy | "Great question!", "You're absolutely right!" | 8 | delete; answer the question |
| 14 | Collaborative artifacts | "I hope this helps", "Certainly!", "Would you like…" | 10 | delete; it's a deliverable, not a chat turn |
| 15 | Cutoff disclaimers | "As of [date]", "based on available information" | 10 | delete or cite the actual source + date |
| 16 | Excessive hedging | "could potentially possibly", "might have some effect" | 8 | "could potentially have some impact" → "works — here's the data" |
| 17 | Generic positive conclusion | "the future looks bright", "exciting times ahead" | 10 | "the future looks bright for AI" → "they plan to double AI budget next quarter" |
| 18 | Filler phrases | "in order to", "due to the fact that", "at this point in time" | 5 | → "to", "because", "now" |

Style tells worth a quick scan (-2 to -5 each): title-case headings, emoji on headings/bullets, curly quotes, bold on every key term, lists where every item is a bold-header-colon.

## Scoring

Start at 100; subtract per occurrence. The same pattern stacks up to 2x its base penalty. Bands: 90-100 clean · 70-89 minor tells, quick fix · 50-69 obvious AI, real rewrite · <50 full rewrite. Advisory only.

## What good looks like

Opinions (not just reporting) · varied sentence rhythm · concrete names, dates, numbers · simple verbs (is, has, does) · honest uncertainty · first person where it fits.
