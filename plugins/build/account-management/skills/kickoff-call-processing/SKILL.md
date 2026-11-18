---
name: kickoff-call-processing
description: Turns a new-build client's Kickoff Call (orientation call) transcript into the Blueprint inputs. Use when a Kickoff Call transcript needs processing after the call, for example "process the kickoff call transcript for [client]", "write the Blueprint Input Package", "pull the quote bank from the call" or "did the AM promise more than the SOW on the call". Writes the call-updates file for client-context-update, the Blueprint Input Package SEO starts the Growth Blueprint from (services priority, audiences, area tiers, voice, competitors, topics, scope) and a verbatim client quote bank, and flags any page count or deliverable said on the call that differs from the scope source as a CONFLICT while the scope source still wins. Do NOT use for merging a finished call-updates file or intake form into the context (use client-context-update), the Day 1 kickoff files (use new-build-kickoff), brand, voice or audience files (use client-reference-kit), or the AM's brief before the call (use kickoff-call-brief).
---

# Kickoff Call Processing

After the Kickoff Call, three things have to leave the transcript: facts for the client context, a handoff SEO can plan from, and the client's own words. Judging what the call said is your job, captured in one JSON plan. The script `scripts/process_call.py` holds the plan to the transcript (every quote word for word, every timestamp real), decides which page counts and deliverables clash with the scope source, and renders the files. Finish only on `RESULT: PASS` from its check.

## Inputs

- The call transcript, as a text file: Dialpad, Zoom, Otter or similar, with a timestamp and a speaker on each turn. A summary the tool added at the end (a `---` line, "Dialpad AI Summary") is not evidence and is ignored.
- The client's kickoff folder `kickoff/<slug>/` from new-build-kickoff, holding at least `<slug>-context.md` (its `Client:` line and the `SOW pages:` and `Included services:` lines of `## Scope Summary` are read). If the context does not exist, say new-build-kickoff runs first and stop without writing anything.
- Read `<slug>-gap-questions.md` and, if present, `<slug>-missing-items.md` and `<slug>-kickoff-call-brief.md` too: they say what the call was meant to settle.

## Outputs

All in `kickoff/<slug>/`. The script writes them; never write or edit them by hand.

- `<slug>-call-updates.md`: client-context-update's input format. Header lines `Client:`, `Source: call`, `Date:` (the call date, `YYYY-MM-DD`), `From:` (the transcript file name), a `## Updates` heading, then one table `| # | Section | Fact | Evidence |`. `Section` is a context heading (`Snapshot` through `Scope Summary`), `Platform Access` or `Intake Items`; Evidence is `Speaker (HH:MM:SS): "verbatim quote"`. Scope conflicts are `Scope Summary` rows whose Fact starts `CONFLICT:`.
- `<slug>-blueprint-input-package.md`: header lines `Client:`, `Call date:`, `From:`, `Scope source:`, then the sections `## Services Priority`, `## Audiences`, `## Service Area Tiers`, `## Voice and Design Direction`, `## Competitors`, `## Topics to Own`, `## Goals and Success Measures`, `## Scope Decisions`, `## Open Items`, in that order. Every bullet ends `(HH:MM:SS) [call]`; `## Scope Decisions` opens with the context's `SOW pages:` and `Included services:` lines and then each `CONFLICT:` (or a line saying there is none).
- `<slug>-quote-bank.md`: header lines `Client:`, `Call date:`, `From:` and `Agency speakers:`, then `| # | Quote | Speaker | Timestamp | Use for |` with 8 to 12 client quotes, verbatim, `Timestamp` as `HH:MM:SS`, `Use for` from the fixed list in the rules.

The script never changes `<slug>-context.md`, the change log or the missing items; client-context-update does that from the call-updates file.

## Steps

Paths are relative to the working directory; `<skill-dir>` means this skill's folder. Each script call is a single bare command, `python3 <skill-dir>/scripts/process_call.py <subcommand> ...`, on a line of its own: no `cd`, no `&&`, no pipes, since the sandbox allows plain `python3` calls only. A refused call usually means something was chained to it; issue the bare command alone. The script is the only writer of the three files.

1. **Parse.** `python3 <skill-dir>/scripts/process_call.py transcript <transcript> --turns`. It prints the turns with their timestamps, the speakers, the call date if the transcript or its file name has one, and every page-count mention. If it prints `TRANSCRIPT UNREADABLE`, say which formats it accepts and stop. If no date is found, use the date the user gave, else today's date, and say which.
2. **Read** the context, the gap questions and any missing items or call brief, then the whole transcript.
3. **Decide and write the plan.** Read [Processing Rules](references/processing-rules.md) first. Write `call-processing-plan.json` in the working directory (not inside `kickoff/`): the update rows, the package bullets, the quotes, a classification of every page-count mention, and every deliverable promised or agreed on the call.
4. **Dry run.** `python3 <skill-dir>/scripts/process_call.py build kickoff/<slug> --transcript <transcript> --plan call-processing-plan.json --dry-run`. Fix every line under `PLAN REJECTED` in the plan (most often a quote that is not word for word) and rerun until it prints `PLAN OK`.
5. **Build.** The same command without `--dry-run`. It writes the three files and runs the check. If the check fails, fix the plan and build again; `python3 <skill-dir>/scripts/process_call.py check kickoff/<slug> --transcript <transcript> --plan call-processing-plan.json` reruns only the check.

## Answer

In chat give: the three files written; each `CONFLICT:` in full, with who said it and that the build follows the scope source until a signed change; a short summary of the package (top services, core and secondary areas, voice, competitors, topics to own); what the call left open; the checker table with its `RESULT:` line; and the next step, in these words or close: "Next, run client-context-update on `kickoff/<slug>/<slug>-call-updates.md` to merge the call into the client context and refresh the missing items."
