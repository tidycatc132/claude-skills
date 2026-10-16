# Kickoff file specs

All files go in `kickoff/<slug>/` and start with the slug: `<slug>-context.md`, and so on. Get the slug from `python3 scripts/check_kickoff.py --slug "<Client Name>"`. Every markdown file's first line is `Client: <Client Name>`.

## Source tags

Every fact bullet (`- ` line) in `<slug>-context.md` ends with one source tag in square brackets, naming where it came from: `[transcript]`, `[site]`, `[sow]`, `[notes]` (discovery notes, pre-sale audit), `[user]` (what the person running kickoff typed), `[maps]`. Combine with commas when two sources agree: `[site, transcript]`. A bullet with no source starts with `GAP:` instead and has no tag. When two sources disagree, start the bullet with `CONFLICT:`, give both versions with their tags inside the sentence, say which one the build follows, and end with the tags of both: `[sow, transcript]`. The SOW wins on scope; the transcript wins on facts the client stated about the business; the site wins on nothing it contradicts in the other two.

Never write a fact that is not in a source. No invented review counts, ratings, years, team sizes, prices or URLs.

## `<slug>-context.md`

Headings, exactly and in this order:

```
Client: <Client Name>

# <Client Name>: client context

## Snapshot
## Business Overview
## Services
## Customers and Service Area
## Goals and Conversion
## Differentiators and Proof
## Competitors
## Website Today
## Scope Summary
## Open Items
## Sources
```

- `## Snapshot`: bullets for name, website (or the source saying there is none), service area, kickoff date. Facts the person running kickoff typed, and the kickoff date, take `[user]`; a fact that is also in a file takes that file's tag too (`[sow, user]`).
- `## Website Today`: what the current site has and lacks, page count from the inventory. With no website, one bullet saying the business has no website, tagged with the source that says so.
- `## Scope Summary` carries these, in this order:
  - a line `SOW pages: <N> [sow]` (the number the SOW states; `SOW pages: unknown` only when the SOW gives none),
  - a line `Included services: <comma-separated list from the SOW> [sow]`,
  - a `> ` blockquote copied word for word from the SOW line that states the page count, ending with ` [sow]`,
  - then bullets for exclusions and any conflict with what Sales said (as a `CONFLICT:` bullet).
- `## Open Items`: one bullet per `R` item that is not `covered`, naming the item id (`R6`), and whether it was asked or left for the call. No source tags needed here.
- `## Sources`: one bullet per file read, with its path, plus the site pages read, plus `Kickoff request` (what the person running kickoff typed) whenever any bullet carries `[user]`. No tags needed here.

## `<slug>-url-inventory.csv`

Header, exactly: `url`,`title`,`page_type`,`status`,`source`

- `page_type`: one of `home`, `about`, `service`, `location`, `contact`, `blog`, `post`, `legal`, `other`.
- `status`: the HTTP status when fetched live, `saved` for a page read from a saved copy, `listed` for a URL seen only in the sitemap or links.
- `source`: `sitemap`, `crawl`, `saved` or `user`.

Build it with `scripts/make_inventory.py`, never by hand. With no website, the file holds only the header row.

## `<slug>-gap-questions.md`

```
Client: <Client Name>

# Gap questions for <Client Name>

## Questions

1. <question>
Answer:

2. <question>
Answer:

## Checklist Coverage

| ID | Requirement | Status | Evidence |
|---|---|---|---|
| R1 | ... | covered | transcript: "..." |
```

- 3 to 5 questions, numbered `1.` to `5.`, each followed on the next line by `Answer:` with nothing after it, then a blank line. This block is pasted into the intake form's gap field, so nothing else goes between the questions.
- The coverage table has one row per item R1 to R10, with the statuses defined in `week-1-requirements.md`. Every question number appears once as `asked Qn`.

## `<slug>-project-instructions.md`

At most 80 lines. Sections: `## Client` (name, URL, service area, one-paragraph summary), `## Project Files` (each kickoff file and what it holds, plus the Sales transcript(s) and SOW), `## Working Rules` (the SOW is the scope; facts come from Project files, not guesses; flag gaps instead of filling them). Do not list skills or tools.

## `<slug>-setup-checklist.md`

The steps in `week-1-sequence.md`, in order, as `- [ ] ` items.

## `<slug>-paid-media-brief.md` (only when the SOW includes paid media)

Write it only when `python3 scripts/check_kickoff.py --paid-media <sow file>` prints `yes`. Sections: `## Paid Media Scope` (quote the SOW's paid media line, including any spend figure, word for word), `## Services and Areas to Target` (from context, with source tags), `## Seed Terms` (search phrases taken from how the client described their services, marked as unverified, with no volumes), `## Open Questions for Paid Media`.
