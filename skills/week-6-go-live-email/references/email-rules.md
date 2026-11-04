# Go-live email: body rules

Load this before writing the body. Each rule below names the check that tests it (`golive_email.py check`).

## Order of the body

1. `Hi <first name>,` on its own line (check: greeting). The first name is the first word of the `To:` line.
2. **The site is ready.** One or two sentences: the new website is ready to go live (check: says the site is ready).
3. **What launches.** The new design and the new content across the real page count, for example "the new design and fresh content across all 5 pages". You may name page groups using the counts `facts` printed ("two service pages"). Then the integrations the PM named, in plain words ("your contact form and Google Analytics go live with it"). With none named, say nothing about integrations. (Checks: recap names the new design, recap names the new content, total page count stated, page numbers match the dev handoff index, named integration listed, no unnamed integration.)
4. **The launch.** With no agreed date: ask the client to confirm they are ready for us to launch, and say we will set the day and time with them (check: asks the client to confirm). With an agreed date: state it written out as `facts` printed it, for example "Tuesday, November 24 at 10:00" (or "10am"; the check accepts `10:00`, `10am`, `10 am`, `10 a.m.`) (check: agreed launch date stated). Do not ask them to pick a date they already agreed.
5. **Right after launch.** We check every page on the live site, submit the sitemap and watch indexing over the first days (checks: every page, sitemap, indexing).
   Say it with a check verb ("we check every page"): the recap's "all 5 pages" does not count.
6. **After that.** The monthly work starts after launch; they will get a short close-out summary and a plan for the next months (checks: monthly, summary, plan). Do not list roadmap tasks: the roadmap is written later.
7. A short thank-you or closing line in the client's voice.
8. The sign-off, as the last lines: the sender's name (if given) on one line, then `<role>, WISE Digital Partners` (check: sign-off). Default: `Account Manager, WISE Digital Partners` alone.

## Words

- Under 200 words from the greeting to the sign-off (check: body under 200 words). Aim for 110 to 160.
- Follow the voice row `facts` printed (sentence length, exclamation marks, first names). With no voice file: plain, warm, short sentences, no exclamation marks.
- Never use: QA, BugHerd, severity, CRITICAL, MAJOR, MINOR, GO, NO-GO, handoff, dev index, deferred, noindex, toggle, final sweep (check: no internal terms). Never mention open issues, fixes in progress or items held for after launch.
- Never claim structured data, schema, rich results or markup (check: no structured data or schema claim).
- No links: the site is not live and staging is done (check: no links).
- Numbers about pages must be the total or a group count from `facts` (check: page numbers match). Do not name a page outside this launch (check: no page outside this launch named).

## Subject

`Subject: ` and a plain line such as "Your new <business> website is ready to launch" or, with an agreed date, "Your new website goes live on Tuesday, November 24". No internal terms.

## Warnings

The check writes one `WARNING:` line when:

- the Week 5 handoff file is missing (header shows `(missing)`): run week-5-handoff-check first;
- its last line is `NO-GO` (header shows `(NO-GO)`): a new final sweep must end `GO` before sending;
- its last line is neither (header shows `(no result line)`): re-run week-5-handoff-check;
- the dev handoff index does not end `GO`: some Build pages may not be ready, so the page count may be wrong.

The email is still drafted under the warning so it is ready when the sweep ends GO. When it does, run `check` again: it removes the warning and the header changes to `(GO)`, so update the header line to match.
