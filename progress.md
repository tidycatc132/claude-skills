# Progress log

Newest entries at the bottom. One entry per session: what shipped, what was hard, what the next session must know.

## 2026-10-09 Harness reoriented: no backlog, fresh skills only
- Removed the kit's example skills, their evals, fixtures and contract, and the `/next-skill` command. `skills_backlog.json` is now an empty list that the scripts still read; nothing is planned there.
- `scripts/selftest.py` generates its own synthetic skill pair, so the harness self-test runs on an empty `skills/`.
- Every skill now starts with `/new-skill <description>`. Sibling skills are read only for their `description` line, to write the boundary sentence.
- Next: build the first real skill with `/new-skill`. Expect `/verify-skill` to spend tokens on real trigger and output evals.
