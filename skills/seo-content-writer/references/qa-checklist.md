# Pre-publish QA

Two layers. The script checks what can be checked mechanically; you check the rest by reading. The script writes `qa/<url-slug>/qa_report.md`, a working file; the judgment checks are fixed in the draft and not recorded.

## Scripted checks (`scripts/check_draft.py`)

| Check | FAIL means | Fix |
| --- | --- | --- |
| One H1 | 0 or 2+ H1s | One `# ` line only |
| Named author byline | No `By ` line under the H1, or a generic one | Real name and credentials, or the `[NEEDS INPUT: author ...]` flag |
| H2/H3 phrased as questions | A label heading | Rewrite as the question a person asks |
| 5+ sub-questions under own headings | Fewer than 5 question headings | Build sub-questions (brief-intake.md) |
| First sentence is a direct answer | Opens with a pronoun, a lead-in, or under 5 words | Put the full answer, with its subject named, first |
| First sentence restates the heading's subject (WARN) | Fewer than half the heading's content words appear in the answer's first sentence | Make sure the subject is named; a natural paraphrase of the heading can stay |
| Yes/no questions open with a verdict and the subject | A yes/no answer that does not start with Yes, No, Usually, Rarely, Most..., or that does not name the heading subject in its first 15 words | "No, a tankless water heater on city water does not need ..." (choice questions get a WARN instead) |
| No unattributed claims | "studies show", "experts say"... | Name the source or flag `[NEEDS SOURCE: ...]` |
| A statistic or evidence flag per major section | A question H2 section with no figure | Add a sourced figure or a `[NEEDS SOURCE: ...]` flag |
| Every figure names its source in the same sentence | A sentence, bullet or table row with %, $, a decimal or ppm, or any figure from the brief's evidence ("10 to 15 years"), and no source cue; a source named in the next sentence does not count | Add the source name or a short tag such as "(U.S. Department of Energy)" |
| Sources section for stated figures | Figures but no `## Sources` | Add the list |
| Descriptive anchor text | "click here", "learn more"... | Name the destination topic |
| Every internal link from the brief is placed | A brief link is missing | Place it in a sentence that says why it is relevant |
| Comparison table present | Brief asks for a table, none on the page | Add it |
| FAQ answers are complete statements | Answer under 15 words or bare yes/no | 2-4 sentences with a specific |
| No placeholder text | Unfinished-work markers or filler text | Replace with content or a NEEDS flag |
| Meta title is the H1 plus at most the brand | More than 3 words beyond the H1 and the client name | Use the H1, optionally " | Brand" |
| Metadata table complete, 3-7 key takeaways, summary 3-4 sentences | Field missing or wrong count | Fix the metadata table at the top of `article.md` |
| No mechanical keyword repetition | Exact keyword over the limit | Replace repeats with specific language |

`scripts/selftest_structure.py` checks `make_semantic.py` on small cases; run it after changing that script.

On a homepage (`--page-type homepage`) the byline check is skipped, the per-section statistic is a WARN, and four more checks run; they are listed in `homepage.md`. About, Contact and location pages (`--page-type about`, `contact`, `location`) work the same way, with the checks listed in `client-pages.md`.

WARN items (paragraph length, first sentence vs heading wording, vague intensifiers, keyword placement, numbers not in the brief, meta title vs H1, open flags) are not failures, but read each one and fix it unless it is right as written. "Numbers not in the brief" is the fabrication alarm: every listed number must be a step count, a date, a derived figure you show the arithmetic for, or a value cited in `## Sources`. Otherwise delete it or flag it.

## Judgment checks (read the draft)

1. **Natural reading.** Read the page aloud top to bottom. Does any sentence describe the page, its tone or its sourcing rules instead of the topic? Do the section openers vary, or do they all follow "X does Y because [statistic]"? Is a name or source repeated where a person would say "it", "the firm" or "the study"?
2. **Entity names.** Is each entity called by one name throughout, including the aliases the brief bans?
3. **Claims match sources.** For each number: is the wording as strong as the source and no stronger, and is the source named in the sentence?
4. **Quotes.** Is each quote verbatim from the brief, a client file or a cited source, with name and role? On a homepage, About, Contact or location page, does every client fact keep its file's qualifier ("about 47 reviews" stays "about 47")?
5. **First-hand experience.** Is at least one client experience marker on the page, or a flag asking for one?
6. **Format rules.** Are the `format-rules.md` items for this page type met (table, imperative numbered steps, one-sentence definition with mechanism, specific list differentiators, visible pricing)?
7. **Tables.** Is every set of 3+ comparable items or figures in a table?
8. **Keyword use.** Target phrase in the H1 and first 100 words, otherwise natural language; nothing reads as stuffed.
9. **YMYL.** If the topic is health, finance, legal or safety: are credentials, sources and required disclosures present or flagged, and, with no reviewer named in the client files, is that an open flag in `handoff.md`?
10. **Client rules.** If client reference files exist: banned words absent, product names exact, required disclaimers present.

Fix what fails and rerun the script.
