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
