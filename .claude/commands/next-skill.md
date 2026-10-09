---
description: Build the next skill from the backlog, one skill per session, gated by evidence
argument-hint: "[skill-id to build instead of the next one]"
---

You are building ONE skill this session. Follow the loop exactly.

## 1. Get your bearings (do not skip)
- Run `bash init.sh` (validates everything, runs the harness self-test, shows the backlog).
- Read `progress.md` (last entries) and `failure_log.md` (open items).
- Pick the skill: $ARGUMENTS if given, otherwise the output of `python3 scripts/check_backlog.py --next`. If that prints `none`, say so and stop; do not invent work.
- If anything is red before you start, fix or report that first. Never build on a broken base.

## 2. Plan the skill's interface BEFORE writing it
- Read the backlog entry, the sibling skills' `description` lines, and `CLAUDE.md`.
- If the skill is a pipeline stage, write down its input and output format exactly (column names, file names, enums). If it connects to another skill, add a contract in `contracts/` plus a frozen fixture in `fixtures/contracts/`. New contract files are allowed; existing committed ones are frozen.
- Write the evals FIRST: `evals/<id>/trigger.json` (4+ should, 4+ should-not including near-neighbour prompts that belong to siblings) and `evals/<id>/outputs.json` (at least one case with computational assertions). Fixtures go in `fixtures/<id>/`.

## 3. Write the skill
- `skills/<id>/SKILL.md` with frontmatter `name` (= folder name), `description` (what it does, "Use when...", "Do NOT use for X (use sibling)"), and a lean body. Put detail in `references/`, deterministic work in `scripts/`.
- Hooks validate each edit. Read their messages and fix; do not argue with them.

## 4. Gates (all must be green)
```
python3 scripts/validate_skill.py <id> --strict
python3 scripts/check_contracts.py --skill <id>
python3 scripts/check_overlap.py
```
Then behavior: run `/verify-skill <id>`. A skill is not done on structure alone.

## 5. Close out
- Set `"passes": true` for the skill in `skills_backlog.json` (change nothing else; add a short `notes` if useful).
- Append a dated entry to `progress.md`: what shipped, what was hard, anything the next session must know.
- `python3 scripts/package_skill.py <id>` to confirm it packages.
- Commit once, with a descriptive message. Stop after one skill.

## Hard rules
- Never edit committed evals, fixtures, contracts, scripts or `.claude/` to make something pass. If you believe one is wrong, stop and tell the user exactly what and why.
- If a gate keeps failing for a reason you do not understand, run `/log-failure` and ask the user. Do not weaken the gate.
