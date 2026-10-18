# Output spec

All files go in `content/<url-slug>/` unless the user names another folder. The scripts read these layouts, so keep them exact. A homepage uses the layout in `homepage.md` for `article.md` (and its folder is `content/home/`); the other files follow this spec with the changes listed there.

## `article.md`

Plain markdown, no front matter, in this order:

```
# <H1: the primary question or a title containing the target phrase>

By [<Author Name>](<bio-url>), <credentials> · Updated <YYYY-MM-DD>

<Opening answer: 2-4 sentences. First sentence answers the primary question with a sourced specific. On a definition page the first sentence is the one-sentence definition.>

## Key Takeaways

- <3-7 bullets, each a complete sentence that starts with the entity name, not a pronoun>

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

## `metadata.md`

One table, these eight rows in this order, field names exact:

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
| Article summary | <3-4 sentences that state the page's findings directly, in the voice of the page, never "This page/article explains...": the answer with its key figure, the main factor or cause, the most useful practical figure, and the next step> |
```

Default character limits do not apply to the meta title and description; write them for clarity and intent. Key takeaways match the page's `## Key Takeaways` bullets.

## `qa_report.md`

Written by `scripts/check_draft.py`. Never hand-write or edit it. Its first line is `VERDICT: READY`, `VERDICT: NEEDS_INPUT` or `VERDICT: FIX`.

## `article.html`

Written by `scripts/make_html.py` from `article.md` and `metadata.md`. Never hand-edit; change the markdown and rerun.

## `handoff.md`

Sections in this order:

```
# Handoff: <H1>

VERDICT: <same verdict as qa_report.md>

## Open Flags
| Flag | Where | Who resolves it |
(every [NEEDS SOURCE] and [NEEDS INPUT] in article.md and metadata.md; "None" if empty)

## Intake
(the eight intake items, each marked from brief / built / FLAG)

## Judgment QA
(each item in qa-checklist.md "Judgment checks", PASS or what was fixed or left and why; every WARN kept from qa_report.md with the reason)

## Build and Publish Checklist
(the developer's checks, unchecked boxes, see below)

## After Publishing
(the tracking plan, see below)
```

### Build and Publish Checklist (copy, fill the specifics)

- [ ] Build from `article.html`: semantic `<article>`, `<header>`, `<section>`, `<aside>`; one H1; heading levels not skipped.
- [ ] Critical facts (prices, specs, hours, key answers) are in the initial HTML, not loaded by JavaScript.
- [ ] Page is indexable: no `noindex`, not blocked in robots.txt, listed in the XML sitemap.
- [ ] Canonical tag points to the page's own final URL; no existing page targets the same primary question (check for cannibalization against <list any pages the brief names>).
- [ ] Mobile-friendly, HTTPS with no mixed content, Core Web Vitals pass.
- [ ] Redirects to this URL are one hop or fewer.
- [ ] Reachable within 3 clicks of the homepage or a hub page; the pillar page links here.
- [ ] Byline links to a bio page that shows the credentials.
- [ ] Structured data (Article, author Person, FAQPage where used) is a separate job (structured-data skill); it must match the visible text.
- [ ] YMYL only: compliance or expert review signed off by <reviewer named in the client files>. If no reviewer is named, write `[NEEDS INPUT: compliance reviewer for ...]` here and list it under Open Flags, with the disclosures the page still needs (for lending, for example, the regulator's required notices).

### After Publishing (copy, fill the specifics)

- Spot-check the primary question and 3 sub-questions in Google AI Overviews / AI Mode, ChatGPT and Perplexity within 2-4 weeks; log whether the page is cited.
- Add the page to the monthly check of AI Overview appearance, AI-platform referral traffic and organic rankings.
- Treat early citation checks as a directional signal, not proof that a specific change caused a result.
- If the page ranks outside the top 3 after 8-12 weeks, revisit it to add evidence and sub-question coverage.
