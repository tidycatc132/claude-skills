# Skills factory

This repo builds Claude skills. It is a harness: scripts and hooks check your work, and evidence (not your confidence) decides when a skill is done. Build ONE skill per session.

## Layout
- `skills/<name>/SKILL.md` (+ `references/`, `scripts/`, `assets/`): the product.
- `evals/<name>/trigger.json`, `outputs.json`, `fixtures/`, `contracts/`: the definition of "correct". Add new ones freely; once committed they are frozen.
- `skills_backlog.json`: what to build. You may only change `passes` and `notes`.
- `progress.md`, `failure_log.md`: session memory. Read them first, append to them last.
- `scripts/`, `.claude/`: the harness itself. Frozen.

## Skill rules (every one is checked by a script)
- `name` is kebab-case, equals the folder name, max 64 chars, never contains "claude" or "anthropic".
- `description` is max 1024 chars, no angle brackets. It says what the skill does, when to use it ("Use when..."), and what it is NOT for, naming the sibling skill that owns that job ("Do NOT use for X (use other-skill)").
- Keep SKILL.md under 400 lines. Put detail in `references/` and say in SKILL.md when to load each file.
- No hard-coded absolute paths (`/mnt/...`, `/home/...`, `/Users/...`). Use paths relative to the skill folder or the working directory.
- Deterministic work goes in `scripts/`, not in prose. Prefer the standard library.
- Pipeline skills state their input and output formats exactly, with column and file names in backticks, and have a contract in `contracts/`.
- No TODO/FIXME/TBD in anything shipped.

## Workflow
- Start with `bash init.sh`. Then `/new-skill <description>` for a fresh skill (no backlog needed) or `/next-skill` for a backlog item. Behavior checks: `/verify-skill <id>`. Repeated failure: `/log-failure`.
- Write the evals before the skill. Describe the interface before the implementation.
- Done means: strict validator, contracts, overlap check and backlog gate are green, `/verify-skill` was run, and the work is committed with a message naming the skill.

## Do not
- Edit committed evals, fixtures, contracts, scripts or `.claude/` to make a check pass. Fix the skill. If a frozen file is wrong, stop and tell the user exactly what and why.
- Set `passes` to true on a skill whose gates you have not run, or claim an eval passed that did not run.
- Add instructions to a skill only to patch a model weakness you have not observed. Every instruction should trace to a failing eval or a documented failure.
- Add a line to this file without removing or merging one. Keep it under 60 lines.
