---
name: week-2-client-email
description: Drafts the end-of-Week-2 email a WISE AM sends a website client with the Growth Blueprint deck and the sitemap page content. Use when the AM asks for the Week 2 client email, the email sending the Blueprint or strategy deck and the page copy, or the Week 2 send-out, for a client whose deck, AM Briefing, content/[url-slug]/ pages and missing items file exist. Writes emails/[slug]/[slug]-week-2-email.md in WISE's voice, under 250 words, with 2 or 3 briefing recommendations, the deck as the file to open first, three feedback questions, one reply-by date, a walkthrough offer and what the client still owes; a script checks it. Do NOT use for the Week 1 homepage email (use week-1-client-email), the client's feedback or our reply (use client-feedback), building the deck (use blueprint-deck), the Blueprint or AM Briefing (use growth-blueprint), the page content (use seo-content-writer), the welcome email (use welcome-email), or checking Week 1 or Week 2 is complete (use week-1-handoff-check, week-2-handoff-check).
---

# Week 2 client email

At the end of Week 2 the client gets the strategy and the words for their new site in one send: the Growth Blueprint deck and the page content. This skill drafts that email for the Account Manager. A run is done when `scripts/week2_email.py check` prints `RESULT: PASS`.

## Inputs

Paths are relative to the client's working folder. `<slug>` is the kickoff folder name.

| Input | Path | Written by |
|---|---|---|
| Growth Blueprint deck | `blueprint/<slug>/<slug>-growth-blueprint-deck.pptx` (or the path the AM gives with `--deck`) | blueprint-deck |
| AM Briefing | `blueprint/<slug>/<slug>-am-briefing.md`: `Executive Summary`, `Key Strategic Bets`, `Numbers the AM Should Know`, `Anticipated Client Questions`, `Calibration Framing` | growth-blueprint |
| Page content | `content/<url-slug>/article.md`, one folder per page, with its `[NEEDS INPUT: ...]` and `[CLIENT INPUT NEEDED #n: ...]` flags | seo-content-writer |
| Missing items | `kickoff/<slug>/<slug>-missing-items.md`: the `| Item | Status | Note |` and `| Platform | Status | Note |` tables | client-context-update |

From the AM: the contact's name and the AM's own name (required). Optional: the send date (default today), a reply-by date, links (a shared copy of the deck, the page copy document, a booking link for the walkthrough), the PDF's file name, or that no PDF goes with it.

Stop and write nothing when the contact or AM name is missing, or when `facts` prints `INPUT MISSING OR INVALID`: say which file is missing and who makes it (the deck: blueprint-deck; the briefing: growth-blueprint; the pages: seo-content-writer; the missing items: client-context-update). Never draft around a missing deck: the deck is what this email delivers. Do not ask about anything optional.

## Output

`emails/<slug>/<slug>-week-2-email.md`, laid out as `references/email-format.md` says. Nothing else is written.

## Steps

1. **Facts.** `python3 <skill-folder>/scripts/week2_email.py facts --slug <slug> --contact "<contact>" --send-date <YYYY-MM-DD> [--reply-by <YYYY-MM-DD>] [--deck <path>] [--pdf <name> | --no-pdf]`
   It prints JSON: `client`, `out_path`, `greeting`, `deck_file`, `pdf_file`, `reply_by`, `reply_by_text`, `bets` (the briefing's Key Strategic Bets without their `Wrong if:` part), `pages` (each page's label and flags) and `asks` (the exact still-owed lines). Without `--reply-by` the date is four business days after the send date.
2. **Read** `references/email-format.md` and `references/voice.md`, then the AM Briefing's `Executive Summary` and `Key Strategic Bets`. Do not open the deck; `facts` already read it.
3. **Write** the email to `out_path`. Pick the two or three bets that matter most to the client and restate each in plain words, one bullet each. Paste every `asks` line exactly as printed.
4. **Check.** `python3 <skill-folder>/scripts/week2_email.py check <out_path> --slug <slug> --contact "<contact>" --am "<AM name>" --send-date <YYYY-MM-DD> --reply-by <reply_by> [--link <url> ...] [--user-date] [--deck <path>] [--pdf <name> | --no-pdf]`
   Pass every link the AM gave, each with its own `--link`, in the order they will appear on the `Links:` line. Pass `--user-date` only when the AM chose the reply-by date. `references/checks.md` says what each row tests. Fix every `FAIL` in the email and rerun until it prints `RESULT: PASS`. Never edit the briefing, the pages or the missing items to make it pass.
5. **Answer** with the path, the `RESULT:` line, the reply-by date, how many still-owed lines went in, and one line reminding the AM to export the deck to PDF (unless `--no-pdf`), attach the files, read the email and send it.

Run each script as its own plain `python3` command with paths as arguments: no `cd`, no `&&`, no pipes. Write the skill folder's real path in place of `<skill-folder>`. If a command is denied, retry that exact command once; never check the email by hand instead.

## Rules

- **WISE's voice, never the client's.** The page copy is in the client's brand voice for their customers; none of its slogans or phrasing goes in the email.
- **The briefing is internal.** Use its bets and figures, restated for the client. Never its `Wrong if:` lines, its anticipated questions and answers, its `Calibration Framing` or the word "briefing".
- **Figures come from files.** Every number in digits, and number words from four up, must appear in the briefing's first three sections, the deck or a missing-items note; the briefing's questions and framing are not sources. No promises of rankings, traffic or patients.
- **Links only from the AM.** No link the AM did not give.
- This skill writes the email; the AM sends it. It does not send email, attach files or handle the reply.

## References

- `references/email-format.md`: read at step 2. The exact layout, line by line, and what each part must say.
- `references/voice.md`: read at step 2. How WISE sounds in this email and what it never does.
- `references/checks.md`: read at step 4, or when a check row fails. Every check and its usual fix.
