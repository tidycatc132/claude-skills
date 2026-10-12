# Executing `clickup_ops.json` against the ClickUp connector

Load this when you are about to run the plan. Every op names the connector tool (`tool`) and its arguments (`args`). Run ops in `seq` order; ops for one task are grouped, with `verify_task` first.

## Per op

| op | tool | what to do with the result |
|---|---|---|
| `verify_task` | `clickup_get_task` (`expand_statuses: true`) | Confirm the task exists and its name matches what the sub-agent described. Keep `available_statuses` for the `update_status` op of the same task. If the id is unknown or the task is clearly a different piece of work, skip every later op for that task and record `failed` with the reason. |
| `verify_task` with `requires: resolve` | `clickup_search` (`asset_types: ["task"]`) | Resolve the name. Exactly one match: fill `task_id` into the task's remaining ops and continue. Zero or several: skip the task, record `skipped: ambiguous task_ref`, and report it. |
| `add_comment` | `clickup_create_comment` | Before posting, read the latest comments with `clickup_get_task_comments`. If a comment with the same first line (`**Update from <agent>** (<reported_at>)`) is already there, record `skipped: duplicate` instead of posting again. |
| `update_status` | `clickup_update_task` | Pick the first entry of `status_candidates` that appears, case-insensitively, in `available_statuses` and send it as `status`. None matches: record `skipped: no matching status` and name the list's statuses in your report so the status map can be fixed. |
| `set_due_date` | `clickup_update_task` | Send as given. |
| `attach_file` | `clickup_attach_task_file` | Send `file_url`. A URL that needs authentication will fail; record `failed` and leave the link in the comment as the fallback (it is already there). |
| `upload_file` | `clickup_request_attachment_upload` | Follow that tool's description for local files; the planner cannot upload. |
| `add_time_entry` | `clickup_add_time_entry` | Send `start` and `duration`. If the workspace rejects time tracking, record `failed` and move on; the comment already states the time. |
| `add_tag` | `clickup_add_tag_to_task` | Fails when the tag does not exist in the space; record `failed`, do not create tags. |
| `create_task` | `clickup_create_task` | `list_id` null (`requires: list_id`): read the parent with `clickup_get_task` and use its list. Before creating, search the list for a task with the same name to avoid duplicates on a re-run. |

## Status map

`plan_ops.py` ships a default map from outcome to candidate statuses. Workspaces differ; when `update_status` keeps being skipped, write a `status_map.json` next to the plan and pass `--status-map`:

```json
{"completed": ["Complete"], "in_progress": ["In Progress"], "blocked": ["Blocked"], "needs_review": ["Client Review"], "cancelled": ["Closed"]}
```

Keep it with the project so later runs reuse it.

## The log: `clickup_sync_log.json`

Write it when execution finishes, even if everything failed:

```json
{
  "executed_at": "2026-10-12T15:02:00Z",
  "source_agent": "content-writer",
  "reported_at": "2026-10-12 14:30",
  "results": [
    {"seq": 1, "op": "verify_task", "task_id": "86c1abc2d", "result": "done", "note": ""},
    {"seq": 3, "op": "update_status", "task_id": "86c1abc2d", "result": "done", "note": "status=complete"},
    {"seq": 8, "op": "update_status", "task_id": "WEB-418", "result": "skipped", "note": "no matching status; list has: to do, doing, done"}
  ]
}
```

`result` is `done`, `skipped` or `failed`. One row per op in the plan. A `create_task` row's `note` carries the new task id.

## Rules that do not bend

- Never change assignees, priority of an existing task, or watchers unless the sub-agent's report explicitly asks for it and the plan contains it.
- Never close or complete a task on a `needs_review`, `in_progress` or `blocked` outcome, whatever the sub-agent's tone.
- Never fabricate progress. The comment carries the sub-agent's words; if the report is vague, the comment is vague too.
- A failed op does not stop the others for the same task except after a failed `verify_task`.
