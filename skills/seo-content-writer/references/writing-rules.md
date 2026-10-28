# Writing rules

These rules make each passage quotable by an answer engine and still pleasant to read top to bottom. They apply to every page type; `format-rules.md` adds the type-specific ones.

## Page structure and headings

- Phrase every H2 and H3 as the question a person would ask. "Water Heater Types" becomes "Which type of water heater lasts longest?". Exceptions: `Key Takeaways`, `Frequently Asked Questions`, `Sources`, and numbered H3s for how-to steps or listicle items.
- One sub-question per heading, with its own self-contained answer. Never answer a sub-question inside a paragraph about something else.
- Cover the how much, how often, why and what if variants, not only what and how.
- Add a question heading of your own (beyond the brief's) only when you can answer it from the brief, the client files or a cited source. A question whose answer would be only a flag is cut from the page.
- Put the key claim of the page in the first paragraph under the H1. The most important answer is never in the middle of the page.
- Split a section that covers two topics, with an H3 per subtopic.
- The CTA section is also a question heading, for example "How do I book a descaling visit in Portland?".

## Writing each section (passage rules)

- **Answer first.** The first sentence under every heading is a direct, complete answer that would make sense quoted alone. Then support it. Never build up to the answer.
  - Wrong: "It depends on several factors." / "Let's look at what affects lifespan."
  - Right: "A tankless water heater lasts more than 20 years, according to the U.S. Department of Energy."
- **Answer in plain words, not by echoing the heading.** Do not open every section with the heading turned into a statement plus "because" plus a statistic ("SEO helps an accounting firm get found by new clients because Google bases local results..."). Write the answer the way an expert would say it, use "because" only for a real cause, and let the supporting figure come in the second sentence when one sentence would carry both.
- **The first sentence carries the answer itself**, matched to the question type:
  - how much / how long / how often: the figure or interval ("Replacing a tankless water heater in Portland starts at $3,850 installed, according to Harbor & Pine's published pricing.")
  - what are the signs / types / causes: the items themselves, named in the sentence ("A failing tankless water heater shows lukewarm water, error codes on the display and rumbling from the heat exchanger.")
  - why: the cause; what if: the outcome.
  - decision and yes/no questions (is it worth it, should I, do I need, can I, does X): the first word is the verdict for the typical reader (Yes, No, Usually, Rarely, Repair, Replace, or the option chosen), then the heading's subject named in full, then the deciding condition, all in the same sentence ("No, a tankless water heater on Portland city water does not need a water softener, because Bull Run water is very soft", not "Usually not, because Portland city water is very soft"). "No, a tankless water heater rarely pays off before a move in 5 years, because the $5,400 switch costs more than 5 years of energy savings recover." Not "It is hard to justify", not a restatement of the facts without a verdict, and never a conditional fragment such as "Only if..." or "It depends on..."; put the condition after the verdict.
  - how do I / how can I: the action itself, as an imperative or a plain statement, with the brand, service or route named ("Book a tankless water heater descaling with Harbor & Pine by calling (503) 555-0142").
  If you do not have the figure, state the answer you can support and flag the figure after it; never open with "it depends", "several factors" or "can cost" without the amount.
- **Name the subject** in the first sentence of every section. After that, write as a person would: pronouns ("it", "they") are fine where the reference is clear. A short name is fine only if the brief's naming table or `style.md` does not ban it ("the firm" for an accounting firm, never "the new model" when the table lists it under "Never call it").
- **2-4 sentences per paragraph.** Vary sentence length; a short sentence after a long one reads naturally.
- **Critical facts live in body text**, never only in image alt text, captions or footnotes.
- **Tables for comparisons.** Any time there are 3 or more comparable items or data points, add a table. Name the entities in the header row; cells are short phrases, not sentences that repeat the row's entity.
- **Yes/no questions** open with the answer and the reason in one sentence: "Yes, a tankless water heater needs descaling every one to two years because mineral scale builds on the heat exchanger." Never a bare "Yes."

## Entity names

- One name per entity. Do not alternate "Aegis Pro 5", "the Pro 5" and "the new model". Honor names the brief or `style.md` bans.
- Formal terms: spell out once with the abbreviation, "Uniform Energy Factor (UEF)", then use the abbreviation, never "the rating" or "this standard".

## Evidence, quotes and sources

- At least one concrete figure per major section: a percentage, dollar amount, duration, quantity or measurement, in place of "significantly", "much faster" or "a lot".
- Attribute every claim to a named, checkable source in the sentence: "according to the U.S. Department of Energy", "Harbor & Pine's 2025 service records show". Ban "studies show", "experts say", "research suggests", "many people believe".
- Quantities written in words ("more than a decade", "twice as long", "half the cost") are figures too, and so is every quantity in a first-hand case: each sentence that carries one names its source or the client ("Harbor & Pine's records show...").
- Attribute a figure every time it appears, not only the first time: Key Takeaways bullets, table cells, the FAQ and later sections each name the source in the same sentence or cell, even as a short tag ("starts at $3,850 installed (Harbor & Pine pricing)"). Within one section, give the source's full name once; later sentences in that section say "the study" or "the survey". Never repeat the full source name for a definition or a non-figure sentence.
- Use real quotations from the brief verbatim, in quotation marks, with name, role and context. Do not paraphrase an approved quote into the page's own voice, and never write a quote nobody said.
- Copy numbers exactly as the source states them, including the qualifier ("more than 20 years", "around 3 to 8 ppm"). Never round up, combine two sources into a new number, or strengthen "some" into "most".
- Derived comparisons and conclusions ("roughly twice as long", "pays for itself over the unit's life", "saves $X a year") are new claims. State the two sourced figures side by side instead ("more than 20 years versus 10 to 15 years"), or show the arithmetic from sourced figures ("$5,400 minus $3,850 is $1,550"). A payback, savings or ROI claim needs its own source or a flag.
- Never fabricate a statistic, quote, source, credential, price or URL. When a section needs evidence you do not have, write `[NEEDS SOURCE: <what figure, from what kind of source>]`.
- **What needs a source and what does not.** Figures (percentages, dollar amounts, durations, counts, rates, limits), quotes, rankings, and claims about a named organization need a source or a flag. General explanatory knowledge that any licensed practitioner in the field would state (how something works, common symptoms, the usual steps, what a term means) does not; write it plainly, without numbers you were not given.
- **A flag never replaces the answer.** Write the complete answer sentence first from what you know, then put the flag where the missing figure would strengthen it: "A failing tankless water heater usually shows lukewarm water, error codes on the display or rumbling from the heat exchanger. [NEEDS SOURCE: how many years before failure these signs typically appear]"
- **No hypothetical or illustrative figures.** Do not invent a worked example ("say your home is worth $400,000 and the lender allows 85%"). Build examples only from sourced or client-supplied figures; otherwise explain the calculation in words and flag the figures. This applies doubly on YMYL pages.
- List every source in `## Sources` at the end, with its title, publisher and URL when known.
- If the brief says the page ranks outside the top 3, add more evidence per section than the minimum.

## Language and keywords

- Use the target phrase in the H1, its terms in the first 100 words after the H1, and in a heading only where it reads naturally. Do not count density.
- A question-form keyword ("how long does a tankless water heater last") is carried by the H1. In body text use its terms in a natural sentence ("A tankless water heater lasts more than 20 years"); never paste the question into a sentence ("homeowners asking how long does a tankless water heater last").
- Never repeat the exact keyword mechanically. Use the varied, specific language an expert uses: product names, numbers, sub-concepts, the entities from the brief.
- Work the brief's entities into the prose where they belong, so the page reads like someone who knows the trade wrote it.
- Plain, fluent sentences. Short words over jargon; define a term the first time it appears.
- Authoritative tone is not evidence. A confident sentence without a specific is a weak sentence.
- **The brief's directions are instructions, never copy.** Notes on tone ("consultative, not alarmist"), framing ("position on value, never price"), order ("formula first, then proof"), or dating ("date-stamp platform claims") are applied in how you write; the page never describes itself, its tone, its sourcing or its own rules. Wrong: "Every claim about a fast-moving AI platform ages quickly, so any platform fact on this page carries the date it was checked." / "The survey's year is worth stating whenever the figure is quoted." Right: give the date or year inline with the fact.
- Natural wording never adds a fact. Do not turn one testimonial into what customers say ("Homeowners describe..."), give a person a role or duty no file states, or widen a claim beyond its source to make a sentence flow.
- A scope limit on a source is stated once, as a plain fact about the data, where the figure first appears ("Hinge surveyed professional services firms in general, not accounting firms alone"). Do not add a caveat sentence after every figure.

## Author, experience and trust

- Visible byline under the H1: `By [Name](bio-url), credentials`. Credentials are demonstrable (license number, certification, years in the field), never "expert team".
- At least one first-hand experience marker where the client has one: a number from real work, a named case, a mistake seen in the field. Write it as the client's experience ("we", or the author's name) and keep its details exact.
- Place a first-hand case inside the section it supports, as the paragraph after that section's answer. Do not give a case or story its own heading; every heading is a question, and a story does not answer one.
- YMYL pages (health, finance, legal, safety): credentials, sourcing and first-hand experience are the most important part of the draft. Missing ones are flags, and so is each required disclosure the brief did not supply; a missing reviewer is an open flag in `handoff.md`.

## Internal links

- Place every pillar, sub-topic and sibling link the brief lists, using the planned anchor text or a close, descriptive variant that names the destination topic.
- Never "click here", "learn more", "read more" or a bare URL as anchor text.
- Each link sits in a sentence that says why the destination is relevant: "Our [tankless water heater installation](/tankless-water-heater-installation/) page explains venting and gas line changes."
- Link only to URLs you were given. A needed but unknown URL is `[NEEDS INPUT: URL for ...]`.
