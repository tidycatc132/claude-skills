---
name: client-feedback
description: Sorts a website client's reply to the Week 1 review (homepage copy and designs) or the Week 2 review (Growth Blueprint, deck and page content) into a feedback table and drafts the Account Manager's answer, or a nudge when the Week 2 reply-by date passes with no reply. Use when the client's reply to the homepage or Blueprint email needs triage, sorting, its facts pulling out or an answer drafting, or the client has not answered the Week 2 email. Checks page requests against the scope, holds Blueprint direction changes for SEO, writes facts for client-context-update, and drafts a reply in WISE's voice. Do NOT use for the emails sending the work (use week-1-client-email or week-2-client-email), merging updates or an email with only business facts or access (use client-context-update), the welcome email (use welcome-email), changing the Blueprint (use growth-blueprint) or rebuilding the deck (use blueprint-deck), rewriting copy (use seo-content-writer), or checking Week 1 is complete (use week-1-handoff-check).
---

# Client feedback

Turns the client's answer to the Week 1 email (homepage copy and designs) or the Week 2 email (Growth Blueprint deck and page content) into work the team can act on and a reply the AM can send. You read the client and decide what each point is; `scripts/feedback.py` holds every quote to the client's own words, checks scope requests against the scope source, writes the files and checks them. Nothing is finished until the script's check ends with `RESULT: PASS`.

## Inputs

- The client's feedback as a text file: the email as received, with or without headers and the quoted thread below it. If the user pastes it, first save it word for word as `feedback/<slug>/<date>-client-email.txt` (`<date>-2-client-email.txt` when that name is taken by another email) and use that file. Only the client's own words count; headers, `>` lines and the quoted earlier email are ignored.
- The kickoff folder `kickoff/<slug>/` from new-build-kickoff, holding at least `<slug>-context.md` (its `Client:` line and `## Scope Summary` are read). Read `<slug>-missing-items.md` too when it exists: it says what the client still owes. Without the context there is nothing to check scope against: tell the user the kickoff (new-build-kickoff) has to exist first, and write nothing.
- For a reply to the Week 2 email, also the Week 2 files in the working folder: `blueprint/<slug>/<slug>-growth-blueprint.md` (required; its `##` section names are read), the `content/<url-slug>/article.md` pages (the `<url-slug>` folder names are read) and `emails/<slug>/<slug>-week-2-email.md` (its `Send date: YYYY-MM-DD` and `Reply by: YYYY-MM-DD` lines are read). Read [Week 2](references/week-2.md) before sorting. You can tell it is the Week 2 reply when the client answers the Blueprint, deck, sitemap or page content, or quotes the Week 2 email.
- From the user: the AM's name for the sign-off. Without one, use the AM the context names; failing that, the script signs `[AM name]` and you tell the user to fill it in.

## Outputs

In `feedback/<slug>/`, next to `kickoff/`. The script writes both; never write or edit them by hand.

- `<date>-feedback.md`, where `<date>` is the date the client wrote (`YYYY-MM-DD`):
  - Header lines `Client:`, `Date:`, `From:` (the feedback file name) and `Scope source:`; a Week 2 reply adds `Week: 2`, `Blueprint:` and `Week 2 email:` (with its reply-by date).
  - `## Summary`: item counts by type, what was approved, scope requests by verdict, and the updates file.
  - `## Feedback Items`: one table `| # | Feedback | Type | Affects | Impact | Action | Owner |`. Feedback is a verbatim quote; Type is `content`, `design`, `scope`, `question` or `approval`, plus `strategy` in a Week 2 reply; Affects starts with `homepage copy`, `homepage design`, `site scope`, `client context`, `timeline`, `platform access`, `intake items` or `other` (a detail may follow a colon, `homepage design: Option B`), plus `blueprint: <section>` and `page: <url-slug>` in a Week 2 reply; Impact is `none`, `low`, `medium` or `high`, and in a Week 2 reply it goes on to name what changes (`high: Blueprint Keyword Opportunity; deck slides 9, 10; pages home`); Owner is `AM`, `Content`, `Design`, `SEO` or `Dev`.
  - `## Scope Check`: one line per scope row with its verdict (`outside scope`, `to confirm` or `within scope`) against the scope source, or `- No scope requests.`
  - Week 2 only, `## SEO Review`: `Status: hold the reply until SEO signs off the items below`, then one `- #<n> <Blueprint section>: <action>` line per strategy item; with none, `- No strategy items; the reply can go once the AM has read it.`
  - `## Reply Draft`: `Subject:` line, the email, then the AM's name and `Account Manager, WISE Digital Partners`.
