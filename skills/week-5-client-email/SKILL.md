---
name: week-5-client-email
description: Drafts the Week 5 email a WISE Account Manager sends a website client with the staging site link for their last review before launch, under 150 words, what to check (facts, names, numbers, services, contact details), how to send edits (reply, or BugHerd for guests), a reply-by date three business days out and, by default, that WISE goes ahead with the site as it is if there is no reply. Use when the AM asks for the Week 5 email, the staging review email, the email sending the staging link, or the final check before launch email. Writes emails/[slug]/[slug]-week-5-email.md, warns above it when the latest staging QA is NOT READY or has open AM items, and a script checks it. Do NOT use for the welcome email (use welcome-email), the Week 1 or 2 emails (use week-1-client-email, week-2-client-email), sorting or answering the client's staging edits (use client-feedback), the staging QA (use staging-site-qa), chasing a silent client, the final sweep before launch (use week-5-handoff-check), or the go-live email.
---

# Week 5 client email

The Account Manager sends the client the staging site once QA has been processed and the AM has reviewed it. This skill drafts that email; the AM sends it. The email is short on purpose: one link, what to look at, how to send edits, one date.

## Inputs

All paths are relative to the client's working folder; `<slug>` is the client folder name.

| Input | Required | Used for |
|---|---|---|
| `kickoff/<slug>/<slug>-context.md` | yes | `- Name:` (business name) and, if present, a `- Primary contact:` or `- Contact:` line |
| Contact name | if the context has none | the `To:` line and the greeting. If `facts` prints `Contact: unknown`, ask the AM before writing. |
| AM name | yes | the sign-off. Ask if not given. |
| Staging URL | if no QA report names one | the link. Defaults to the newest QA report's `Staging:` line. |
| Send date | no (default today) | the reply-by date |
| Protected staging | no | if yes, a password placeholder line the AM fills by hand. |
| BugHerd guest access | no | if yes, BugHerd is offered as a second way to send edits |
| Newest `qa/<slug>/<slug>-staging-qa-<YYYY-MM-DD>.md` | no (warns if missing) | its `Staging:` line, its last `RESULT:` line and the bullets under `## AM Items` |
| `client-reference/<slug>/voice.md` | if it exists | only the Tone Matrix `Email` row (formality, first names, punctuation). The email stays in WISE's voice (I and we), never the client's marketing voice. |

## Output

`emails/<slug>/<slug>-week-5-email.md`, in this order:

1. Warning lines, only when the script prints them (QA `RESULT: NOT READY`, no QA report, or open AM items). Each starts `WARNING (not part of the email):`. The AM reads them and does not send them.
2. The header, exactly as the script prints it: `Client:`, `To:`, `Send date:`, `Reply by:`, `Reply-by rule:`, `Staging:`, `Password:`, `Edits by:`, `No-reply line:`, `QA report:`. client-feedback (and week-5-handoff-check) read `Client:`, `Send date:` and `Reply by:`.
3. A blank line, `Subject: <subject>`, a blank line, then the email body, ending with the AM's name and `Account Manager, WISE Digital Partners` (or the title the AM gives).

## Steps

Run the script as plain `python3` commands from the working folder. If a command is refused, retry the same plain command once; never redo its checks by hand.

1. **Facts.** `python3 <skill-folder>/scripts/week5_email.py facts --slug <slug>` plus, as they apply: `--contact "<name>"`, `--staging-url <url>`, `--send-date YYYY-MM-DD`, `--reply-by YYYY-MM-DD` (only when the AM names a date), `--protected`, `--bugherd`, `--no-go-ahead` (only when the AM asks to drop the go-ahead line). If it prints `STOP`, tell the AM what it said and write nothing.
2. **Write the file.** Copy the block between the `-----` lines exactly, then write the subject and body. The body says, in this order and in plain words:
   - the site is ready to review, with the staging URL on its own line, and the `Password:` placeholder line right under it when the facts say so (copied exactly);
   - this is the last check before launch;
   - what to look at: facts, names, numbers, services, contact details, and anything that looks wrong;
   - how to send edits: reply to this email with the page and the change, and, only when `Edits by` includes BugHerd, comment on the page in BugHerd;
   - the reply-by date written as the facts give it (for example "Friday, November 13"), and, unless the line is dropped, that if there is no reply by then, WISE will go ahead with the site as it is.
   Keep the body under 150 words, greeting and sign-off included. Use no other date, no other link, and nothing from the QA report: no findings, severities, AM items, QA or BugHerd column names. The client never learns how many issues the team fixed.
3. **Check.** `python3 <skill-folder>/scripts/week5_email.py check emails/<slug>/<slug>-week-5-email.md`. Fix each `FAIL` row in the file and run it again until the last line is `RESULT: PASS`.
4. **Tell the AM** in chat: the file path, the subject, the reply-by date, the check's last line (`RESULT: PASS`), and every warning line in full. When the QA result is `NOT READY` or AM items are open, say so first and say the email should wait until the PM and AM have cleared them. When it is `CONDITIONAL`, say MAJOR items are still open; the email can go if the PM is happy. Name the reply-by weekday and ask the AM if a public holiday falls before it. Remind the AM to paste the staging password by hand when the placeholder is there.

A hand-edited draft: run step 3 on it and fix only what fails, keeping the AM's wording. If its header is missing lines, run step 1 with the draft's dates and settings and copy the header from there.

Load `references/email-rules.md` when the AM asks why a rule exists, wants a different reply-by date or sign-off, or the check fails a row you do not understand.

## Rules

- The reply-by date is three business days after the send date (weekends skipped, holidays not), unless the AM names a date; then pass `--reply-by` and the header records `Reply-by rule: AM's date`.
- Never write a staging password the user gives you into any file or repeat it in chat. The placeholder line is the only password line.
- The warnings go above the email, never inside it. Do not soften or drop them; the check compares them with the newest QA report.
- This skill drafts; the AM sends it. It does not send email, change BugHerd, or touch the QA files.
