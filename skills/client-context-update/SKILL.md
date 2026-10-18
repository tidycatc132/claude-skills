---
name: client-context-update
description: Merges new client information into an existing new-build kickoff client context. Use when an intake form submission (with its GAP Answers), a call-updates file, a feedback-updates file, a pasted client email or a note that platform access arrived needs folding into kickoff/[slug]/[slug]-context.md, for example "merge the intake form into the client context" or "GA access came through, update the missing items". Keeps headings and source tags, adds [intake], [call] and [client] facts, resolves answered GAP bullets, flags conflicts, never deletes a fact, logs every change and rewrites the missing-items Kickoff Call agenda. Do NOT use for the Day 1 kickoff files or gap questions (use new-build-kickoff), the welcome email (use welcome-email), brand, voice or audience files (use client-reference-kit), syncing progress to ClickUp (use clickup-progress-sync), or a raw Kickoff Call transcript, which must first become a call-updates file (use kickoff-call-processing).
---

# Client Context Update

Folds one new source of client information into the kickoff folder that new-build-kickoff wrote. You decide what each new fact means; `scripts/update_context.py` writes the files and checks them. The run is done when it prints `RESULT: PASS`.

## Inputs

- The client's kickoff folder `kickoff/<slug>/`, holding at least `<slug>-context.md` (headings and source tags as new-build-kickoff writes them) and `<slug>-gap-questions.md`. If the context is missing, say new-build-kickoff runs first and stop.
- Exactly one new source, of one of these kinds:
  - `intake`: an intake form submission (ClickUp form fields prefixed `CON`, `NAP`, `ACC`, `BRD`, `CNT`, `GAP`, `PRF`, including the `GAP Answers` field), pasted or as a file.
  - `call`: a `<slug>-call-updates.md` file (written by the planned kickoff-call-processing skill).
  - `client`: a `feedback/<slug>/<date>-feedback-updates.md` file (written by the client-feedback skill), or a client email pasted into chat.
  - `call`: a `<slug>-call-updates.md` file (written by kickoff-call-processing).
  - `client`: a `feedback/<slug>/<date>-feedback-updates.md` file (written by the planned client-feedback skill), or a client email pasted into chat.
  - `user`: a note from the team, typically that platform access arrived ("Dev verified the GA4 invite").

  Updates files follow [Updates Format](references/updates-format.md). A raw call transcript is not a source for this skill; say it must first become a call-updates file in that format. If several sources arrive at once, run the steps once per source, oldest first.

## Output

All in `kickoff/<slug>/`:

- `<slug>-context.md`, updated in place. Same eleven headings (`## Snapshot` through `## Sources`) in the same order; the `SOW pages:`, `Included services:` and quoted scope lines of `## Scope Summary` never change. Every fact bullet still ends with source tags; the new tags are `[intake]`, `[call]`, `[client]` (and `[user]` already exists). A `GAP:` bullet that the source answers becomes a tagged fact; a `CONFLICT:` bullet carries both versions.
- `<slug>-change-log.md`, appended: one table `| Date | Source | Section | Change | Before | After |`, where Change is `added`, `updated`, `resolved-gap` or `conflict`. A replaced fact lives on in the Before column; nothing is deleted without a row.
- `<slug>-missing-items.md`, rewritten: `## Intake Items` (`| Item | Status | Note |`), `## Platform Access` (`| Platform | Status | Note |`) and `## Kickoff Call Agenda`, a numbered list of every intake item still `missing` or `partial` and every platform not yet `confirmed` (or `n/a`).
- `<slug>-gap-questions.md`: answered questions get their `Answer:` line filled in, tagged.
- `history/<slug>-context-NN.md`: the context as it was before each update (the checker compares against these).

## Steps

Work from the working directory. `<skill-dir>` is the folder holding this SKILL.md. Run the script by its path inside this skill's folder, as one plain `python3` command with file paths as arguments: `python3 <skill-dir>/scripts/update_context.py ...`. Never chain, pipe or `cd`. If a Bash call is denied, run the same command again on its own; never stop or hand-write a file the script writes.

1. **Read.** The whole source, then `<slug>-context.md`, `<slug>-gap-questions.md`, and `<slug>-missing-items.md` and `<slug>-change-log.md` if they exist. For an updates file, first run `python3 <skill-dir>/scripts/update_context.py updates <file>`; if it prints `UPDATES INVALID`, report the errors and stop.
2. **Decide each change.** Read [Merge Rules](references/merge-rules.md) before deciding. For every new fact in the source, pick the section and the change type; for every answered gap question, the answer; for intake and access items, the status. Never copy a password, login or secret anywhere, even into a note; if the source contains one, say so in your answer without repeating it.
3. **Write the plan** as `context-update-plan.json` in the working directory (not inside `kickoff/`), in the shape given in Merge Rules.
4. **Dry run.** `python3 <skill-dir>/scripts/update_context.py apply kickoff/<slug> --plan context-update-plan.json --dry-run`. Fix every line under `PLAN REJECTED` in the plan and rerun until it prints `PLAN OK`.
5. **Apply.** The same command without `--dry-run`. It snapshots the context, writes the files and runs the check. If the check fails, run `python3 <skill-dir>/scripts/update_context.py check kickoff/<slug>`, fix the cause, and never edit the context, change log or missing items by hand to make it pass.

## Answer

In chat give: the files updated; the changes as a short list grouped by change type (gaps resolved, conflicts with both versions and which one the build follows, facts updated, facts added); the Kickoff Call agenda from the missing items file; any password or secret you left out (by field name only); and the checker table with its `RESULT:` line.
