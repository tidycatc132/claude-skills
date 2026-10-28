# Batch mode: write all the briefs

Load this when the user asks to write every brief in a folder ("write all the briefs", "write every page from the briefs", "write the pages that are still missing") instead of one named brief.

## Steps

1. **Plan.** Run, as its own command:
   `python3 <skill-folder>/scripts/batch_pages.py plan research/content-briefs --content content`
   (use the folders the user names instead). It lists every brief with its page folder `content/<url-slug>/`, its page type, its open client inputs and its action: `write` or `skip (exists)`. Older brief versions (`<id>.v<N>.md`) are not pages and are left out. A page counts as written when `content/<url-slug>/article.md` exists, so the homepage from Week 1 and every page written on an earlier run are skipped. Never rewrite or touch a skipped page. A `CLASH` line means two briefs would write one folder: write neither of them and name both in the answer.
2. **Write each `write` row, one page at a time, in the plan's order.** For each one, run the single-page workflow in SKILL.md (steps 1 to 8) with that brief alone, and finish it, QA run and `handoff.md` included, before opening the next brief.
   - Facts come only from that page's brief and the client files. Never carry a fact, figure, quote, name or flag answer from one page's brief into another page; if two briefs disagree on a client fact, write each page from its own brief and add an Open Flags row to both `handoff.md` files: `[NEEDS INPUT: briefs disagree on <fact>]`.
   - A brief with open client inputs keeps them as flags on its page, so its verdict is `NEEDS_INPUT`. Never fill a slot from another brief, from memory or from what a business like this usually has.
   - Load the page-type reference each brief needs (`homepage.md`, `client-pages.md`, `format-rules.md`) for that page only.
   - If a page's QA still FAILs after fixing what you can, leave its verdict as `FIX`, and go on to the next brief.
3. **Summarize.** Run:
   `python3 <skill-folder>/scripts/batch_pages.py summary research/content-briefs --content content`
   It writes `content/batch-summary.md` with one row per brief, pages written earlier included: `| Page | Brief | VERDICT | Open flags |`. A `CONFIRM` line names a page whose brief listed open client inputs but whose verdict is `READY`. For a page written in this run, check that every one of those inputs came from a client file, or put its flag back and rerun QA on that page. For a page that was skipped (written earlier), do not edit it: list the `CONFIRM` line in the answer for a person to check.
4. **Answer in chat** with the summary table exactly as printed, then the open flags grouped by page (each one quoted) and any page left at `FIX`. Do not call a page publish-ready unless its verdict is `READY`.

## Re-running

Running batch mode again writes only the pages still missing. To rewrite one page on purpose, the user names that brief and the single-page workflow runs on it.
