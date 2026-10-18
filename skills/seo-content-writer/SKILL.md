---
name: seo-content-writer
description: Use when a content brief (from the brief step after keyword research) must become the finished, publish-ready page (blog post, guide, how-to, comparison, listicle, definition, service page or homepage), optimized for Google, AI Overviews, ChatGPT and Perplexity and for readers. Trigger on "write the article from this brief", "turn this brief into the finished page", "draft the service page from this brief", "write the homepage copy from this brief", "execute this brief", including when the client's voice.md, style.md or compliance.md come with the brief. Produces article.md, metadata.md, article.html, qa_report.md and handoff.md, and flags missing evidence instead of inventing it. Do NOT use for building the brief or for a keyword-research report alone (use content-brief), auditing or scoring a page or draft not written from a brief (use content-quality-auditor), the client voice and style kit (use client-reference-kit), JSON-LD schema (use structured-data), or social posts and emails.
---

# SEO Content Writer

Third step of the content pipeline: keyword research, then the content brief, then this skill. It turns one approved brief into a page that ranks, gets quoted by answer engines, and reads well. Every passage must stand on its own when an AI system lifts it out of the page, and every fact must trace to a source a human can check.

## Inputs

- **The brief** (required): a file path or pasted text, from the content brief step. A keyword-research report is not a content brief; if that is all there is, the brief step runs first. Any layout works for you; read it for the fields in `references/brief-intake.md`. A brief from content-brief (`research/content-briefs/<id>.md`, with front-matter) already carries the intake, the outline and the evidence; `references/brief-intake.md` says how to map it. Otherwise `check_draft.py` reads two things from the brief by layout: the target keyword from a line starting `Keyword:`, `Primary:` or `Target keyword:` (else pass `--keyword`), and internal links from the section whose heading contains "internal link" (else it cannot check link placement, and you check it yourself).
- **Client reference files** (optional): if `client-reference/<client-slug>/` exists (from client-reference-kit, where `<client-slug>` is the client's domain without `www.` and the TLD, for example `cedarlinecu`), read `voice.md`, `style.md` and `compliance.md` and follow them. Their banned words, product names and disclaimers win over your defaults.
- **Live research** (optional): use WebSearch or WebFetch only if available, only to find sources for claims, and cite every page you use.

If there is no brief, only a topic, say the brief step should run first. If the user still wants the page, build the intake checklist yourself and label it an unapproved working brief in `handoff.md`.

## Outputs

Write five files into `content/<url-slug>/` (or the folder the user names). `<url-slug>` is the last segment of the brief's URL, else the primary keyword hyphenated; a homepage uses `content/home/`.

| File | What it is |
| --- | --- |
| `article.md` | The page. Layout fixed by `references/output-spec.md` |
| `metadata.md` | One `\| Field \| Value \|` table with `Meta title`, `Meta description`, `H1`, `URL slug`, `Primary question`, `Target keyword`, `Key takeaways`, `Article summary` |
| `article.html` | Semantic static HTML, made by `scripts/make_html.py` |
| `qa_report.md` | The QA table and `VERDICT:` line, made by `scripts/check_draft.py` |
| `handoff.md` | Open flags, judgment QA, build and indexability checks, post-publish tracking |

## Workflow

1. **Intake.** Read the brief like a checklist using `references/brief-intake.md`. Write down, before drafting: the primary question, 5-8 sub-questions, 8-15 entities with one primary name each, the evidence for each section, the author and credentials, first-hand material, and each internal link with its anchor. Build missing sub-questions and entities yourself (how much, how often, why, what if variants). Never build missing evidence or authors; flag them (step 3).
2. **Load the writing rules.** Read `references/writing-rules.md` in full before drafting. Read `references/format-rules.md` for the page type(s) the brief names (comparison, how-to, definition, listicle, FAQ, product or service). For a homepage (page type or format `homepage`, or URL `/`), read `references/homepage.md`: its section map and client-fact rule replace the article layout.
3. **Draft `article.md`** to the layout in `references/output-spec.md`. Where the page needs a fact you do not have from the brief, the client files or a cited source, write a visible flag in place of the fact (a brief's `[CLIENT INPUT NEEDED #n: ...]` slots are copied as they are): `[NEEDS SOURCE: what is needed]` for evidence, `[NEEDS INPUT: what is needed]` for author, pricing, URLs or client facts. Never write a number, quote, source, credential or URL you were not given or did not verify; "typical industry figures" from memory count as invented. An unverifiable number is worse than a flag.
4. **Write `metadata.md`** per `references/output-spec.md`. The meta title starts from the H1 and keeps its intent. Length limits for title and description are not enforced.
5. **Run the QA script** as its own plain command, paths as arguments:
   `python3 <skill-folder>/scripts/check_draft.py content/<url-slug>/article.md --brief <brief-path>`
   On a homepage add `--page-type homepage` and `--client-dir client-reference/<client-slug>/` (when it exists), plus `--facts <file>` for each other client file you took facts from.
   Fix every FAIL in the draft and rerun until the verdict is `READY` or `NEEDS_INPUT`. Read every WARN and fix it or say in `handoff.md` why it stays (for example, a number not in the brief that is cited in Sources).
6. **Do the judgment QA** in `references/qa-checklist.md` (the checks a script cannot make: isolation reading, entity consistency, sources match claims, YMYL depth). Fix the draft, then rerun step 5.
7. **Build the HTML**: `python3 <skill-folder>/scripts/make_html.py content/<url-slug>/article.md`
8. **Write `handoff.md`** per `references/output-spec.md`: every open flag, the build and indexability checklist, and the post-publish citation tracking plan.
9. **Answer in chat** with the `VERDICT:` line, the file list, the open flags (each one, quoted), and the top build checks. Do not call the page publish-ready unless the verdict is `READY`.

Run each script as a single plain `python3` command (use `python` where `python3` is not on the path) with paths as arguments. Do not chain commands with `&&`, `|`, `cd` or loops, and inspect files with the file-reading tool. If a command is denied, retry the plain `python3` form once before reporting that the script could not run; never hand-write `qa_report.md` in its place.

## Rules that decide most outcomes

- Every H2 and H3 is the question a real person would type or ask, except the utility sections `Key Takeaways`, `Frequently Asked Questions`, `Sources` and numbered step or list-item H3s.
- The first sentence under every heading is the complete answer and names its subject. No lead-ins, no opening pronoun.
- Every major section carries at least one specific number tied to a named source, or a `[NEEDS SOURCE: ...]` flag. Exception: a section the content brief marks `- Evidence: none verifiable` is explained without a number, as its concern says; `check_draft.py` reads that from the brief and only warns.
- One name per entity, restated at the start of paragraphs, list items and table rows.
- YMYL topics (health, finance, legal, safety): credentials, sourcing and first-hand experience come first; missing ones are flags, and `handoff.md` routes the page to compliance or expert review.

## Reference files

| File | Load when |
| --- | --- |
| `references/brief-intake.md` | Step 1, always |
| `references/writing-rules.md` | Step 2, always |
| `references/format-rules.md` | Step 2, for the page type(s) in the brief |
| `references/output-spec.md` | Steps 3, 4 and 8 |
| `references/homepage.md` | Steps 2 to 8, when the page is a homepage |
| `references/qa-checklist.md` | Step 6, and when a QA check FAILs and the fix is unclear |
