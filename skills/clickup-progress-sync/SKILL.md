---
name: clickup-progress-sync
description: For a managing agent that must write a sub-agent's progress report into ClickUp through the ClickUp connector. Converts the report into agent_update.json, plans an ordered set of ClickUp operations (verify task, post comment, set status, due date, attachments, time entry, tags, create follow-up tasks) in clickup_ops.json with a preview, executes them with the connector tools and logs results in clickup_sync_log.json. Use when a worker or sub-agent has reported task progress, completion, a blocker or new follow-up work and ClickUp tasks must reflect it: "update ClickUp with this", "log this outcome", "mark the task done and attach the deliverable", "reflect the sub-agent's status in ClickUp". Not a user-facing skill. Do NOT use for reading or reporting on ClickUp (triage, summaries, exports), for other trackers, or for creating workspace structure; it only writes task-level updates that came from an agent's report.
---

# ClickUp progress sync

A sub-agent tells you what happened; ClickUp has to say the same thing. The planner turns the report into exact connector calls so that every write is traceable to something the sub-agent said. You transcribe, plan, execute, log.

## Files

- `scripts/plan_ops.py`: validates `agent_update.json` and writes `clickup_ops.json` plus `clickup_sync_preview.md`. Standard library; run it as its own plain `python3 <skill>/scripts/plan_ops.py agent_update.json` command, where `<skill>` is the folder holding this file. No `cd`, no chaining.
- `references/input-format.md`: every field of `agent_update.json` and how to pick the `outcome`. Load it before transcribing a free-text report or when validation fails.
- `references/executing.md`: what to do with each op's result, the status map, the log format, and the rules that never bend. Load it before executing against the connector.

## Interface

Input `agent_update.json`: `source_agent`, `reported_at`, optional `default_list_id`, `items[]` (`task_ref`, `outcome` in `completed|in_progress|blocked|needs_review|cancelled|no_change`, `summary`, optional `details`, `blockers`, `artifacts`, `time_spent_minutes`, `progress_percent`, `due_date`, `tags`) and `new_tasks[]` (`name`, `parent_ref` or `list_id`, `description`, `priority`, `due_date`).

Output `clickup_ops.json`: `generated_at`, `source_agent`, `reported_at`, `warnings[]`, `ops[]` with `seq`, `op`, `tool`, `task_ref`, `task_id`, `args`, `reason`, `requires`. `op` is one of `verify_task`, `add_comment`, `update_status`, `set_due_date`, `attach_file`, `upload_file`, `add_time_entry`, `add_tag`, `create_task`. `tool` is the ClickUp connector tool name and `args` its arguments, except `update_status`, which carries `status_candidates` for you to match against the task's real statuses. `requires` is empty or `resolve`, `status_choice`, `list_id`.

After execution: `clickup_sync_log.json` with one `done|skipped|failed` row per op.

## Workflow

1. Transcribe. If the report is already `agent_update.json`, validate it. Otherwise write `agent_update.json` from the report: one item per task mentioned, the sub-agent's own words in `summary`, blockers as a list, deliverable links as `artifacts`, minutes as `time_spent_minutes`, follow-up work the sub-agent discovered as `new_tasks`. Pick `outcome` by the rules in `references/input-format.md`; a report with open failures or caveats is `needs_review`, not `completed`.
2. Plan:
   ```
   python3 <skill>/scripts/plan_ops.py agent_update.json
   ```
   Fix any validation error it prints by correcting `agent_update.json`, never by guessing missing facts; a task you cannot identify stays a name and is resolved at execution time. Read `clickup_ops.json` and its `warnings`.
3. Execute, when the ClickUp connector tools are available: follow `references/executing.md` op by op in `seq` order. Verify before writing, skip duplicates, match statuses against the task's real list, and write `clickup_sync_log.json` at the end.
4. Report back in the manager's voice: per task, what is now in ClickUp (status, comment, attachments, time), what was skipped or failed and why, and anything a human must decide (ambiguous task names, statuses that did not match, cancellations awaiting confirmation).

When the connector is not available, stop after step 2 and say so: the plan and preview are the deliverable, nothing has been written to ClickUp, and the log must not be created.

## Judgement calls

- The sub-agent's claim is the input, not the truth. Record it as a comment faithfully; only set `completed` when it reported completion with no open problems.
- Cancellation is a recommendation. The plan sets a cancelled status and the comment states why; a human closes the task.
- Re-running the same report must not double-post: the comment header carries the agent and timestamp, and `executing.md` says to check for it first.
- One report, one plan file. If several sub-agents report at once, write one `agent_update.json` per agent and run the planner with `--out` and `--preview` paths that name the agent.
