---
name: kickoff-call-brief
description: Writes the brief an account manager reads before a new website client's Kickoff Call, once the Day 1 kickoff files already exist. Use when the AM is preparing for the Kickoff Call or kickoff meeting, for example "prep me for the kickoff call" or "what do we still need to settle on the call". Reads the existing kickoff/[slug]/ context, gap questions and missing items and writes [slug]-kickoff-call-brief.md with Call Goals, What We Know, Questions to Settle (every open requirement, unanswered gap question, gap and conflict), Scope to Confirm (page count, scope conflicts, paid media), Access to Confirm, and blank Relationship Notes. Do NOT use to set up a new client or create the Day 1 kickoff files and gap questions from a Sales handoff (use new-build-kickoff), merging intake answers or call notes into the context (use client-context-update), processing the Kickoff Call transcript after the call (planned kickoff-call-processing), the welcome email (use welcome-email), or brand files (use client-reference-kit).
---

# Kickoff Call Brief

One page the AM reads before the client Kickoff Call: what the call must settle, what we already know, and what to confirm. `scripts/kickoff_call_brief.py` lists the open items and checks the brief; you write the wording. The run is done when the check prints `RESULT: PASS`.

## Input

The client's kickoff folder `kickoff/<slug>/`:

- `<slug>-context.md` (required): written by new-build-kickoff, possibly updated by client-context-update. The brief reads its `## Scope Summary` (the `SOW pages:` line), `## Open Items` (one `R` item per bullet), and every `GAP:` and `CONFLICT:` bullet.
- `<slug>-gap-questions.md`: the numbered questions; a question whose `Answer:` line is empty is still open. Its `## Checklist Coverage` table links an `R` item to the question that asked it.
- `<slug>-missing-items.md` (optional): written by client-context-update; its `## Kickoff Call Agenda` lists intake items and platform access not yet in hand, one numbered line each: `N. <item>: <status> (<note>)`. Without it (intake form not merged yet), every intake item and platform is listed as `no record yet`, except `Website login` when the URL inventory is empty (no website) and the three ad platforms when paid media is not in scope.
- `<slug>-paid-media-brief.md` (optional): its presence means paid media is in the signed scope.

If `<slug>-context.md` does not exist, say that new-build-kickoff has to run first and stop; write nothing. The slug is the folder name.

## Output

`kickoff/<slug>/<slug>-kickoff-call-brief.md`, at most 120 lines. The exact layout, with an example, is in [Brief Format](references/brief-format.md); read it before writing. In short:

```
Client: <Client Name>

# Kickoff Call brief for <Client Name>

## Call Goals
## What We Know
## Questions to Settle
## Scope to Confirm
## Access to Confirm
## Relationship Notes
```

Write no other file. Never edit the context, gap questions or missing items; client-context-update owns them.

## Steps

`<skill-dir>` is the folder holding this SKILL.md. Run the script by its path, as one plain `python3` command with the folder as argument; never chain, pipe or `cd`. If a Bash call is denied, run the same command again on its own; never hand-check the brief instead.

1. **List.** `python3 <skill-dir>/scripts/kickoff_call_brief.py items kickoff/<slug>`. It prints the open item groups with their ids (`R4`, `Q1`, `G1`, `C2`) and where each group goes, the two fixed Scope lines, the Access lines and the facts What We Know may quote. If it prints `ERROR`, report it and stop.
2. **Read** the context and gap questions so the wording fits the client.
3. **Write** the brief to [Brief Format](references/brief-format.md): one line per printed group, ids exactly as printed; the Scope and Access lines copied exactly; up to 10 facts copied word for word; up to 5 goals.
4. **Check.** `python3 <skill-dir>/scripts/kickoff_call_brief.py check kickoff/<slug>`. Fix each `FAIL` in the brief and rerun until `RESULT: PASS`.

## Answer

In chat: the brief's path, the number of questions to settle and scope items, whether the access list came from the missing items file or is `no record yet` (then say client-context-update fills it once the intake form is merged), and the checker table with its `RESULT:` line.
