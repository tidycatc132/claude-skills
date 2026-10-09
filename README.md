# Skills harness

A harness for a Claude Code project whose product is **skills**. The model writes the skills; this repo supplies the guides (what to do) and sensors (proof it worked) so that "done" is decided by evidence, not by the model's confidence.

> Agent = Model + Harness. Guides steer before the agent acts; sensors check after and feed the result back.

There is no backlog and no template skill. Every skill is built from scratch, one per session, from a plain-language description.

## Quick start

```bash
cd claude-skills
bash init.sh                                                  # must print GREEN
claude                                                        # open Claude Code here
# then:  /new-skill <what the skill should do>
```

Requirements: Python 3.9+, git, the `claude` CLI (only for the real eval runners). The hooks call `python3`; on Windows, change the command name in `.claude/settings.json` if your interpreter is `python`/`py`.

The "frozen once committed" rules are based on git, so an eval, fixture or contract is only frozen once it is tracked.

## Layout

| Path | Role |
|---|---|
| `CLAUDE.md` | Short rules (advisory guide) |
| `skills/<name>/` | The product |
| `evals/<name>/` | `trigger.json`, `outputs.json`, optional `golden/` |
| `contracts/`, `fixtures/` | Machine-checked interfaces between pipeline skills, and their test data |
| `skills_backlog.json` | Kept as an empty list; the scripts read it but nothing is planned there |
| `progress.md`, `failure_log.md` | Session memory and the steering-loop log |
| `scripts/` | Sensors (validator, contracts, overlap, eval runners, packager, selftest) |
| `.claude/settings.json`, `hooks/` | Deterministic enforcement |
| `.claude/agents/skill-reviewer.md` | Read-only reviewer subagent |
| `.claude/commands/` | `/new-skill`, `/verify-skill`, `/log-failure` |
| `init.sh`, `Makefile` | Session-start ritual and shortcuts |

## The loop

1. `/new-skill <description>` picks an id, states the interface, and writes the evals (trigger prompts, output assertions, fixtures, a contract if the skill chains to another) before any skill text.
2. The skill is written. Hooks validate each edit.
3. Cheap gates: strict validator, contracts, overlap. Then `/verify-skill <id>`: real trigger evals, real output evals, an independent reviewer subagent.
4. A dated entry goes in `progress.md`, the skill is packaged, and the work is committed. One skill per session.

Sibling skills are read only for their `description` line, to write the "Do NOT use for X (use other-skill)" boundary. Nothing else is copied from them.

## Guides and sensors

| Guide (feedforward) | Sensor (feedback) |
|---|---|
| `CLAUDE.md` rules | `validate_skill.py --strict`: name, description, size, paths, syntax, placeholders, evals present |
| Contract JSON for pipeline interfaces | `check_contracts.py`: fixture shape, doc/contract column sync, optional producer/consumer commands |
| Boundary sentence in descriptions | `check_overlap.py`: lexical collision check across all skills |
| Evals written before the skill | `run_trigger_evals.py`: does Claude actually invoke the skill? |
| Fixtures | `run_output_evals.py`: deterministic assertions plus optional LLM judge |
| Hooks | `selftest.py`: proves each sensor fires on known-bad input, using a synthetic skill pair it generates itself |

## Hooks

| Event | Script | Behavior |
|---|---|---|
| SessionStart | `session_brief.py` | Injects the rules, the skills on disk, anything red, and the tail of `progress.md` |
| PreToolUse | `protect_paths.py` | Blocks edits to frozen files (committed evals, fixtures, contracts, scripts, `.claude/`) and Bash writes to them |
| PostToolUse | `post_edit_check.py` | Validates a skill right after it is edited and returns findings to Claude |
| Stop | `stop_gate.py` | Blocks finishing while gates are red; gives up after 2 blocks (`HARNESS_MAX_STOP_BLOCKS`) and writes to `failure_log.md`; also blocks if protected files were tampered with |

Human override: create an empty `.harness-unlock` file to let edits to frozen files through; delete it afterwards. It is git-ignored.

## Gates

```bash
make check      # validator --strict, contracts, overlap, backlog sentinel   (what the Stop hook runs)
make selftest   # mutation checks on the sensors themselves
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
Strict validation wants at least 4 of each. Runs happen in a sandbox containing all skills in this repo (and nothing from the user's plugins); a trigger is a `Skill` tool call naming the skill.

`evals/<skill>/outputs.json`: cases with `prompt`, `fixtures` (`src`, `dest`) and `assertions`. Types: `file_exists`, `file_absent`, `contains`, `not_contains`, `regex`, `not_regex`, `max_words`, `min_words`, `max_lines`, `csv_columns`, `csv_min_rows`, `csv_enum`, `csv_no_empty`, `json_valid`, `json_has_keys`, `rubric` (judge, only with `--judge`).

`evals/<skill>/golden/<case-id>/`: approved outputs, recorded with `--record` after a human reviews a real run. See `evals/GOLDEN.md`.

## The steering loop

1. Something goes wrong.
2. `/log-failure` records it with a root cause.
3. Seen once: a note. Seen twice: add a control, preferring in this order: validator rule, contract assertion, eval case, hook, and last a line in `CLAUDE.md`.
4. Add a selftest case so the new control is itself tested.
5. Periodically remove controls that no longer catch anything; model improvements make some obsolete.

## Honest limitations

- **Hooks are guardrails, not security.** A determined agent with shell access can route around them. For harder limits add `permissions.deny` rules in `.claude/settings.json`.
- **Overlap check is lexical.** It catches structural collisions, not semantic ones. Trigger evals are the real test.
- **Evals cost tokens and need `claude` authenticated.** Headless flags were verified against Claude Code 2.1.295; check `claude --help` if they change.
- **Model sensitivity.** Smaller models under-trigger where larger ones pass. Run trigger evals with the model you ship on. Fix misses by improving the description, not the evals.
- **Eval prompts that reference files not present** can make the model ask a question instead of invoking the skill. Ship fixtures with the prompt or make it self-contained.
- **The LLM judge is another model.** Treat rubric checks as signal, not proof; keep deterministic assertions wherever possible.
- **Harness assumptions go stale.** Re-evaluate the controls when you move to a newer model.
