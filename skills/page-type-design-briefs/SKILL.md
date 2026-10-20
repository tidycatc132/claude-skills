---
name: page-type-design-briefs
description: Writes one design brief per page type (service, location, about, contact, resource) so the designers can build the inner-page templates. Reads the written pages in content/, the client reference kit, the homepage design brief and the chosen homepage direction from feedback/, and writes slug-page-type-design-briefs.md with, for each page type found, a section-by-section content map, repeating blocks, content length, CTA placement, sourced brand cues, mobile-first priorities, the link to the homepage direction and what varies per page. Content structure and brand constraints only, never visual styling. Use when the inner pages are written and the designers need template or page-type briefs. Do NOT use for the homepage design brief (use homepage-design-brief), writing the pages (use seo-content-writer), brand or voice files (use client-reference-kit), planning the sitemap (use site-structure-optimizer), sorting client feedback (use client-feedback), or client emails (use week-1-client-email).
---

# Page-type design briefs

The homepage already has its own design brief. This skill covers every other template: it reads the written pages, groups them by page type, and tells the designer what each template has to hold. The designer decides how it looks; the brief says what goes in it, what repeats, what varies and which brand rules bind it.

## Input

All paths are relative to the client's working folder. `<slug>` is the client's folder name under `design/` and `feedback/`.

| Path | Required | What it gives |
| --- | --- | --- |
| `content/<url-slug>/article.md` (+ `metadata.md`) | yes | The written pages, one folder each, from seo-content-writer. `content/home/` is the homepage and is left out |
| `research/content-briefs/<id>.md` | no | content-brief's front matter: `page_url` (or else `primary_keyword`) matches a brief to its page folder, and `format` tells a service page (`service-page`) from a resource article (`explainer`, `how-to` and the other article formats) when the page has no section markers. A brief with no known format falls through to the URL |
| `client-reference/<client-slug>/` | no | The kit (`brand.md`, `style.md`, `voice.md`, `audience.md`, `compliance.md`, any that exist) |
| `design/<slug>/<slug>-homepage-design-brief.md` | no | The homepage design brief (homepage-design-brief): its Brand Cues and the homepage sections |
| `feedback/<slug>/<date>-feedback.md` | no | The client's reply sorted by client-feedback. The homepage option they picked is a `## Feedback Items` row whose Type is `design` or `approval`, Impact `none`, Affects `homepage design`, naming one option in the Affects detail (`homepage design: Option B`) or else in the quote. The latest file that picks an option or asks a `question` about the homepage design decides; a question with no pick, or two different options, means not chosen |

If no page other than the homepage is written, say the pages have to be written first (seo-content-writer) and stop; write nothing. If there is more than one folder under `client-reference/`, pass the right one with `--kit`. If the user named no client and there are several `design/` folders, ask which client; that is the only question this skill asks.

## Page types

The script decides each page's type, in this order: a `--type <url-slug>=<type>` you pass; the section markers seo-content-writer writes (`<!-- section: Company Story -->`, `<!-- section: Mission and Values -->`, `<!-- section: Team -->`, `<!-- section: Credentials -->` mean about; `<!-- section: Contact Form -->`, `<!-- section: Phone and Email -->`, `<!-- section: Address and Hours -->`, `<!-- section: Map -->` mean contact; `<!-- section: How We Serve -->`, `<!-- section: Local Services -->`, `<!-- section: Local Proof -->`, `<!-- section: Directions -->` mean location; `<!-- section: Hero -->`, `<!-- section: FAQ -->` and `<!-- section: Final CTA -->` are shared); the content brief's `format:`; the `URL slug` row in `metadata.md` (`/services/...`, `/locations/...`, `/blog/...`, `/about/`, `/contact/`). When it prints `UNKNOWN TYPE`, read the page and pass `--type` for it. Only page types that have pages get a section.

## Output

`design/<slug>/<slug>-page-type-design-briefs.md`. The layout, every subsection and the evidence tags are in `references/brief-spec.md`; read it before filling the brief.

## Running the scripts

The script is `scripts/ptdb.py` in this skill's folder. Run it from the client's working folder by its full path, as one plain command: `python3 <skill-folder>/scripts/ptdb.py <mode> --slug <slug> ...`. Nothing chained before or after it (no `cd`, `&&`, pipes or loops). If a call is denied, send the same single `python3` command again, and use `python` if `python3` is missing. Never write the scaffold or the check result by hand because a call failed.

## Workflow

1. **Scan.** `python3 <skill-folder>/scripts/ptdb.py scan --slug <slug>`. It lists each page with its type, word count, H2 count, sections (or headings) and open flags; the kit files; the homepage design brief's Brand Cues; and the homepage option the client picked (`direction not chosen yet` when none). Resolve every `UNKNOWN TYPE` with `--type` and use the same `--type` options in every later call.
2. **Read the sources.** Every page listed, every kit file, the homepage design brief and the feedback file the scan names.
3. **Scaffold.** `python3 <skill-folder>/scripts/ptdb.py scaffold --slug <slug> --client "<client name>" --date <today>`. It writes the brief with everything computable filled in (header, page lists, the content map rows for pages with markers, the length lines, flags in Open Questions, Hand-off, Sources) and `<fill>` where you write.
4. **Fill every `<fill>`** following `references/brief-spec.md`. The rules that decide most outcomes:
   - Describe structure and constraints, never looks. No layouts, column counts, sizes, effects, UI patterns or type treatments; the designer chooses those. Say what a block holds and how much it varies, not how it is drawn.
   - Write no copy. Section names come from the pages; purposes are one plain line about what the section does for the visitor.
   - Every brand cue carries a source tag (`[kit: brand.md]`, `[homepage brief]`, ...) or starts with `GAP:`. A colour value is quoted only as a source gives it. When no source gives colours, a `GAP:` line says so.
   - When the client picked a homepage option, each Homepage Relationship names it and says what the template carries over from the homepage brief. When they have not, it says `direction not chosen yet` and names no option: do not guess which one they will pick.
   - Flags on the pages are boxes the designer must leave room for; they are already copied into Open Questions. Add a question for anything else the designer is waiting on.
5. **Check.** `python3 <skill-folder>/scripts/ptdb.py check design/<slug>/<slug>-page-type-design-briefs.md --slug <slug>`. Fix every FAIL in the brief and run it again until it prints `RESULT: PASS`.
6. **Report** in a few lines: the brief's path, the page types and page counts, the homepage direction, how many open questions the client or AM must answer, and the hand-off for Design (this brief, the content files, the homepage design brief).

## Scripts

| Script | Use |
| --- | --- |
| `scripts/ptdb.py scan` | Page types, lengths, sections, flags, brand cues, homepage option (`--json` for machine output) |
| `scripts/ptdb.py scaffold` | The brief with computed parts filled (`--force` to start again) |
| `scripts/ptdb.py check` | The brief against the files: sections, pages, content map, length lines, tags, colours, quotes, flags, no visual design |
| `scripts/selftest_ptdb.py` | Small cases for the checker; run after changing `ptdb.py` |

Standard-library Python 3 only.