- `<date>-feedback-updates.md`, only when the client stated facts: client-context-update's updates format (`Client:`, `Source: client`, `Date:`, `From:`, `## Updates`, then `| # | Section | Fact | Evidence |`). With no facts, no file. `feedback.py updates-json` prints the same rows as JSON with the keys `Client`, `Source`, `Date`, `From` and `rows` (the contract with client-context-update).

A second, different email on the same date gets `<date>-2-feedback.md`; rerunning the same email overwrites its own files.

- `<today>-week-2-nudge.md`, only when the client has not answered the Week 2 email by its reply-by date: `## Notes` (Week 3 proceeds with the Blueprint as is) and `## Nudge Draft`. See [Week 2](references/week-2.md).

## Steps

Run the script by its path inside this skill's folder (`<skill-dir>` is the folder holding this SKILL.md), as one plain `python3` command with paths as arguments. Keep each call a single command: no `&&`, `|` or `cd`. Read files and look for folders with the file-reading and search tools, not shell commands. A denied call gets retried once exactly as it was, and a denied `ls` or `cat` says nothing about `python3`: still run the script. The files the script writes are never typed by hand instead.

1. **Read** the whole feedback file, `<slug>-context.md` and `<slug>-missing-items.md`. Then get the scope source: `python3 <skill-dir>/scripts/feedback.py scope kickoff/<slug>` (add `--week 2` for a Week 2 reply: it also lists the Blueprint sections, page folders, deck slides and reply-by date).
2. **Sort and decide.** Read [Sorting Rules](references/sorting-rules.md), and for a Week 2 reply [Week 2](references/week-2.md), and split the client's text into items, pick each one's type, affects, impact, action and owner, judge every scope request, and pick out the facts for the context.
3. **Draft the reply.** Read [Reply Voice](references/reply-voice.md) and write the reply body.
4. **Write the plan** as `feedback-plan.json` in the working directory, in the shape given in Sorting Rules.
5. **Dry run:** `python3 <skill-dir>/scripts/feedback.py render kickoff/<slug> --feedback <feedback file> --plan feedback-plan.json --dry-run`. Each line under `PLAN REJECTED` names a problem in the plan; correct the plan and dry-run again until you see `PLAN OK`.
6. **Render:** the same command without `--dry-run`. It writes the files and runs the check. On `RESULT: FAIL`, fix the plan and render again.

No reply to the Week 2 email and its reply-by date has passed: skip the steps above and follow the nudge steps in [Week 2](references/week-2.md) (`feedback.py nudge`).

## Answer

In chat: the files written; a short list of the items by owner; for a Week 2 reply, the items waiting for SEO before the reply goes, and the Blueprint sections, deck slides and pages that change; each scope request with its verdict; the facts going to the context and the line `run client-context-update with <updates file>` when there is one; any login or password the client sent, by kind only, with a note that the AM should ask them to change it; the reply draft as written; and the checker table with its `RESULT:` line.

## Boundaries

- Never agree to pages or deliverables beyond the scope source; the AM settles those with a change order.
- Never copy a password, username, PIN or code anywhere, including the chat answer.
- No fact, number, date or promise the client's text, the kickoff folder or the user does not give.
- Never say the Blueprint's direction has changed, or promise it will, before SEO has reviewed the point.
- This skill drafts; the AM sends. It does not edit the copy, designs, Blueprint or deck, update the context, or create tasks.
