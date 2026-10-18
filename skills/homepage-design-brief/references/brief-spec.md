# Brief spec

The brief is `design/<slug>/<slug>-homepage-design-brief.md`, at most 160 lines. `scripts/check_design_brief.py` checks everything marked (checked).

## Top of the file

```
Client: <client name> · Page: <path of the edited article.md> · Built: <YYYY-MM-DD>
Content review: confirmed (<who>, <date>)

# Homepage Design Brief: <client name>
```

(checked) The first line is exactly that shape. The second line is `Content review: confirmed (<who>, <date>)` when the user said the copy passed editorial review (use the name and date they gave; write `not given` for a missing one), otherwise `Content review: not confirmed`.

## Sections

(checked) Exactly these `##` headings, in this order, and no others: `## Goals`, `## Audience`, `## Brand Cues`, `## Design References`, `## Section Map`, `## Imagery`, `## Must-Haves`, `## Do-Nots`, `## Open Questions`, `## Sources`.

### Evidence tags

(checked) Every `-` bullet in Goals, Audience, Brand Cues, Imagery, Must-Haves and Do-Nots ends with one or more tags naming where it comes from, or starts with `GAP:` or `Recommended:`.

| Tag | Source |
| --- | --- |
| `[article]` | the edited homepage |
| `[kit: brand.md]` (or `voice.md`, `style.md`, `audience.md`, `compliance.md`) | the client reference kit file |
| `[context]` | `kickoff/<slug>/<slug>-context.md` |
| `[blueprint]` | `kickoff/<slug>/<slug>-blueprint-input-package.md`; add the call timestamp when it gives one, `[blueprint 00:05:10]` |
| `[user]` | something the user said in this conversation |

`GAP:` names a fact the designer needs that no file has, and who can supply it; the same gap is also an open question. `Recommended:` marks a design default of yours that no source states, for example `Recommended: one primary button style used in Hero and Final CTA`. Use it for layout and pattern advice only, never for a fact about the client. A tag vouches for the whole bullet: when a bullet would join a sourced fact to a design idea of yours (the client wants the phone visible; you suggest a sticky tap-to-call bar), split it into a tagged bullet and a `Recommended:` bullet. A tag also means the source says it about the page or its look. Carrying a rule from another context into the design (a copy rule like no fear selling becoming no countdown timers or alarm colours) is your inference: write it as `Recommended:` and name the rule it follows, for example `Recommended: no countdowns or alarm colours, following voice.md's no-fear-selling rule`.

### Goals

3 to 5 bullets: what the homepage must make a visitor understand and do (the conversion action and the route to it), and the business goal behind it. From the context's Goals and Conversion and the blueprint package's Goals and Success Measures.

### Audience

2 to 4 bullets: who lands on the page, on what device when a source says so, and what they need to see first. From the kit's `audience.md`, then the context, then the blueprint package's Audiences.

### Brand Cues

Colours, logo, type feel, tone the design must carry, and approved claims that need visual weight. Each from a source; a visual fact no source states (logo files, colour values, fonts) is a `GAP:` line. With no client reference kit, say so in a `GAP:` line here and take the voice and look-and-feel cues from the context and blueprint package.

### Design References

Only websites the client named as ones they like, as a table:

```
| Reference | What the client likes | Source |
| --- | --- | --- |
| Larkspur Bakery (larkspurbakery.com) | hand-drawn icons, one bold colour, short pages | [blueprint 00:05:10] |
```

(checked) Each reference name must appear in the source files. Never list a competitor, a site the AM or anyone at the agency suggested, or a site you found yourself. A site the client said they dislike goes in Do-Nots. When the client named none, write one line: `GAP: the client named no reference sites; ask at the next client touchpoint.`

### Section Map

(checked) One row per section of the edited page, in page order, numbered from 1. With the writer's markers (`<!-- section: Hero -->`, `<!-- section: Why Us -->`, `<!-- section: Services Overview -->`, `<!-- section: Proof -->`, `<!-- section: About Snapshot -->`, `<!-- section: Service Area -->`, `<!-- section: Process -->`, `<!-- section: FAQ -->` when the page has one, `<!-- section: Final CTA -->`), the Section cell is the marker's name exactly. Without markers, one row per H1 and H2, named after the homepage role it plays.

```
| # | Section | Purpose | Layout idea | Content source |
| --- | --- | --- | --- | --- |
| 1 | Hero | Say what, for whom, where; get the booking click | Full-width photo, H1 and one sentence left, primary button and phone right | article.md > Hero |
```

- Purpose: what the section must achieve for the visitor, in one line.
- Layout idea: structure only (columns, cards, list or table, photo placement, button placement, what sits above the fold, mobile order when it matters). No wording: never write a headline, tagline, button label or sentence; the page already has them.
- Content source: `article.md > <Section>`, plus the open flag numbers or short names the section waits on (`article.md > Proof; waits on #2, #3`).

### Imagery

What photography or illustration each part of the page needs, the subjects, and the rules from sources (a client's "no stock photos", a compliance rule about what photos must show). Name planned shoots or assets a source mentions. A missing asset (photos, team headshots, logo files) is a `GAP:` line.

### Must-Haves

Things the design must show because a source says so: the conversion action the client chose, approved proof, contact details the files give, client requests. Each sourced. Good practice no source states (the call button reachable on every screen size, a sticky header, one button style) is a `Recommended:` bullet, never a tagged one.

### Do-Nots

Things the client or the kit rules out: looks the client rejected (including a competitor's site they dislike, described by what they dislike), banned imagery, prohibited claims that must not get visual weight. Each sourced.

### Open Questions

A numbered list. In this order:

1. When the content review is not confirmed: `Has the homepage copy passed editorial review? This brief maps the draft as it stands.` (checked: it is item 1)
2. (checked) Every open flag on the page (`[NEEDS INPUT: ...]`, `[CLIENT INPUT NEEDED #n: ...]`, `[NEEDS SOURCE: ...]`), copied verbatim, once, with the section it sits in and who answers it, for example `[NEEDS INPUT: office hours] (Final CTA). Client.` A numbered slot that appears in several sections is one question listing every section.
3. Every `GAP:` in the brief, as a question with who answers it.
4. A missing input file (no client reference kit, no blueprint package), with what it would have supplied.

### Sources

One line per file read, with its path.

## Quoted wording

(checked) Text in double quotes of four or more words must appear word for word in the article or a source file. Quote the client to justify a cue (for example the words they used about a site they dislike); never put proposed copy in quotes.

## Wireframe

`design/<slug>/<slug>-homepage-wireframe.html`, written only by `scripts/make_wireframe.py` and only when the user asks for a wireframe, a mockup or HTML-to-Figma. (checked with `--wireframe`) One `data-section` per page section in page order; inline CSS; no scripts, images, fonts, external links or `src`.
