---
name: subagent-performance-review
description: For a managing agent that delegates work to sub-agents and must judge them. Runs a 30-day performance review of one sub-agent from the dispatch log the manager keeps, scores it on four fixed criteria (first-pass acceptance, instruction adherence, efficiency, reliability), reaches one verdict (promote, retain, improvement plan, reassign, merge, replace, or insufficient data), applies that verdict to the sub-agent's definition file at once so no position is left empty, and reports findings and actions to the user. Use when asked to review, evaluate, grade or rate a sub-agent or worker agent, decide whether to keep, retrain, reassign, merge, replace or promote one, put one on a performance improvement plan, or log a finished dispatch for later review. Writes only the local dispatch log. Do NOT use to push or log a sub-agent's progress or outcome into ClickUp or any external tracker (use clickup-progress-sync), to audit a web page or article (use content-quality-auditor), or to review a human employee.
---

# Sub-agent performance review

You are the manager. Sub-agents are definition files (`NAME.md` with `name`, `description`, `tools`, `model` frontmatter and a system-prompt body). Their record is the dispatch log you keep. Every number in the review comes from `scripts/score_review.py`; you write the instructions, not the scores.

## Inputs
- `subagent_dispatch_log.jsonl`, one JSON object per dispatch with `dispatch_id`, `agent`, `dispatched_at`, `task`, `task_type`, `complexity` (1 to 3), `outcome` (`accepted`, `accepted_with_fixes`, `rejected`, `abandoned`, `blocked`), `rework_rounds`, `scope_violations`, `fabrication`, `tool_errors`, `duration_s`, `notes`. Append to it with `python3 scripts/log_dispatch.py` after every delegated task; it also says when a review is due.
- The agents folder, `.claude/agents/` if it exists, else `agents/`, or whatever the user names.
- A review date. Use the date the user gives as `--as-of`; otherwise today.

## Outputs (written next to the log)
- `review_NAME.json` and `review_NAME.md` with a `VERDICT:` line, the four scores, composite, trend, per-task-type table, findings and evidence.
- `review_actions.json`, one entry per action with the files changed, created or retired.
- `pip_NAME.md` when the verdict is an improvement plan.

## Workflow
1. The `scripts/` folder is inside this skill's folder, not the working directory, so pass the script's full path. Run each script as its own plain `python3` command with paths as arguments, no `cd`, no `&&`, no pipes. If a Bash call is denied, run the plain command again; inspect inputs with the file-reading tool.
2. Score: `python3 scripts/score_review.py --log subagent_dispatch_log.jsonl --agent NAME --as-of YYYY-MM-DD`. Pass `--prior review_NAME.json` when an earlier review of the same agent exists; the script keeps a dated copy of it as `review_NAME.DATE.json` before writing the new one. Read `review_NAME.md`. The criteria and bands are in `references/criteria.md`; load it when the user asks why a score or verdict came out as it did.
3. Act on the verdict with `python3 scripts/apply_action.py --review review_NAME.json --agents-dir DIR` plus the arguments below. Never edit a definition by hand; the actions log must match reality. Load `references/actions.md` before writing any new body or description.

| Verdict | Extra arguments | What changes |
|---|---|---|
| `insufficient_data`, `retain` | none | nothing; the entry is still logged |
| `improvement_plan` | `--body FILE` holding the rewritten system prompt (optional; without it only the plan section is appended) | body replaced, plan section appended, `pip_NAME.md` written |
| `reassign` | `--description TEXT` narrowed to the strong task types | description replaced |
| `replace` | `--body FILE` with a new system prompt | old file moved to `retired/NAME.DATE.md`, new file at the same name the same minute |
| `promote` | `--new-role NAME --description TEXT` | new role file created; the old position stays filled |
| `merge` | `--into NAME` | scope appended to the sibling's description, this file retired |

4. Replace, merge and promote are never left half done: the retire or copy and the fill happen in the same `apply_action.py` run, before you report. If the user names the new role, use that name; otherwise derive one from the strong task type (for example `lead-researcher`).
5. When reviewing several agents, run steps 2 and 3 per agent and write one report with a section per agent.

## Report to the user
Write it in this order, nothing before it:
1. `Verdict: X for NAME (composite N, M dispatches, window START to END)`.
2. Evidence: two to five lines quoting counts and dispatch ids from the findings and evidence lists.
3. Action taken: the files changed, created or retired, exactly as `apply_action.py` printed them, and the re-review date. For `insufficient_data` say that five dispatches are needed and how many exist.
4. What the instruction change targets, one line per finding, only when a body or description was written.
State only actions the script logged. If no file changed, say so.
