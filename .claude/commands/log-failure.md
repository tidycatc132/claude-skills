---
description: Log a repeated agent failure and turn it into a harness control (the steering loop)
argument-hint: "<what went wrong>"
---

Something went wrong that may happen again: $ARGUMENTS

1. Append an entry to `failure_log.md` using the template at the top of that file: date, what happened, which skill, the root cause (guide missing? sensor missing? sensor too weak? model assumption gone stale?), and the evidence (command output, diff, prompt).
2. Check the log for the same root cause recorded before. A failure seen once is a note; a failure seen twice is a missing control.
3. If it is the second occurrence, propose the cheapest control that would have prevented or caught it, in this order of preference:
   - a deterministic check (validator rule, contract assertion, eval assertion) over
   - a hook over
   - a line in `CLAUDE.md` over
   - more prose in a skill.
4. Do NOT implement controls that live in frozen paths (`scripts/`, `.claude/`, committed `evals/`, `contracts/`). Write the proposal in the log entry (exact rule, exact file) and tell the user, who will unlock and approve it.
5. You may add a line to `CLAUDE.md` yourself if the control is guidance. Keep CLAUDE.md under 60 lines: remove or merge a line when you add one.
