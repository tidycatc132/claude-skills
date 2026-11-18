# What the Week 2 check looks at

Every row `scripts/week2_handoff.py run` writes, in report order. Paths are relative to the working folder. "Incomplete" files are reported `missing` with what they lack in the note. Every failing row's note ends with the owner: the team, then the skill that makes the file.

| Item | Required | Looked for at | Present when | Stale when | Owner |
|---|---|---|---|---|---|
| Week 1 handoff | yes | `handoff/<slug>/<slug>-week-1-handoff.md` | its last non-empty line is `GO` (a `NO-GO` or no file is `missing`) | | PM, week-1-handoff-check |
| Competitor report | yes | the last-named `seo-reports/competitor-analysis/*.md` | it is not empty | | SEO, competitor-analysis |
| Growth Blueprint | yes | `blueprint/<slug>/<slug>-growth-blueprint.md` | the eight `##` sections in order (`Executive Summary` to `Measurement and Next Steps`), a `Source:` line in each, `### Phase 1`, `### Phase 2`, `### Phase 3`, `### Trajectory` under `Growth Strategy`, no `[WRITE: ...]` left. Open `[NEEDS INPUT ...]` lines are counted in the note, not blocking | | SEO, growth-blueprint |
| AM Briefing | yes | `blueprint/<slug>/<slug>-am-briefing.md` | `Executive Summary`, `Key Strategic Bets`, `Numbers the AM Should Know`, `Anticipated Client Questions`, `Calibration Framing`, no `[WRITE: ...]` | | SEO, growth-blueprint |
| Blueprint deck | yes | `blueprint/<slug>/<slug>-growth-blueprint-deck.pptx` | a readable PowerPoint file (a zip holding `ppt/presentation.xml`) | | SEO, blueprint-deck |
| Deck compliance | yes | `blueprint/<slug>/<slug>-deck-compliance.md` | zero hits: `RESULT: PASS` or `RESULT: NEEDS_INPUT`, the `em-dashes`, `prescribe`, `figures` and `quotes` rows of its `| Check | Result | Detail |` table all `PASS`, and an empty `| Slide | Check | Where | Text |` hits table | the Blueprint's `Date:` is later than the compliance file's `Checked:` date (the deck was built from an older Blueprint) | SEO, blueprint-deck |
| Sitemap report | yes | the last-named `seo-reports/site-structure-optimizer/*.md` that has a `countable pages N / SOW cap M` line and a `| Page | URL | Parent | Nav location | Priority |` URL map | both exist and N is at most M. The note gives the number of pages to write, the URL-map rows the content step never writes, and any brief or page folder that is not in the sitemap | | SEO, site-structure-optimizer |
| `Page: <page name>`, one row per URL-map row | yes | its brief: the `research/content-briefs/*.md` whose front-matter `page_url` ends in the same last segment (older `<id>.v<N>.md` copies are skipped); its page: `content/<url-slug>/` | the brief exists with `status` `DONE` or `DONE_WITH_CONCERNS`; the page has `article.md`, `metadata.md`, `article.html`, `qa_report.md` and `handoff.md`; the `VERDICT:` in `qa_report.md` is `READY`, or `NEEDS_INPUT` with at least one `[NEEDS INPUT: ...]`, `[NEEDS SOURCE: ...]` or `[CLIENT INPUT NEEDED #n: ...]` flag listed in `handoff.md` (that list is what the AM asks the client for) | | Content, content-brief (brief) or seo-content-writer (page) |
| Page-type design briefs | yes | `design/<slug>/<slug>-page-type-design-briefs.md` | `## Page Types`, `## Open Questions`, `## Hand-off`, `## Sources`, no `<fill>` left | a written sitemap page other than the homepage is not listed in it as `content/<url-slug>/`, or it lists a page that was dropped from the sitemap and deleted | Design, page-type-design-briefs |
| Week 2 client email | yes | `emails/<slug>/<slug>-week-2-email.md` | a `Subject:` line and a `Reply by: YYYY-MM-DD` line | | AM, week-2-client-email |
| Client feedback | no | the last `feedback/<slug>/*-feedback.md` with a `Week: 2` line, else the last `feedback/<slug>/*-week-2-nudge.md` | either exists. A reply's note counts the `- #<n>` items under `## SEO Review` that wait for SEO; a nudge's note says Week 3 goes ahead with the Blueprint as is. With neither, the row is `missing` and the note gives the reply-by date, or says the date passed and the nudge is due | | AM, client-feedback |

## How the page lists are compared

- The sitemap's pages are the rows of the URL map. A row's `<url-slug>` is the last segment of its URL, and `home` for `/`. Rows marked `(not in SOW scope)` (the homepage, the contact page) still need a brief and a page: they are left out of the page count, not out of the build.
- Rows the content step never writes are listed in the Sitemap report note and get no page row. Only the URL path decides, never the page name (a bakery's `/cookies/` page is checked): `/blog/` and anything under it, `/privacy...`, `/terms...`, `/cookie-policy/`, `/legal/...`, `/404/` and `/sitemap...`.
- Two checked rows whose URLs end in the same segment (`/services/back-pain/` and `/conditions/back-pain/`) would share one `content/<url-slug>/` folder, so one page could stand in for both. The Sitemap report row is then `missing` and names the pair.
- A brief or a `content/` folder with no matching URL-map row is listed in the Sitemap report note as "not in the sitemap". It does not block; someone decides whether the sitemap or the extra page is wrong.

## Choices behind the rules

- A `NEEDS_INPUT` page can go to Week 3: client facts are often still owed. It blocks only when nobody wrote down what is owed, because then the AM cannot ask for it.
- `RESULT: NEEDS_INPUT` on the deck is not a hit; the open slides are named in the note. Any em-dash, form of prescribe, figure not in the Blueprint or quote not in the quote bank is a hit and blocks.
- Staleness is read from dates and lists inside the files, never from file times, which change when folders are copied.
- The client's reply is listed so nobody forgets it, but Week 3 starts on the Blueprint as it stands.
