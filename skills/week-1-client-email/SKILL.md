---
name: week-1-client-email
description: Drafts the end-of-Week-1 email a WISE Account Manager sends a website client with the homepage design options and the homepage copy. Use when the AM asks for the Week 1 client email, the homepage design or calibration email, or the email that sends the design variants and content, for a client with homepage copy in content/[url-slug]/ and a kickoff/[slug]/[slug]-missing-items.md file. Writes emails/[slug]/[slug]-week-1-email.md in WISE's voice, never the client's brand voice, with the design links, the feedback asked for by a reply-by date, and what the client still owes. Do NOT use for the Day 1 welcome email (use welcome-email), sorting or replying to the client's feedback on the designs (use client-feedback), the design brief (use homepage-design-brief), the homepage copy itself (use seo-content-writer), or updating the missing items (use client-context-update).
---

# Week 1 client email

Writes the email that puts the homepage in front of the client at the end of Week 1: the design options, the copy, what we want back and by when. The run is done when `scripts/week1_email.py check` prints `RESULT: PASS`.

## Inputs

- Homepage copy in `content/<url-slug>/` (usually `content/home/`), written by seo-content-writer and edited by the team. The skill reads `article.md` for its client-input flags: `[CLIENT INPUT NEEDED #n: ...]` and `[NEEDS INPUT: ...]`.
- `kickoff/<slug>/<slug>-missing-items.md` from client-context-update: its `Client:` line, the `| Item | Status | Note |` intake table and the `| Platform | Status | Note |` access table, with the exact item names, platform names and statuses listed in `references/email-spec.md`. If `facts` prints `MISSING ITEMS INVALID`, report the errors and stop; never fix the file by hand.
- From the AM: the contact's name, the AM's full name, and each design option's name and link. Optional: a link to the shared copy, which option design recommends, a reply-by date. The send date is today unless the AM says otherwise.

Stop and ask, writing nothing, when the design option links, the contact name or the AM's name are missing, or when either file is missing: an email without the designs does not do its job. Do not ask about anything optional; use the defaults in `references/email-spec.md`.

## Output

`emails/<slug>/<slug>-week-1-email.md`, laid out exactly as `references/email-spec.md` says. Nothing else is written.

## Steps

1. Get the facts:
   `python3 <skill-dir>/scripts/week1_email.py facts --content content/<url-slug> --missing kickoff/<slug>/<slug>-missing-items.md --send-date <YYYY-MM-DD> [--reply-by <YYYY-MM-DD>]`
   It prints JSON: `client`, `out_path`, `flags` (one per detail the copy still needs, deduplicated), `asks` (the exact lines for the still-needed list: intake items `missing` or `partial`, and one access line for platforms marked `needs help`, `someone else manages it`, `not sure` or `no answer`), and `reply_by_text`.
2. Read `article.md`'s H1 and opening for one specific detail, then read `references/voice.md` and `references/email-spec.md`, and write the email to `out_path`.
3. Check it:
   `python3 <skill-dir>/scripts/week1_email.py check <out_path> --content content/<url-slug> --missing kickoff/<slug>/<slug>-missing-items.md --send-date <YYYY-MM-DD> --reply-by <reply_by> --contact "<contact>" --am "<AM name>" --option "<name>=<link>" [--option ...] [--content-url "<link>"] [--recommended "<option name>"] [--user-date]`
   Pass `--user-date` only when the AM gave the reply-by date. Fix every `FAIL:` line in the email and rerun until it prints `RESULT: PASS`. Never edit the copy or the missing items file to make it pass.
4. Reply with the path, the `RESULT:` line, the reply-by date, and how many copy details and still-needed items went in, plus one line reminding the AM to attach the copy if there is no link, read the email and send it.

Run each script as its own plain `python3` command with paths as arguments, never chained with `&&`, `cd` or pipes. If a call is denied, retry the same plain command once; never check the email by hand instead.

## Boundaries

- WISE's voice only. The client's slogans and style in the copy are never copied into the email.
- No fact, number or link that is not in the files or given by the AM.
- This skill writes the email; the AM sends it. It does not send email, attach files, create ClickUp tasks or process the client's reply.
