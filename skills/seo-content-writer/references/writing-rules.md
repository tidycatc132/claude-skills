# Writing rules

These rules make each passage quotable by an answer engine and still pleasant to read top to bottom. They apply to every page type; `format-rules.md` adds the type-specific ones.

## Page structure and headings

- Phrase every H2 and H3 as the question a person would ask. "Water Heater Types" becomes "Which type of water heater lasts longest?". Exceptions: `Key Takeaways`, `Frequently Asked Questions`, `Sources`, and numbered H3s for how-to steps or listicle items.
- One sub-question per heading, with its own self-contained answer. Never answer a sub-question inside a paragraph about something else.
- Cover the how much, how often, why and what if variants, not only what and how.
- Add a question heading of your own (beyond the brief's) only when you can answer it from the brief, the client files or a cited source. A question whose answer would be only a flag is cut from the page and listed in `handoff.md` as a suggested addition.
- Put the key claim of the page in the first paragraph under the H1. The most important answer is never in the middle of the page.
- Split a section that covers two topics. A section longer than about 300 words usually needs H3s.
- The CTA section is also a question heading, for example "How do I book a descaling visit in Portland?".

## Writing each section (passage rules)

- **Answer first.** The first sentence under every heading is a direct, complete answer that would make sense quoted alone. Then support it. Never build up to the answer.
  - Wrong: "It depends on several factors." / "Let's look at what affects lifespan."
  - Right: "A tankless water heater lasts more than 20 years, according to the U.S. Department of Energy."
- **The first sentence carries the answer itself**, matched to the question type:
  - how much / how long / how often: the figure or interval ("Replacing a tankless water heater in Portland starts at $3,850 installed, according to Harbor & Pine's published pricing.")
  - what are the signs / types / causes: the items themselves, named in the sentence ("A failing tankless water heater shows lukewarm water, error codes on the display and rumbling from the heat exchanger.")
  - why: the cause; what if: the outcome.
  - decision and yes/no questions (is it worth it, should I, do I need, can I, does X): the first word is the verdict for the typical reader (Yes, No, Usually, Rarely, Repair, Replace, or the option chosen), then the heading's subject named in full, then the deciding condition, all in the same sentence ("No, a tankless water heater on Portland city water does not need a water softener, because Bull Run water is very soft", not "Usually not, because Portland city water is very soft").
  - how do I / how can I: the action itself, as an imperative or a plain statement, with the brand, service or route named ("Book a tankless water heater descaling with Harbor & Pine by calling (503) 555-0142"). "No, a tankless water heater rarely pays off before a move in 5 years, because the $5,400 switch costs more than 5 years of energy savings recover." Not "It is hard to justify", not a restatement of the facts without a verdict, and never a conditional fragment such as "Only if..." or "It depends on..."; put the condition after the verdict.
  If you do not have the figure, state the answer you can support and flag the figure after it; never open with "it depends", "several factors" or "can cost" without the amount.
- **Restate the subject** in the first sentence of every section, even if it feels repetitive to someone reading the whole page.
- **2-4 sentences per paragraph.**
- **Isolation test.** After each section, read it as if nothing else on the page existed. If it relies on an earlier paragraph to make sense, rewrite it.
- **Critical facts live in body text**, never only in image alt text, captions or footnotes.
- **Tables for comparisons.** Any time there are 3 or more comparable items or data points, add a table. Name the entities in the header row and restate the entity in each row's first cell.
- **Yes/no questions** open with the answer and the reason in one sentence: "Yes, a tankless water heater needs descaling every one to two years because mineral scale builds on the heat exchanger." Never a bare "Yes."

## Entity clarity

- Search the draft for it, this, that, these, those, they, such, the former, the latter. For each, delete everything before it in the paragraph; if the sentence no longer says what it refers to, replace the pronoun with the name.
- No paragraph, list item or table row starts with a pronoun. Restate the full entity name there.
- One name per entity. Do not alternate "Aegis Pro 5", "the Pro 5" and "the new model". Honor names the brief or `style.md` bans.
- In comparisons, name both entities in every sentence that states a comparative fact: "A tankless water heater lasts about twice as long as a tank water heater", not "It lasts about twice as long."
- Formal terms: spell out once with the abbreviation, "Uniform Energy Factor (UEF)", then use the abbreviation, never "the rating" or "this standard".

## Evidence, quotes and sources

- At least one concrete figure per major section: a percentage, dollar amount, duration, quantity or measurement, in place of "significantly", "much faster" or "a lot".
- Attribute every claim to a named, checkable source in the sentence: "according to the U.S. Department of Energy", "Harbor & Pine's 2025 service records show". Ban "studies show", "experts say", "research suggests", "many people believe".
- Attribute a figure every time it appears, not only the first time: Key Takeaways bullets, table cells, the FAQ and later sections each name the source in the same sentence or cell, even as a short tag ("starts at $3,850 installed (Harbor & Pine pricing)"). A passage lifted out of the page must still say where its number came from.
- Use real quotations from the brief verbatim, in quotation marks, with name, role and context. Do not paraphrase an approved quote into the page's own voice, and never write a quote nobody said.
- Copy numbers exactly as the source states them, including the qualifier ("more than 20 years", "around 3 to 8 ppm"). Never round up, combine two sources into a new number, or strengthen "some" into "most".
- Derived comparisons and conclusions ("roughly twice as long", "pays for itself over the unit's life", "saves $X a year") are new claims. State the two sourced figures side by side instead ("more than 20 years versus 10 to 15 years"), or show the arithmetic from sourced figures ("$5,400 minus $3,850 is $1,550"). A payback, savings or ROI claim needs its own source or a flag.
- Never fabricate a statistic, quote, source, credential, price or URL. When a section needs evidence you do not have, write `[NEEDS SOURCE: <what figure, from what kind of source>]`.
- **What needs a source and what does not.** Figures (percentages, dollar amounts, durations, counts, rates, limits), quotes, rankings, and claims about a named organization need a source or a flag. General explanatory knowledge that any licensed practitioner in the field would state (how something works, common symptoms, the usual steps, what a term means) does not; write it plainly, without numbers you were not given.
- **A flag never replaces the answer.** Write the complete answer sentence first from what you know, then put the flag where the missing figure would strengthen it: "A failing tankless water heater usually shows lukewarm water, error codes on the display or rumbling from the heat exchanger. [NEEDS SOURCE: how many years before failure these signs typically appear]"
- **No hypothetical or illustrative figures.** Do not invent a worked example ("say your home is worth $400,000 and the lender allows 85%"). Build examples only from sourced or client-supplied figures; otherwise explain the calculation in words and flag the figures. This applies doubly on YMYL pages.
- List every source in `## Sources` at the end, with its title, publisher and URL when known.
- If the brief says the page ranks outside the top 3, add more evidence per section than the minimum, and say so in `handoff.md`.

## Language and keywords

- Use the target phrase in the H1, its terms in the first 100 words after the H1, and in a heading only where it reads naturally. Do not count density.
- A question-form keyword ("how long does a tankless water heater last") is carried by the H1. In body text use its terms in a natural sentence ("A tankless water heater lasts more than 20 years"); never paste the question into a sentence ("homeowners asking how long does a tankless water heater last").
- Never repeat the exact keyword mechanically. Use the varied, specific language an expert uses: product names, numbers, sub-concepts, the entities from the brief.
- Work the brief's entities into the prose where they belong, so the page reads like someone who knows the trade wrote it.
- Plain, fluent sentences. Short words over jargon; define a term the first time it appears.
- Authoritative tone is not evidence. A confident sentence without a specific is a weak sentence.

## Author, experience and trust

- Visible byline under the H1: `By [Name](bio-url), credentials`. Credentials are demonstrable (license number, certification, years in the field), never "expert team".
- At least one first-hand experience marker where the client has one: a number from real work, a named case, a mistake seen in the field. Write it as the client's experience ("we", or the author's name) and keep its details exact.
- Place a first-hand case inside the section it supports, as the paragraph after that section's answer. Do not give a case or story its own heading; every heading is a question, and a story does not answer one.
- YMYL pages (health, finance, legal, safety): credentials, sourcing and first-hand experience are the most important part of the draft. Missing ones are flags; `handoff.md` routes the page to the client's compliance or expert reviewer, and lists required disclosures the brief did not supply.

## Internal links

- Place every pillar, sub-topic and sibling link the brief lists, using the planned anchor text or a close, descriptive variant that names the destination topic.
- Never "click here", "learn more", "read more" or a bare URL as anchor text.
- Each link sits in a sentence that says why the destination is relevant: "Our [tankless water heater installation](/tankless-water-heater-installation/) page explains venting and gas line changes."
- Link only to URLs you were given. A needed but unknown URL is `[NEEDS INPUT: URL for ...]`.
