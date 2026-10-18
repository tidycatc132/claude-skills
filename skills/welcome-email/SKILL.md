---
name: welcome-email
description: Writes the Week 1 welcome email a WISE Account Manager sends a new website client right after kickoff. Use when the AM asks for the welcome email, Day 1 client email or the email sending the intake form, for a client whose kickoff files exist (kickoff/[slug]/ with the context and the AM-reviewed gap questions). Reads those files and the links the AM gives (intake form, Kickoff Call booking page), and writes welcome-email/[slug]/[slug]-welcome-email.md, a ready-to-paste email in WISE's voice, not the client's, that introduces the AM, links the intake form, lists only the gap questions still unanswered, and explains what happens in Week 1. Do NOT use for the kickoff files or the gap questions themselves (use new-build-kickoff), the client's brand and voice files (use client-reference-kit), ClickUp updates (use clickup-progress-sync), merging intake answers into the context (use client-context-update), or later client emails such as the Week 1 homepage design email or sales outreach (not covered by this skill).
---

# Welcome email

Writes the first email the Account Manager (AM) sends a new client, after kickoff and after the AM has reviewed the gap questions. The run is done when `scripts/check_email.py` prints `RESULT: PASS`.

## Inputs

- `kickoff/<slug>/<slug>-context.md` and `kickoff/<slug>/<slug>-gap-questions.md`, written by new-build-kickoff and possibly edited by the AM. Use the files as they are now: the AM may have answered some questions on their `Answer:` line or deleted them.
- The AM's full name.
- The intake form link (a ClickUp Form link, used exactly as given, pre-filled or not).
- Optional: the Kickoff Call booking link.

If the kickoff files are missing, say so and stop; this skill does not write them. If the AM's name or the intake form link is missing, ask for it and stop: a welcome email without the form link does not do its job. A missing booking link is fine (the email asks for times instead).

## Output

`welcome-email/<slug>/<slug>-welcome-email.md`, laid out exactly as `references/email-spec.md` says: `Client:` line, `Subject:` line, blank line, then the email to paste. Nothing else is written.

## Steps

1. List the open questions:
   `python3 <skill-dir>/scripts/open_questions.py kickoff/<slug>/<slug>-gap-questions.md --open`
   It prints a JSON list of `number`, `question` and `answer` items. These, in this order and word for word, are the only questions the email asks.
2. Read `kickoff/<slug>/<slug>-context.md` for the greeting name and one or two specific details (the goal they named, the service they want to grow, what is wrong with today's site).
3. Read `references/voice.md` (how WISE sounds, what it never says) and `references/week-1-for-clients.md` (what the client is told happens next), then write the email to the spec in `references/email-spec.md`.
4. Check it:
   `python3 <skill-dir>/scripts/check_email.py welcome-email/<slug>/<slug>-welcome-email.md --gap kickoff/<slug>/<slug>-gap-questions.md --context kickoff/<slug>/<slug>-context.md --am "<AM full name>" --form-url "<form link>" [--booking-url "<booking link>"]`
   Fix every `FAIL:` line in the email and rerun until it prints `RESULT: PASS`. Never edit the kickoff files to make it pass.
5. Reply with the path, the `RESULT:` line, how many questions went in and how many were left out as answered, and one line reminding the AM to read it and add a personal touch before sending.

Run each script as its own plain `python3` command with paths as arguments, never chained with `&&`, `cd` or pipes; read files with the file-reading tool, not the shell. If a call is denied, retry the same plain command once; never check the email by hand instead.

## Boundaries

- The email is in WISE's voice. The client's tagline, slogans and style in the context file are never copied into it.
- No fact, number or link that is not in the kickoff files or given by the AM.
- This skill writes the email; the AM sends it. It does not send email, create ClickUp tasks or book the call.
