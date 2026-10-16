# Failure log (the steering loop)

A failure seen once is a note. A failure seen twice is a missing control: add a validator rule, a contract assertion, an eval case, a hook, or (last resort) a line in CLAUDE.md. Keep entries short.

Template:

```
## YYYY-MM-DD <skill-id> - <one-line symptom>
- What happened:
- Root cause: missing guide | missing sensor | sensor too weak | stale model assumption | spec was vague
- Evidence: <command output, diff, prompt>
- Control added or proposed: <exact rule and file> (status: proposed | approved | done)
```

## Entries

(none yet)

## 2026-10-12 clickup-progress-sync - SKILL.md frontmatter rejected by a strict YAML parser
- What happened: the `description` contained `reflect it: "update ClickUp with this"`. The harness's own `parse_frontmatter` accepted it and every gate passed, but a real YAML parser (where the skill is loaded) fails with "mapping values are not allowed in this context at line 2 column 571". User reported it after merge.
- Root cause: sensor too weak. `validate_skill.py` checks the description for length and angle brackets but not for YAML-breaking sequences (`: ` or ` #` inside an unquoted scalar, or a leading quote/bracket).
- Evidence: `python3 -c "import re;l=open('skills/clickup-progress-sync/SKILL.md').read().splitlines()[2];print([m.start()+1 for m in re.finditer(': ',l)])"` printed `[12, 571]` before the fix.
- Control added or proposed: add to `validate_skill.py` an error when any frontmatter value contains `: ` or ` #` or starts with a YAML indicator character, and a selftest case for it (status: proposed; scripts/ is frozen, so this needs the user to approve the edit). Until then: never write `: ` inside a description; use a comma or "for example".

## 2026-10-12 technical-seo-checker - output eval wrote no files after a denied chained Bash call (second occurrence of the seo-drift-monitor failure)
- What happened: the model explored with `ls -la && ls pages | head` and a `for` loop, both denied by the sandbox allow-list, then wrote "Bash was denied in this session" and never ran the plain `python3 scripts/audit_pages.py ...` command or wrote the report. Same class of failure as the 2026-10-12 seo-drift-monitor entry in progress.md.
- Root cause: missing guide (the rule lived in SKILL.md but after the workflow steps) and missing sensor (nothing checks that a skill with scripts/ carries the rule).
- Evidence: kept sandbox trace, TOOL Bash `{"command": "ls -la && ls pages | head -50"}` followed by no python3 call; final text "The deterministic scripts did not run. Bash was denied".
- Control added or proposed: all five new skills now say to retry the plain python3 command after a denial. Proposed sensor for `validate_skill.py`: warn when a skill has `scripts/*.py` and SKILL.md does not mention running them as a plain `python3` command (status: proposed; scripts/ is frozen).

## 2026-10-14 client-reference-kit - output eval could not run any script on Windows (third occurrence of the script-denial class)
- What happened: in the eval sandbox the model wrote all five files but every `python3` and `python` call was refused, so it hand-checked the kit and wrote its own summary table; the stdout table assertion failed.
- Root cause: stale model assumption in the harness. On this win32 machine the `claude` CLI exposes a PowerShell tool and no Bash tool, so `evalkit.DEFAULT_ALLOWED` (`Bash(python3 *)` only) never matches. Reproduced with a bare `claude -p "run python3 --version"` using the same flags: "Permission to use PowerShell has been denied because Claude Code is running in don't ask mode."
- Evidence: recorded stdout of kineticpath-full-kit (inspected, then deleted), and the bare reproduction above.
- Control added or proposed: client-reference-kit's outputs.json sets per-case `allowed_tools` with `PowerShell(python3 *)` added (done). Proposed for `scripts/evalkit.py`: add `PowerShell(python3 *)` to `DEFAULT_ALLOWED` so every skill's evals can run scripts on Windows (status: done 2026-10-14, user-approved harness edit; see progress.md). Also: run evals with the real interpreter first on PATH (`/c/Users/hello/AppData/Local/Python/bin`), since `python3` otherwise resolves to the Windows Store stub.
- Closed 2026-10-14: `DEFAULT_ALLOWED` now carries `PowerShell(...)` twins of every `Bash(...)` rule; a bare `claude -p` reproduction ran `python3 --version` with it and was denied without it. Per-case `allowed_tools` overrides are no longer needed for new skills.

## 2026-10-15 seo-content-writer - rubric judge flips verdicts on long multi-item criteria
- What happened: across ~20 judged runs the "every heading opener is a direct answer" criterion failed every time, on a different heading each run, including openers earlier runs called fine; several verdicts said "criterion 1 is met... criterion 2 is met" or "minor and arguably acceptable" and still FAILed; two returned invalid JSON. A criterion asking the judge to compare numbers with the brief failed with "the evidence pack is not provided", because the judge sees only the rubric's target file. A later run rejected a source the criterion explicitly allowed.
- Root cause: sensor too weak / too noisy. One tool-less judge pass over a long document with an "every X" criterion has a high false-fail rate, and rubric criteria that reference files other than `target` cannot be judged.
- Evidence: run outputs in this session (harborpine-full-brief, cedarline-thin-ymyl-brief), e.g. "the brief's evidence pack is not provided, so it cannot be confirmed"; "Criterion 1 is met ... Criterion 2 is met" followed by FAIL.
- Control added or proposed: (done) express per-item rules as script checks and assert the `qa_report.md` rows with regex; keep rubrics for whole-document judgments and write criteria verifiable from the target file alone. (done 2026-10-16, user-approved) `run_output_evals.py --judge-runs N` majority vote, and a rubric `context` list for reference files; see progress.md.
- Update 2026-10-16: after the two most frequent judge complaints (figure sourced only in the next sentence; "The difference is..." naming neither side) became `check_draft.py` checks, the plumbing and HELOC rubrics both passed. Pattern worth repeating: when a judge keeps failing the same kind of sentence, turn that kind into a script check and keep the rubric for the rest.
