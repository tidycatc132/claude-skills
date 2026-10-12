# `agent_update.json`: the structured form of a sub-agent report

Load this when transcribing a sub-agent's free-text report, or when `plan_ops.py --validate` rejects the file.

```json
{
  "source_agent": "content-writer",
  "reported_at": "2026-10-12 14:30",
  "default_list_id": "901300112233",
  "items": [
    {
      "task_ref": "https://app.clickup.com/t/86c1abc2d",
      "outcome": "completed",
      "summary": "One or two sentences on what happened.",
      "details": "Optional longer notes, kept verbatim in the comment.",
      "blockers": ["Required when outcome is blocked"],
      "artifacts": [{"name": "draft.md", "url": "https://..."}, {"name": "report.pdf", "path": "out/report.pdf"}],
      "time_spent_minutes": 95,
      "progress_percent": 60,
      "due_date": "2026-10-16",
      "tags": ["content"]
    }
  ],
  "new_tasks": [
    {"name": "Supply pricing table", "parent_ref": "WEB-418", "list_id": "optional", "description": "...", "priority": "high", "due_date": "2026-10-15", "assignees": [], "tags": []}
  ]
}
```

## Fields

| field | required | notes |
|---|---|---|
| `source_agent` | yes | the sub-agent's name as it should appear in ClickUp comments |
| `reported_at` | yes | `YYYY-MM-DD` or `YYYY-MM-DD HH:MM`; time entries end at this moment, so include the time when you have it |
| `default_list_id` | no | list for `new_tasks` that do not name one |
| `items[].task_ref` | yes | ClickUp task URL, custom id (`WEB-418`), raw id (`86c1abc2d`, lowercase letters and digits, at least one digit) or the exact task name. Anything else counts as a name; names cannot be written to until resolved and the plan marks them `requires: resolve` |
| `items[].outcome` | yes | `completed`, `in_progress`, `blocked`, `needs_review`, `cancelled`, `no_change` |
| `items[].summary` | yes | what the sub-agent reported, in its own terms, not your interpretation |
| `items[].details` | no | kept verbatim in the comment |
| `items[].blockers` | when blocked | one entry per blocker; each becomes a bullet |
| `items[].artifacts` | no | `url` entries become attachments by URL; `path` entries become local uploads |
| `items[].time_spent_minutes` | no | positive number; becomes one time entry ending at `reported_at` |
| `items[].progress_percent` | no | shown in the comment only; ClickUp progress fields vary per workspace |
| `items[].due_date` | no | only when the sub-agent reported a new date |
| `items[].tags` | no | tag names that already exist in the space |
| `new_tasks[].name` | yes | |
| `new_tasks[].parent_ref` | no | makes it a subtask; also lets the executor read the list from the parent when no list id is given |
| `new_tasks[].list_id` | one of list_id / default_list_id / parent_ref | |
| `new_tasks[].priority` | no | `urgent`, `high`, `normal`, `low` |
| `new_tasks[].assignees`, `tags` | no | passed through to task creation; assignees on a new task are fine, this is the only place the skill sets them (existing tasks are never reassigned) |
| `new_tasks[].status`, `task_type`, `time_estimate` | no | passed through as given; `time_estimate` is minutes |

## Choosing the outcome from free text

- `completed`: the sub-agent says the work is done and names no open problems. "Done but two checks fail" is not completed.
- `needs_review`: finished from the sub-agent's side but a human or another agent must look before it closes (QA with failures it could not fix, a draft awaiting approval, results with caveats).
- `in_progress`: partial, with more work planned by the same agent.
- `blocked`: cannot continue without something from outside; list what, one entry per blocker.
- `cancelled`: the sub-agent recommends dropping the task (duplicate, no longer needed). The task is not closed until a human confirms; the plan only sets the status and leaves the reason in the comment.
- `no_change`: a comment only (a note, a question, a heads-up), status untouched.

A report that mentions several tasks is several items. Follow-up work the sub-agent discovered that has no task yet goes in `new_tasks`, never into another task's comment alone.
