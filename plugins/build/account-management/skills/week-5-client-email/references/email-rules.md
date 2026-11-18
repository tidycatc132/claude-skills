# Why the Week 5 email is shaped this way

## The check, row by row

| Row | What it needs | Why |
|---|---|---|
| header lines | The ten header lines, in the order the facts print them | week-5-handoff-check reads `Send date:` and `Reply by:`; the rest records the choices so the check can test the body against them. |
| client name | `Client:` equals the context's `- Name:` | The email names the right business. |
| reply-by date | Three business days after `Send date:` (rule `3 business days`), or a weekday after it (rule `AM's date`) | Week 5 runs on a short clock before launch. |
| warnings above the email | Exactly the warning lines `facts` prints for the newest QA report | A NOT READY site or open AM items mean the AM should hold the email. The warnings must match the current report, so a stale or edited warning fails. |
| QA report line | The newest `qa/<slug>/<slug>-staging-qa-<date>.md` and its result | Shows which QA run the email was written against. |
| no warning inside the email | No `WARNING` line below `Subject:` | Warnings are for the AM only. |
| body under 150 words | At most 149 words from the greeting to the title line | Short emails get read. |
| greeting | `Hi <first name>,` (`Hi Dr. <last name>,` for a title) | Matches the `To:` line. |
| sign-off | Last line is the title (default `Account Manager, WISE Digital Partners`) | WISE's standard sign-off; pass `--title` to check against another. |
| staging link / no other links | The `Staging:` URL is in the body; every other URL is under it | One place to go. A BugHerd board link is not needed: guests comment on the page itself. |
| reply-by written out / one date only | The reply-by date as `Weekday, Month day`, and no other weekday, month-day or numeric date | One date leaves nothing to misread. |
| last check before launch | The word `launch` | The client needs to know this is the final look. |
| what to look at | facts, names, numbers, services, contact details | What clients are best placed to catch; design opinions at this stage are a scope question for the AM (client-feedback handles them). |
| reply to send edits | The word `reply` | Email is always a way in. |
| BugHerd mention | BugHerd named only when `Edits by: reply or BugHerd` | Clients without guest access cannot use it. |
| password placeholder | `Password: [AM: paste the staging password here]` when protected; no password line or word when not | Passwords never sit in a file. |
| no-reply line | With `No-reply line: yes`, a sentence with "go ahead" and the date or "by then"; with `dropped`, none | The default keeps launch from stalling; the AM may drop it for a client who would read it as pressure. |
| no internal words | None of: QA, punch list, severity, CRITICAL/MAJOR/MINOR, finding, launch toggle, noindex, AM items, handoff, go-live message, scope change, BugHerd column names, guest access, internal, PM, RESULT lines | The client sees a finished site, not the team's checklist. |

## Changing the defaults

- Another reply-by date: run `facts` with `--reply-by YYYY-MM-DD`. It must be a weekday after the send date.
- Holidays: the count skips weekends only. If a holiday falls inside the three days, the AM picks the date and you pass `--reply-by`.
- Another sign-off title: write it as the last line and run `check` with `--title "<title>"`.
- A protected site where the AM wants the password in a separate email: drop `--protected` and write no password line; tell the AM.
