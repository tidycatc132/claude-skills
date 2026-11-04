# Month 1 mode and the ClickUp plan

Run after the close-out, when the retainer starts. It works from the roadmap as SEO left it, not from a fresh scaffold.

## What `month1` does

1. Checks the roadmap's rows (not the completeness test, since new items are expected).
2. Takes every Month 1 row, and leaves out:
   - rows whose `QA-` or `CE-` ids are now fixed: `FIXED` in the newest launch check's `## Re-run Status`, or done or closed in `qa/<slug>/<slug>-bugherd-status.json` (a deferred item finished after launch counts as fixed);
   - rows whose Description starts `Already done`.
3. Adds Month 1 items deferred or raised since the roadmap: open findings of the newest launch check, staging items newly deferred in the BugHerd status file, and `Scope Change` rows from Week 5 feedback rounds the roadmap does not cite (in the table or under `## Not Planned`, so an item the SEO dropped stays dropped). Their description ends "New since the roadmap."
4. Writes the task list and the plan, then checks that the plan matches the list row for row.

## Task list: `roadmap/<slug>/<slug>-month-1-tasks.md`

```
Client: <client>
Date: <YYYY-MM-DD>
Roadmap: roadmap/<slug>/<slug>-seo-roadmap.md
Launch check: <path> (RESULT: ...) | none
ClickUp: Client Monthly Work > <list name>
ClickUp plan: roadmap/<slug>/<slug>-clickup-tasks.json

# Month 1 Tasks: <client>

| # | Name | Description | Priority | Est. time | Owner | Source |
|---|---|---|---|---|---|---|

## Left Out

- <task> (<source>): fixed since the roadmap (QA-...) | already done
```

## Plan: `roadmap/<slug>/<slug>-clickup-tasks.json`

```json
{
  "client": "<client>",
  "space": "Client Monthly Work",
  "list": "<list name>",
  "list_id": "",
  "approved_by": "",
  "tasks": [
    {"n": 1, "source": "launch carry-over", "clickup_task_id": "",
     "call": {"tool": "clickup_create_task",
              "args": {"list_id": "", "name": "...", "markdown_description": "...\n\nOwner: SEO\nSource: ...",
                       "priority": "high", "time_estimate": "30", "tags": ["month 1", "seo"]}}}
  ]
}
```

Priority maps high to `high`, medium to `normal`, low to `low`. `time_estimate` is whole minutes. There are no `assignees`: the SEO assigns people in ClickUp. Tests use this file as the recorded tool-call plan; nothing in the repo calls ClickUp.

## Creating the tasks (only after the SEO's go)

1. Find the list: the ClickUp connector's list lookup with the plan's `list` name inside the `Client Monthly Work` space, or the list the SEO names. If no list matches, ask; never create a list or space.
2. For each task in `n` order whose `clickup_task_id` is empty, call `clickup_create_task` with its `args` and the list id. Skip tasks that already have an id.
3. Record the ids with `created` (`--task N=ID` per task, `--list-id`, `--approved-by` with the approver's role). It refuses to overwrite a different id, so a task is never recorded twice.
4. Tell the user how many tasks were created and link the list.

A re-run of `month1` keeps recorded ids for tasks whose Source and name are unchanged (and the list id while the list name is the same), and prints a NOTE for any created task that has dropped out of Month 1 so the SEO can close it by hand.
