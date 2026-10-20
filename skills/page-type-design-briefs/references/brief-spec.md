# Brief spec

`design/<slug>/<slug>-page-type-design-briefs.md`. `ptdb.py scaffold` writes the frame and `ptdb.py check` verifies everything marked (checked). Keep the scaffold's computed lines exactly as written; fill only the `<fill>` parts and add bullets or questions where this spec allows.

## Top

```
Client: <client name> · Built: <YYYY-MM-DD> · Homepage brief: <path, or none>
Homepage direction: <Option X> (<feedback file>)        or        Homepage direction: direction not chosen yet

# Page-Type Design Briefs: <client name>
```

(checked) The direction line matches what the scan read from `feedback/<slug>/`. The latest feedback file that picks an option, or asks a question about the homepage design, decides; a question with no pick, or two different options in one file, counts as not chosen.

## Sections

(checked) `## Page Types`, then one section per page type that has pages, in this order and named exactly: `## Service Pages`, `## Location Pages`, `## About Page`, `## Contact Page`, `## Resource Pages`; then `## Open Questions`, `## Hand-off`, `## Sources`. No section for a type with no pages. The homepage is never a page type here.

`## Page Types` is the table `| Page type | Pages |`, one row per section (checked against the scan).

## Inside each page-type section

(checked) Exactly these `###` subsections, in this order.

### Pages

One bullet per page file of this type, as the scaffold lists them (checked: every file exists, every page of the type is listed, none of another type).

### Content Map

`| # | Section | Purpose | Appears on | Content source |`, one row per section the template must hold, numbered from 1.

- Pages with section markers (about, contact, location): the scaffold fills Section, Appears on and Content source from the markers in page order (checked). Write only the Purpose.
- Pages without markers (service, resource): write the rows. Read the pages' headings side by side and name each section by the job it does across the pages (for example `Opening answer`, `Key Takeaways`, `Question sections`, `FAQ`, `Booking`), in page order. Content source names where it sits (`article.md > H1 and opening`, `article.md > Frequently Asked Questions`).
- Purpose: one line on what the section does for the visitor. No headline or button wording.
- Appears on: `all`, or `k of n` where n is the number of pages of this type (checked).

### Repeating Blocks

Bullets naming the blocks every page of the type repeats with the same job (the booking section, the Key Takeaways list, the credentials strip), and blocks that repeat inside one page (each question section, each service bullet, each FAQ item).

### Content Length

The scaffold writes two computed lines: `Words: <min> to <max> (<n> pages)` and `H2 sections: <min> to <max>` (checked: kept exactly). Below them, bullets on what varies in length (the number of question sections, FAQ items, services listed, team members named) and what the template must hold at the short and the long end. Say it in content terms ("holds from 3 to 6 question sections without empty space"), not as a layout.

### CTAs

Where the calls to action sit on these pages (top, after a given section, the closing section), which route each one uses (the booking link, the phone), taken from the pages, and which CTA treatment from the homepage brief carries over when it names one, tagged `[homepage brief]`. Placement only; no button wording beyond what the pages already say.

### Brand Reference

The brand rules this template must respect, each from a source:

| Tag | Source |
| --- | --- |
| `[kit: brand.md]` (or `style.md`, `voice.md`, `audience.md`, `compliance.md`) | the client reference kit file (checked: it exists) |
| `[homepage brief]` | `design/<slug>/<slug>-homepage-design-brief.md` |
| `[feedback]` | the client's feedback file the scan names |
| `[article]` | the page itself |
| `[user]` | something the user said in this conversation |

(checked) Every bullet ends with a tag or starts with `GAP:`. Colours: when a source gives colour values, quote at least one exactly as given, with its role (checked); a value no source gives is never written (checked). When no source gives colours, a `GAP:` bullet says the colours are missing and who supplies them (checked). Typography and logo follow the same rule: name a typeface or logo file only as a source does, else a `GAP:`. A `GAP:` line states only what the source says about the missing item ("the logo is being redrawn; new files and colours to follow"), never a fact of its own such as "no logo file exists". Rules that limit design (a colour kept to one use, a colour banned, a look the client rejected) go here as constraints, tagged. When such a rule names a visual pattern or effect ("no carousels", "no gradients"), quote the source's words in double quotes, so it reads as the client's rule and not as your instruction.

### Responsive Priorities

Bullets, starting from mobile (checked: mentions mobile): what a phone visitor must reach first on this page type (the phone number, the booking route, the answer), and which sections can come later. Order and priority only, from the pages and `audience.md`.

### Homepage Relationship

- With a homepage option chosen: name it (checked) and say what this template carries over from the homepage brief (brand cues, CTA route, section roles it shares with the homepage, such as Hero and Final CTA), tagged where a source states it.
- Name the option, but do not relay the client's change requests to it (feedback rows with Impact `low` or higher, such as a photo size or a colour swap): they belong to the homepage design, and most are visual instructions this brief must not give.
- With no option chosen: write `direction not chosen yet` (checked) and say what waits on that choice. Name no option anywhere in the brief (checked) and do not describe what the homepage looks like.
- With no homepage design brief: a `GAP:` line (checked).

### Consistent and Variable

Two bullets at least: one starting `Consistent:` (what every page of the type keeps: section order, the CTA route, the brand rules) and one starting `Varies:` (what changes per page: the topic, the number of sections, local proof, the town) (checked).

## Open Questions

A numbered list (checked). The scaffold puts in, in this order: `direction not chosen yet` when no option is chosen (checked), a missing homepage design brief, a missing client reference kit, then every open flag on the briefed pages (`[NEEDS INPUT: ...]`, `[NEEDS SOURCE: ...]`, `[CLIENT INPUT NEEDED #n: ...]`), verbatim, with the pages it sits on and who answers it (checked: every flag present). Add anything else the designer waits on, with who answers it.

## Hand-off

What Design receives: this brief's path (checked), the content files (the Pages lists), and the homepage design brief's path with the chosen option (checked when the brief exists).

## Sources

One bullet per file read, as a path (checked: each exists).

## No visual design

The designer designs. (checked) Outside double quotes and the Sources list, the brief must not contain sizes (`px`, `pt`, `rem`, `em`), CSS properties, visual effects (rounded corners, shadows, gradients, parallax), UI patterns (carousel, slider, accordion, hamburger, animation, hover), layout instructions (full width, column counts, grid layout, card grid, sticky) or type treatments (bold, italic, underline, uppercase), and no "layout idea". Write what a block holds and how much it varies; leave how it is drawn to the designer.

## Quoted wording

(checked) Text in double quotes of four or more words must appear word for word in a source file (a page, the kit, the homepage brief or the feedback). Quote only to justify a constraint.
