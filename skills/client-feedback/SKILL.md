---
name: client-feedback
description: Sorts a website client's reply to the Week 1 review (homepage copy and design options) into a feedback table and drafts the Account Manager's answer. Use when the client's reply or response to the homepage review email needs triage, sorting, its facts pulling out or an answer drafting. Types each point as content, design, scope, question or approval with an owner, checks page and deliverable requests against the scope source in the kickoff context, writes the facts the client stated as a feedback-updates file for client-context-update, and drafts a reply in WISE's voice that answers the questions and agrees to nothing outside scope. Do NOT use for the email that sends the designs (use week-1-client-email), merging the updates into the context, or a client email that only states business facts or access news with no Week 1 feedback (use client-context-update), the Day 1 welcome email (use welcome-email), or rewriting the copy (use seo-content-writer).
---

# Client feedback

Turns the client's answer to the Week 1 email into work the team can act on and a reply the AM can send. You read the client and decide what each point is; `scripts/feedback.py` holds every quote to the client's own words, checks scope requests against the scope source, writes the files and checks them. Nothing is finished until the script's check ends with `RESULT: PASS`.

## Inputs

- The client's feedback as a text file: the email as received, with or without headers and the quoted thread below it. If the user pastes it, first save it word for word as `feedback/<slug>/<date>-client-email.txt` (`<date>-2-client-email.txt` when that name is taken by another email) and use that file. Only the client's own words count; headers, `>` lines and the quoted earlier email are ignored.
- The kickoff folder `kickoff/<slug>/` from new-build-kickoff, holding at least `<slug>-context.md` (its `Client:` line and `## Scope Summary` are read). Read `<slug>-missing-items.md` too when it exists: it says what the client still owes. Without the context there is nothing to check scope against: tell the user the kickoff (new-build-kickoff) has to exist first, and write nothing.
- From the user: the AM's name for the sign-off. Without one, use the AM the context names; failing that, the script signs `[AM name]` and you tell the user to fill it in.

## Outputs

In `feedback/<slug>/`, next to `kickoff/`. The script writes both; never write or edit them by hand.

- `<date>-feedback.md`, where `<date>` is the date the client wrote (`YYYY-MM-DD`):
  - Header lines `Client:`, `Date:`, `From:` (the feedback file name) and `Scope source:`.
  - `## Summary`: item counts by type, what was approved, scope requests by verdict, and the updates file.
  - `## Feedback Items`: one table `| # | Feedback | Type | Affects | Impact | Action | Owner |`. Feedback is a verbatim quote; Type is `content`, `design`, `scope`, `question` or `approval`; Affects starts with `homepage copy`, `homepage design`, `site scope`, `client context`, `timeline`, `platform access`, `intake items` or `other` (a detail may follow a colon, `homepage design: Option B`); Impact is `none`, `low`, `medium` or `high`; Owner is `AM`, `Content`, `Design`, `SEO` or `Dev`.
  - `## Scope Check`: one line per scope row with its verdict (`outside scope`, `to confirm` or `within scope`) against the scope source, or `- No scope requests.`
  - `## Reply Draft`: `Subject:` line, the email, then the AM's name and `Account Manager, WISE Digital Partners`.
- `<date>-feedback-updates.md`, only when the client stated facts: client-context-update's updates format (`Client:`, `Source: client`, `Date:`, `From:`, `## Updates`, then `| # | Section | Fact | Evidence |`). With no facts, no file. `feedback.py updates-json` prints the same rows as JSON with the keys `Client`, `Source`, `Date`, `From` and `rows` (the contract with client-context-update).

A second, different email on the same date gets `<date>-2-feedback.md`; rerunning the same email overwrites its own files.

## Steps

Run the script by its path inside this skill's folder (`<skill-dir>` is the folder holding this SKILL.md), as one plain `python3` command with paths as arguments. Keep each call a single command: no `&&`, `|` or `cd`. A denied call gets retried once exactly as it was; the files the script writes are never typed by hand instead.

1. **Read** the whole feedback file, `<slug>-context.md` and `<slug>-missing-items.md`. Then get the scope source: `python3 <skill-dir>/scripts/feedback.py scope kickoff/<slug>`.
2. **Sort and decide.** Read [Sorting Rules](references/sorting-rules.md) and split the client's text into items, pick each one's type, affects, impact, action and owner, judge every scope request, and pick out the facts for the context.
3. **Draft the reply.** Read [Reply Voice](references/reply-voice.md) and write the reply body.
4. **Write the plan** as `feedback-plan.json` in the working directory, in the shape given in Sorting Rules.
5. **Dry run:** `python3 <skill-dir>/scripts/feedback.py render kickoff/<slug> --feedback <feedback file> --plan feedback-plan.json --dry-run`. Each line under `PLAN REJECTED` names a problem in the plan; correct the plan and dry-run again until you see `PLAN OK`.
6. **Render:** the same command without `--dry-run`. It writes the files and runs the check. On `RESULT: FAIL`, fix the plan and render again.

## Answer

In chat: the files written; a short list of the items by owner; each scope request with its verdict; the facts going to the context and the line `run client-context-update with <updates file>` when there is one; any login or password the client sent, by kind only, with a note that the AM should ask them to change it; the reply draft as written; and the checker table with its `RESULT:` line.

## Boundaries

- Never agree to pages or deliverables beyond the scope source; the AM settles those with a change order.
- Never copy a password, username, PIN or code anywhere, including the chat answer.
- No fact, number, date or promise the client's text, the kickoff folder or the user does not give.
- This skill drafts; the AM sends. It does not edit the copy or designs, update the context, or create tasks.
