# Wireframe spec

`design/<slug>/<slug>-<page-type>-wireframe.html`, one per page type section in the brief. `scripts/wireframe.py build` writes every part; nothing here is filled by hand. Read this to know what the files hold, what the build prints, and what to tell Design.

## When

Only when the user asks for template wireframes, an HTML starter for the templates, or files to pull into Figma with an HTML-to-Figma plugin. The brief must pass `ptdb.py check` first: `build` refuses otherwise, writes nothing, and prints the brief's FAIL lines. Fix the brief, run its check to `RESULT: PASS`, then build.

## What each file holds

- A header strip: client, page type, the page the copy came from (the longest page of the type by word count, with the number of pages and its words), the brief's path, and the colours used.
- One `<section>` per Content Map row, in the brief's order. Each carries `data-section="<Section>"`, a label `NN · <Section> · <Appears on>` (with `· CTA` when a clause of the brief's `### CTAs` bullets names that section without saying it has none), and the row's Purpose line.
- The real copy of the longest page, cut by its section markers (about, contact, location), or for pages without markers by the opening (H1 to the first H2) and each H2, matched to the rows by their Content source: `H1` or `opening` takes the opening, `last H2` the closing section, a heading named in the source or the row takes that heading, and a row whose source names a run of sections (`H2 question sections`) takes the H2s between its neighbours. A row whose source names a heading the page does not have gets no copy, never a neighbour's: the build prints `no copy matched its Content source`, and the fix is the brief's Content Map. An H2 no row takes joins the row before it (the build prints it). `## Sources` is left out.
- A row that appears on only some pages (`1 of 2`) and that the longest page lacks takes its copy from the longest page that has it, and says which.
- Repeating blocks are separate components: each H3 (FAQ item), each H2 inside a row that holds several, and each list item.
- Open flags (`[NEEDS INPUT: ...]`) stay in the copy, boxed, so Design leaves room for them.

## Colours

Neutral greys only, unless the page type's `### Brand Reference` gives a tagged colour value (not a `GAP:` line, and not a colour the bullet bans). Each colour is read in its own clause of the bullet (cut at `;` and `,`, quoted words ignored): a clause that bans or retires a colour, or sets a background, never gives one. A colour is used for the role its clause names and nothing else: headings (headings, or the primary colour), body text, and the label of a call-to-action section. A colour whose clause names no role is not used. Fonts stay a plain system sans; the brief's typefaces are for Design.

## Check

`build` ends with `check`, and `python3 <skill-folder>/scripts/wireframe.py check --slug <slug>` runs it alone after anyone edits a file. Per file: sections in the Content Map order, each labelled with its number and name, the source page named, every line of the placed copy present inside its own section, only greys or the Brand Reference's colours, no scripts, images, embeds, fonts or link targets (links in the copy are kept as text). Also: no wireframe for a page type the brief does not have. The homepage wireframe (homepage-design-brief's) is not touched or checked.

## Report to the user

Each file's path, the page its copy came from, any row whose copy came from another page or that has no copy yet, and whether it uses the brief's colours or greys only. Say they are structure and copy for an HTML-to-Figma import, not a design: Design decides the look.
