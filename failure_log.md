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
