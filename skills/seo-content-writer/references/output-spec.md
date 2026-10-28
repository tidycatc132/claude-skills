# Output spec

All files go in `content/<url-slug>/` unless the user names another folder. The scripts read these layouts, so keep them exact. A homepage uses the layout in `homepage.md` for `article.md` (and its folder is `content/home/`), and an About, Contact or location page the layout in `client-pages.md`; the other files follow this spec with the changes listed there.

## `article.md`

Plain markdown, no front matter, in this order: the metadata table (see "Metadata table" below), a blank line, then the page:

```
| Field | Value |
| --- | --- |
| Meta title | ... |
...

# <H1: the primary question or a title containing the target phrase>

By [<Author Name>](<bio-url>), <credentials> · Updated <YYYY-MM-DD>

<Opening answer: 2-4 sentences. First sentence answers the primary question with a sourced specific. On a definition page the first sentence is the one-sentence definition.>

## Key Takeaways

- <3-7 bullets, each a complete sentence>

## <Question heading?>

<Answer-first section ... one H2 per sub-question, H3s where a section needs them>

## Frequently Asked Questions        (when the brief asks for an FAQ)

### <Question?>

<2-4 sentence complete answer>

## <CTA question heading, for example "How do I book ...?">

<CTA with the brief's contact route>

## Sources

1. <Publisher>, "<Title>", <URL if known>. <What it supports on this page>
```

- `## Sources` lists every source a figure on the page names, including the client's own records, pricing, interviews and each first-hand case ("Harbor & Pine job record, Oregon City, 2025"). If a sentence names a source, that source has a line here.

- Byline line starts with `By `. If the author is missing: `By [NEEDS INPUT: author name, credentials and bio URL]`. Use today's date for Updated.
- Flags: `[NEEDS SOURCE: ...]` for missing evidence, `[NEEDS INPUT: ...]` for missing author, prices, URLs, client facts or approvals. Write them inline where the fact belongs. They stay visible until a human resolves them.
- Required disclaimers from `compliance.md` go above `## Sources`, in their approved wording.

## Metadata table (top of `article.md`)

The first lines of `article.md`, before the H1 (and before a client page's first section marker). One table, these eight rows in this order, field names exact. The scripts read it from there; it is not printed in `article.html` or `article-semantic.md`. There is no separate `metadata.md`.

```
| Field | Value |
| --- | --- |
| Meta title | <the H1 wording, optionally followed by " | <Brand>"; nothing else: no added topic list, slogan or location string> |
| Meta description | <the direct answer plus what else the page covers, with one specific> |
| H1 | <exactly the article's H1> |
| URL slug | <from the brief, else /<url-slug>/> |
| Primary question | <from intake> |
| Target keyword | <primary keyword from the brief> |
| Key takeaways | - <takeaway 1><br>- <takeaway 2><br>- <...> |
| Article summary | <3-4 sentences that state the page's findings directly, in the voice of the page, never "This page/article explains...": the answer with its key figure, the main factor or cause, the most useful practical figure, and the next step; every figure names its source in the same sentence, as in the body> |
```

Default character limits do not apply to the meta title and description; write them for clarity and intent. Key takeaways match the page's `## Key Takeaways` bullets.

## QA report (working file, not in the page folder)

`scripts/check_draft.py` writes `qa/<url-slug>/qa_report.md` (beside `content/`, not inside it). Never hand-write or edit it, and never copy it into `content/<url-slug>/`. Its first line is `VERDICT: READY`, `VERDICT: NEEDS_INPUT` or `VERDICT: FIX`.

## `article.html`

Written by `scripts/make_html.py` from `article.md`; the meta title and description come from its metadata table. Never hand-edit; change the markdown and rerun.

## `article-semantic.md`

Written by `scripts/make_semantic.py` from `article.md`. Never hand-edit; change the markdown and rerun. It is the second version of the content: the markdown kept as markdown (paragraphs, lists, tables, links, H3s), with HTML only where markdown cannot express the tag or the attribute. Every tag sits on its own line with a blank line on each side, so a CommonMark renderer still parses the markdown between the tags.

```
<main id="main-content">
  <article id="<h1-slug>" itemscope itemtype="https://schema.org/Article">
    <header class="article-header">
      <h1 itemprop="headline">                 the H1
      <p class="byline">                       By <a rel="author" ... itemprop="author">, <time datetime="YYYY-MM-DD" itemprop="dateModified">
      <intro paragraphs as markdown>
      <section class="key-takeaways" aria-labelledby="key-takeaways-heading">   the Key Takeaways list
      <nav class="table-of-contents" aria-labelledby="toc-heading">              numbered links to every section (articles with 3 or more sections)
    </header>
    <section id="<h2-slug>" aria-labelledby="<h2-slug>-heading">   one per question H2, its H3s kept as markdown ###
    <section id="<h2-slug>" class="cta" aria-labelledby="...">     the CTA section: a client page's Final CTA, else the last question H2 (this spec puts the CTA last)
    <section id="frequently-asked-questions" ... itemscope itemtype="https://schema.org/FAQPage">
      <article itemprop="mainEntity" itemscope itemtype="https://schema.org/Question">  one per FAQ H3 (itemprop="name"), its answer in <div itemprop="acceptedAnswer"><div itemprop="text">
    <footer class="article-footer">
      <section class="sources" aria-labelledby="sources-heading">   the Sources list
      <section class="summary" aria-labelledby="summary-heading">   the metadata `Article summary`
    </footer>
  </article>
</main>
```

A client page's `<!-- section: ... -->` markers become `data-section` attributes (Hero on the `<header>`) and are never printed; a client page gets no byline, Key Takeaways or table of contents because `article.md` has none. The script checks its own output (one `<main>`, one `<article>`, every `<section>` labelled by a heading id that exists, no heading level skipped) and prints `SEMANTIC: OK`; `python3 scripts/make_semantic.py --check <file>` runs the same check on any such file.

## `handoff.md`

Only the verdict and the open flags, nothing else:

```
# Handoff: <H1>

VERDICT: <same verdict as qa/<url-slug>/qa_report.md>

## Open Flags
| Flag | Where | Who resolves it |
| --- | --- | --- |
(one row per [NEEDS SOURCE], [NEEDS INPUT] and [CLIENT INPUT NEEDED] flag in article.md, quoted; "None" if empty)
```

On a YMYL page with no reviewer named in the client files, add a row `[NEEDS INPUT: compliance or expert reviewer for this page]`, resolved by the client.
