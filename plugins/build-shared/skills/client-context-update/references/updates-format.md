# Updates file format

Skills that collect client facts later in Week 1 hand them to client-context-update in this format, so the merge rules live in one place. kickoff-call-processing writes `kickoff/<slug>/<slug>-call-updates.md` (`Source: call`); client-feedback writes `feedback/<slug>/<date>-feedback-updates.md` (`Source: client`).

```
Client: <Client Name>
Source: call
Date: 2026-11-10
From: kickoff-call-2026-11-10.txt

## Updates

| # | Section | Fact | Evidence |
|---|---|---|---|
| 1 | Services | Water heater replacement is the service they most want to grow | Owner: "Water heaters are where the margin is, push those." |
| 2 | Platform Access | Google Search Console: confirmed, Dev verified the invite during the call | AM: "Dev just confirmed the Search Console invite works." |
```

- Header lines `Client:`, `Source:` (`call` or `client`), `Date:` (`YYYY-MM-DD`, when it was said) and `From:` (the file the facts came from), each on its own line.
- One table with the columns `#`, `Section`, `Fact`, `Evidence`, exactly.
- `Section` is a context heading without `## ` (`Snapshot` through `Scope Summary`), or `Platform Access` or `Intake Items` for status news. `Open Items` and `Sources` are never targets.
- `Fact` is one statement in plain words, with no source tag (client-context-update tags it). `Evidence` is a verbatim quote with its speaker, or the line of the email it came from.
- Promises about pages or deliverables go in `Scope Summary` as what was said, never as the new scope.

Check a file with `python3 <skill-dir>/scripts/update_context.py updates <file>` (`UPDATES OK` or `UPDATES INVALID` with the errors); `--json` prints it as JSON with the keys `Client`, `Source`, `Date`, `From`, `rows`.

When the source is an updates file, each row becomes at most one change in the plan; the merge rules decide the change type, and a row may become no change when the context already says the same thing with the same source.
