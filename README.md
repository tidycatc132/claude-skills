# Skills Harness Kit

A harness for a Claude Code project whose product is **skills**. The model writes the skills; this repo supplies the guides (what to do) and sensors (proof it worked) so that "done" is decided by evidence, not by the model's confidence.

> Agent = Model + Harness. Guides steer before the agent acts; sensors check after and feed the result back.

## Quick start

```bash
cd skills-harness-kit
git init && git add -A && git commit -m "Harness baseline"   # freezes evals, scripts, .claude/
bash init.sh                                                  # must print GREEN
claude                                                        # open Claude Code here
# then:  /new-skill <what the skill should do>    (or /next-skill for a backlog item)
```

Requirements: Python 3.9+, git, the `claude` CLI (only for the real eval runners). The hooks call `python3`; on Windows, change the command name in `.claude/settings.json` if your interpreter is `python`/`py`.

Commit the baseline first: the "frozen once committed" rules are based on git, so nothing is frozen until it is tracked.

## Layout

| Path | Role |
|---|---|
| `CLAUDE.md` | Short rules (advisory guide) |
| `skills/<name>/` | The product |
| `skills_backlog.json` | Optional list of planned skills; model may only change `passes` and `notes`. Ad hoc skills use `/new-skill` and skip it |
| `progress.md`, `failure_log.md` | Session memory and the steering-loop log |
| `evals/<name>/` | `trigger.json`, `outputs.json`, `golden/` |
| `contracts/`, `fixtures/` | Machine-checked interfaces between pipeline skills, and their test data |
| `scripts/` | Sensors (validator, contracts, overlap, backlog, eval runners, packager, selftest) |
| `.claude/settings.json`, `hooks/` | Deterministic enforcement |
| `.claude/agents/skill-reviewer.md` | Read-only reviewer subagent |
| `.claude/commands/` | `/new-skill`, `/next-skill`, `/verify-skill`, `/log-failure` |
| `init.sh`, `Makefile` | Session-start ritual and shortcuts |

## Guides and sensors

| Guide (feedforward) | Sensor (feedback) |
|---|---|
| `CLAUDE.md` rules | `validate_skill.py --strict`: name, description, size, paths, syntax, placeholders, evals present |
| Backlog with archetypes and dependencies | `check_backlog.py`: schema, immutable fields, verifies every `passes: true` claim |
| Contract JSON for pipeline interfaces | `check_contracts.py`: fixture shape, doc/contract column sync, optional producer/consumer commands |
| Boundary sentence in descriptions | `check_overlap.py`: lexical collision check across all skills |
| Evals written before the skill | `run_trigger_evals.py`: does Claude actually invoke the skill? |
| Fixtures | `run_output_evals.py`: deterministic assertions plus optional LLM judge |
| Hooks | `selftest.py`: proves each sensor fires on known-bad input |

## Hooks

| Event | Script | Behavior |
|---|---|---|
| SessionStart | `session_brief.py` | Injects progress, backlog status, next skill |
| PreToolUse | `protect_paths.py` | Blocks edits to frozen files (committed evals, fixtures, contracts, scripts, `.claude/`) and Bash writes to them |
| PostToolUse | `post_edit_check.py` | Validates a skill right after it is edited and returns findings to Claude |
| Stop | `stop_gate.py` | Blocks finishing while gates are red; gives up after 2 blocks (`HARNESS_MAX_STOP_BLOCKS`) and writes to `failure_log.md`; also blocks if protected files were tampered with |

Human override: create an empty `.harness-unlock` file to let edits to frozen files through; delete it afterwards. It is git-ignored.

## Gates

```bash
make check      # validator --strict, contracts, overlap, backlog   (what the Stop hook runs)
make selftest   # 118 mutation checks on the sensors themselves
make golden     # offline assertions against recorded outputs (free)
make triggers   # real routing evals (needs claude CLI, costs tokens)
make outputs    # real output evals with LLM judge (costs tokens)
make package    # deterministic dist/<name>.zip and .skill for skills that pass
```

## Eval formats

`evals/<skill>/trigger.json`
```json
{ "should_trigger": ["prompt", "..."], "should_not_trigger": ["prompt", "..."] }
```
Strict validation wants at least 4 of each. Runs happen in a sandbox containing all skills; a trigger is a `Skill` tool call naming the skill.

`evals/<skill>/outputs.json`: cases with `prompt`, `fixtures` (`src`, `dest`) and `assertions`. Types: `file_exists`, `file_absent`, `contains`, `not_contains`, `regex`, `not_regex`, `max_words`, `min_words`, `max_lines`, `csv_columns`, `csv_min_rows`, `csv_enum`, `csv_no_empty`, `json_valid`, `json_has_keys`, `rubric` (judge, only with `--judge`).

## The steering loop

1. Something goes wrong.
2. `/log-failure` records it with a root cause.
3. Seen once: a note. Seen twice: add a control, preferring in this order: validator rule, contract assertion, eval case, hook, and last a line in `CLAUDE.md`.
4. Add a selftest case so the new control is itself tested.
5. Periodically remove controls that no longer catch anything; model improvements make some obsolete.

## Make it yours

1. Delete `skills/example-*`, `evals/example-*`, `fixtures/example-*`, `contracts/topic-map-to-brief.json`, `fixtures/contracts/`, and the example `evals/*/golden/`.
2. Replace the entries in `skills_backlog.json`. Archetypes and `depends_on` are yours to define. `example-article-outline` is a todo placeholder; delete it.
3. Edit the rules in `CLAUDE.md` to your domain (keep it short).
4. Run `make selftest`; some selftests reference the examples and should be adjusted or removed with them.
5. Re-commit the baseline.

## Honest limitations

- **Hooks are guardrails, not security.** A determined agent with shell access can route around them. For harder limits add `permissions.deny` rules in `.claude/settings.json`.
- **Overlap check is lexical.** It catches structural collisions, not semantic ones. Trigger evals are the real test.
- **Evals cost tokens and need `claude` authenticated.** Headless flags were verified against Claude Code 2.1.295; check `claude --help` if they change.
- **Model sensitivity.** In testing, Haiku under-triggered the example skill (82%) where Sonnet passed 11/11. Run trigger evals with the model you ship on. Fix misses by improving the description, not the evals.
- **Eval prompts that reference files not present** can make the model ask a question instead of invoking the skill. Ship fixtures with the prompt or make it self-contained.
- **Goldens shipped here are synthetic** (see `evals/GOLDEN.md`). Re-record with `--record` after reviewing a real run.
- **The LLM judge is another model.** Treat rubric checks as signal, not proof; keep deterministic assertions wherever possible.
- **Tested here:** selftest 118/118; offline golden evals; real PreToolUse, PostToolUse and Stop hook runs in Claude Code; real headless trigger evals. Not tested live: `run_output_evals.py` against a model with `--judge`/`--record`, and the slash commands in an interactive session.
- **Harness assumptions go stale.** Re-evaluate the controls when you move to a newer model.
