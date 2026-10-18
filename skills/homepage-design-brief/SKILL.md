---
name: homepage-design-brief
description: Writes the one homepage design brief a designer works from, after human editorial review of the homepage copy. Reads the edited homepage article.md from seo-content-writer, the client reference kit, and the kickoff context and blueprint package, and writes design/slug/slug-homepage-design-brief.md: goals, audience, sourced brand cues, only the reference sites the client named, a section map with one row per page section, imagery, must-haves, do-nots and open questions, plus an optional static HTML wireframe for HTML-to-Figma. Use when the homepage copy is reviewed (or a draft must be mapped anyway) and the design team needs the homepage design brief, a section-by-section layout handover or a wireframe. Do NOT use for writing the homepage copy (use seo-content-writer), the homepage content brief (use content-brief), brand, voice or style files (use client-reference-kit), the sitemap or page hierarchy (use site-structure-optimizer), or judging whether the page is ready to publish (use content-quality-auditor).
---

# Homepage design brief

Turns the reviewed homepage copy into the brief the designer builds the homepage design variants from. The copy is finished when this skill runs: the brief maps it, never rewrites it.

## Input

| File | Required | What it gives |
| --- | --- | --- |
| `content/<url-slug>/article.md` | yes | The edited homepage. Default `content/home/article.md`, or the path the user names. seo-content-writer opens each section with a marker such as `<!-- section: Hero -->` |
| `client-reference/<client-slug>/` | no | The kit: `brand.md`, `voice.md`, `style.md`, `audience.md`, `compliance.md` (any that exist) |
| `kickoff/<slug>/<slug>-context.md` | yes | Goals and Conversion (look and feel, conversion action), Customers, Differentiators and Proof, Competitors |
| `kickoff/<slug>/<slug>-blueprint-input-package.md` | no | Voice and Design Direction (the sites the client named), Audiences, Services Priority, from the Kickoff Call |

`<slug>` is the kickoff folder name. If there are several kickoff folders and the user named no client, ask which client; that is the only question this skill asks before writing.

## Output

- `design/<slug>/<slug>-homepage-design-brief.md`, always. The full spec, with the exact headings, tables and tags, is in `references/brief-spec.md`: load it before writing.
- `design/<slug>/<slug>-homepage-wireframe.html`, only when the user asks for a wireframe, mockup or HTML-to-Figma.

## Running the scripts

Outputs go under the working directory (`design/<slug>/`). The scripts live in this skill's folder: call each one by that full path, `python3 <skill-folder>/scripts/<name>.py ...`, as a single command with nothing chained before or after it (no `cd`, `&&`, pipes or loops). If a call is denied, send the same single `python3` command again, and use `python` if `python3` is missing. Never write the wireframe or the checker's verdict by hand because a call failed.

## Workflow

1. **Review status.** If the user said the homepage copy passed editorial review (reviewed, approved, signed off), record who and when as they gave it. If not, still write the brief from the draft as it stands, record `Content review: not confirmed`, and make that open question 1. Do not stop to ask.
2. **Map the page.** Run `python3 scripts/section_map.py <article.md>`. It prints one skeleton Section Map row per section, in page order, and every open flag on the page. If it warns that there are no markers (an editor removed them), name each row after the homepage role its heading plays.
3. **Read the sources.** The article, every kit file present, the context and the blueprint package. Note which are missing; each missing one becomes an open question.
4. **Write the brief** to the spec in `references/brief-spec.md`. The rules that matter most:
   - No copy. Headings, taglines, button labels and sentences come from the article only. Layout ideas describe structure. Quote a source only to justify a cue, word for word.
   - Design References are only sites the client named as ones they like. A competitor, a site someone at the agency suggested and a site you found are never references; a site the client dislikes becomes a Do-Not, described by what they dislike.
   - Every bullet carries its source tag, or is a `GAP:` (no file has the fact) or a `Recommended:` (a layout or pattern default of yours, never a client fact). A tag vouches that the source says that very thing. Any idea of yours, even one a source inspired (a before-and-after photo pair because the client stresses cleanup), starts with `Recommended:` and may name the source that inspired it.
   - Every open flag on the page is copied verbatim into Open Questions, so the designer knows which boxes will stay empty and who fills them.
   - Compliance rules that touch visuals (what photos must show, claims that cannot be featured) go into Imagery, Must-Haves or Do-Nots.
5. **Wireframe, when asked.** Run `python3 scripts/make_wireframe.py <article.md> <brief.md> design/<slug>/<slug>-homepage-wireframe.html`. It builds grey boxes from the page's own headings and the brief's Section Map; do not hand-write or edit the HTML.
6. **Check.** Run `python3 scripts/check_design_brief.py <brief.md> --article <article.md> --sources <every kit, context and blueprint file read>`, adding `--wireframe <html>` when one was made. Fix every FAIL in the brief, then run it again until it passes.
7. **Report** in a few lines: the brief's path (and the wireframe's), the review status, how many open questions the client or AM must answer, and the first thing the designer is waiting on.

## Scripts

| Script | Use |
| --- | --- |
| `scripts/section_map.py` | Sections and open flags of the edited page (`--json` for machine output; `--known <file>` confirms a marker list) |
| `scripts/make_wireframe.py` | The static HTML wireframe |
| `scripts/check_design_brief.py` | The brief's structure, section map, tags, references, open flags, quoted wording and wireframe |
| `scripts/selftest_brief.py` | Small cases for the checker; run it after changing `check_design_brief.py` |

All are standard-library Python 3.
