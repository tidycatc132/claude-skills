---
description: Build one brand-new skill from a plain-language description, with no backlog entry needed
argument-hint: "<what the skill should do>"
---

You are building ONE new skill this session from the description in $ARGUMENTS. Every skill starts from scratch: there is no backlog and no template skill to copy.

## 1. Bearings
- Run `bash init.sh`. If anything is red before you start, report or fix that first.
- Read `progress.md` (last entries) and `failure_log.md` (open items).
- Read the `description` lines of existing skills in `skills/` only to avoid overlap and to write the boundary sentence; do not copy their structure, wording or steps.
- If $ARGUMENTS is empty or too vague to write 8 realistic test prompts from, ask the user ONE short question and stop. Otherwise do not ask; take the most reasonable reading and say which one you took.

## 2. Interface and evals FIRST
- Pick a kebab-case id (max 64 chars, no "claude" or "anthropic"). Stop if `skills/<id>/` already exists.
- State the input and output exactly (file names, columns, enums) in backticks.
- If the skill consumes or produces another skill's files, add `contracts/<a>-to-<b>.json` plus a fixture in `fixtures/contracts/`.
- Write `evals/<id>/trigger.json` (4+ should, 4+ should-not, including near-neighbours that belong to other skills) and `evals/<id>/outputs.json` (at least one case with computational assertions), plus fixtures in `fixtures/<id>/`.

## 3. Write the skill
- `skills/<id>/SKILL.md` with `name` (= folder), `description` (what it does, "Use when...", "Do NOT use for X (use sibling)" when a sibling exists), lean body. Detail in `references/`, deterministic work in `scripts/`.
- Hooks validate each edit. Read their messages and fix; do not argue with them.

## 4. Gates (all green)
```
python3 scripts/validate_skill.py <id> --strict
python3 scripts/check_contracts.py --all
python3 scripts/check_overlap.py
```
Then run `/verify-skill <id>`. Structure alone is not done.

## 5. Close out
- Append a dated entry to `progress.md` (what shipped, what was hard, what a future session must know).
- `python3 scripts/package_skill.py <id>` to confirm it packages.
- Commit once, message naming the skill. Stop after one skill.

## Hard rules
- Never edit committed evals, fixtures, contracts, scripts or `.claude/` to make something pass. If one looks wrong, stop and tell the user exactly what and why.
- Never claim an eval passed that did not run.
- If a gate keeps failing for a reason you do not understand, run `/log-failure` and ask the user. Do not weaken the gate.
