---
name: week-1-handoff-check
description: Go/no-go check that a website build's Week 1 is finished before Week 2. Use when the AM or PM asks for the Week 1 handoff check, a Week 1 readiness check, or whether SEO can start the Growth Blueprint. A script reads the working folder and checks each Week 1 deliverable (context and change log, Kickoff Call outputs, reference kit, keyword research, sitemap within the page cap, homepage brief, homepage copy with editorial sign-off, design brief, Week 1 email), then writes handoff/[slug]/[slug]-week-1-handoff.md with a status per item and a final GO or NO-GO. It does not wait for client feedback. Do NOT use for making any of those files, such as the Day 1 setup (use new-build-kickoff), updating missing items or access (use client-context-update), the Week 1 or Week 2 email (use week-1-client-email or week-2-client-email), sorting client feedback (use client-feedback), judging copy quality (use content-quality-auditor), or ClickUp updates (use clickup-progress-sync).
---

# Week 1 handoff check

The last Week 1 step: confirm every Week 1 file is in the client's working folder and complete, so Week 2 can start without chasing anything. `scripts/handoff_check.py` makes every decision; you run it and report what it found. Never mark an item yourself, and never create, edit or fill in a checked file to turn the result into `GO`.

## Input

The client's working folder, the folder that holds `kickoff/<slug>/` and the other Week 1 folders (`welcome-email/`, `client-reference/`, `research/`, `seo-reports/`, `content/`, `design/`, `emails/`, `feedback/`). Default: the current working folder. `<slug>` is the kickoff folder name. The full item list, where each file is looked for and what makes it complete is in [Checklist](references/checklist.md); read it when a result needs explaining.

Optional, from the user only:
- `--slug <slug>` when there are several kickoff folders.
- `--kit <folder>` when there are several `client-reference/` folders.
- `--content <folder>` when the homepage copy is not in `content/home/`.
- `--date YYYY-MM-DD` for the report's `Checked:` date (default today); `--dry-run` prints the report without writing it.
- `--signoff "<who>, <date>"` when the user says the editor signed off the homepage copy and the design brief does not record it. Pass exactly what they said; never infer a sign-off.

## Output

`handoff/<slug>/<slug>-week-1-handoff.md`:

```
Client: <Client Name>
Checked: <YYYY-MM-DD>

# Week 1 handoff check for <Client Name>

| Item | Required | Status | Path | Note |
|---|---|---|---|---|
...
## Blocking
## Not blocking

GO          (or NO-GO)
```

`Required` is `yes` or `no`. `Status` is `present`, `missing` (absent or incomplete; the note says what is lacking), `stale` (there, but out of date against a file it depends on) or `n/a`. The last line is `GO` when no required item is `missing` or `stale`, else `NO-GO`. Client feedback and platform access are listed but never block.

## Steps

`<skill-dir>` is the folder holding this SKILL.md. Run the script as one plain `python3` command with paths as arguments: no `cd`, `&&` or pipes. If a call is denied, run the same command again on its own; never check the files by hand instead.

1. **Run.** `python3 <skill-dir>/scripts/handoff_check.py run <working-folder> [options]`. It writes the report and prints it; exit 1 means `NO-GO`, which is a result, not an error.
2. If it prints `ERROR` (no kickoff folder, several kickoff or kit folders), report it. For several folders, run again with `--slug` or `--kit` when the user named the client; otherwise ask which one and stop.
3. **Answer** in chat: the report's path, `GO` or `NO-GO`, every blocking item with its owner and the fix the note names (the skill or person that produces it), then the non-blocking items in one line each. For `GO`, say Week 2 can start and name anything still open that the Blueprint team should know (open client flags, access not confirmed, feedback not yet received).

## Boundaries

- The script decides; you do not overrule a status, and you do not soften `NO-GO`.
- The check only reads. It never writes into `kickoff/`, `content/`, `design/` or any other checked folder; its only file is the report under `handoff/`.
- It does not judge the quality of the copy, design or research; those skills' own checks did that when the files were made.
