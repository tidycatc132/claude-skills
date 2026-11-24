# Running the plan against ClickUp

Read this after the person has said yes to the preview. Every step uses the ClickUp connector. Work through `<slug>-clickup-ops.json` in the order below and keep `clickup/<slug>/<slug>-clickup-ids.json` (`{"list_id": ..., "ids": {"<item key>": "<task id>"}}`) up to date after each step, so a stopped run can carry on without making duplicates.

## 1. Find the folder and check for an existing list

- Find the folder named in `list.folder` inside the space named in `list.space` (`clickup_get_workspace_hierarchy`, or `clickup_get_folder`). Never guess an id.
- `clickup_get_list` with `list_name` = `list.name`. If a list with that name already exists in that folder, this is a re-run: do not create a second list. Read it back (step 7), run `check_list.py`, and create only the items its `Every planned task exists once` row says are missing, then carry on from step 5 for those items only. If the ids file is gone, rebuild it from the readback with `check_list.py ... --ids-out clickup/<slug>/<slug>-clickup-ids.json`.

## 2. Create the list

`clickup_create_list_in_folder` with `name` = `list.name` and the folder id. Save `list_id`. The list URL is `https://app.clickup.com/<workspace id>/v/li/<list id>`.

## 3. Look up fields, task types and people

- `clickup_get_custom_fields` with the new `list_id`. Find the dropdowns named `Department` and `Position` and map each item's `department` and `position` to the option id with that exact name. Find the people fields `Account Manager` and `Project Manager`. A field or option that is not there is left off the task and listed in the answer; never pick a near match.
- `Client Name` dropdown: if it has an option with the client's exact name, set it on every item; if not, leave it off and say in the answer that someone adds the option by hand (the connector cannot add dropdown options). For a test run, leave it off.
- Task types `Deliverable` (for `task_type` of groups) and `Milestone`: pass the name as `task_type` to `clickup_create_task`. If the call refuses the type, create the task without it and list it in the answer.
- People: `clickup_resolve_assignees` with every distinct name in `people`. A name that does not resolve to exactly one user gets no assignee; list it in the answer.

## 4. Create the items, level by level

Items in the ops file are already in creation order: every `level` 0 item, then level 1, then level 2. A parent is always created before its children. For each item call `clickup_create_task` with:

| Argument | Value |
|---|---|
| `list_id` | the new list |
| `name` | `name` |
| `parent` | the created id of `parent_key` (omit when `parent_key` is null) |
| `status` | `status` |
| `tags` | `tags` |
| `task_type` | `task_type` (omit when null) |
| `markdown_description` | `markdown_description`, unchanged |
| `assignees` | the resolved id for `assignee` (omit when null or unresolved) |
| `custom_fields` | Department and Position option ids; on every item, the Account Manager and Project Manager people fields when `people.AM` / `people.PM` resolved |

Do not send dates here. Calls within one level can go in parallel; a new level starts only when the one before it is done. Write each returned id into the ids file.

## 5. Set the dates

ClickUp saves date-only values sent at create time a day early. So dates go in afterwards, one `clickup_execute_operator` call per entry of `date_batches`, in the listed order:

- model `task`, operator `update_many`
- body: `task_ids` = the created ids of the entry's `keys`, `start_date` = `start_ms`, `due_date` = `due_ms`, `start_date_time` = false, `due_date_time` = false

Every `*_ms` value is 09:00 UTC on the planned day: that is 4 AM US Eastern, so the date shows on the same day in every US time zone, and it is the value the 2026-11-22 sample list kept when read back. Items with no dates (the issues log) are in no batch.

## 6. Add the dependencies

Only after every date is set. For each entry of `dependencies`, in order: `clickup_add_task_dependency` with `task_id` = id of `task`, `depends_on` = id of `waits_on`, `type` = `waiting_on`. The list is upstream first, which keeps the workspace's automatic rescheduling from moving later tasks.

## 7. Read back

1. `clickup_filter_tasks` with `list_ids` = [the list], `subtasks` true, `include_closed` true, `fields` = ["assignees"]. Repeat with `page` = `next_page` while `has_more` is true. Save each result verbatim as `clickup/<slug>/readback-filter-<n>.json`.
2. `clickup_execute_operator`, model `task`, operator `get_many`, body `{"ids": [up to 50 ids], "includeContent": false}`, with this `query`:

   ```
   tasks[*].data.{id: id, name: name, parent: direct_parent, status: status.status, start_date: time_mgmt.start_date, due_date: time_mgmt.due_date, tags: tags, waits_on: related_tasks[?type=='dependsOn'].task_id}
   ```

   Save each result verbatim as `clickup/<slug>/readback-get-<n>.json`.
3. `python3 <skill-dir>/scripts/readback.py --out clickup/<slug>/<slug>-clickup-readback.json --list-id <id> --list-url <url> --get-many <get files> --filter <filter files>`

## 8. Check, and fix dates that moved

`python3 <skill-dir>/scripts/check_list.py clickup/<slug>/<slug>-clickup-ops.json clickup/<slug>/<slug>-clickup-readback.json` writes `<slug>-clickup-plan.md`.

If the dates row fails, the workspace moved them. Reset each listed task with `update_many` (its planned `start_ms`, `due_ms`, both `*_date_time` false), upstream tasks first, then read back and check again. Do this at most twice; if dates still move, stop and report the tasks and their dates. Any other FAIL row: fix that item (create the missing task, add the missing dependency) and re-check. Never edit the readback or the ops file by hand.

## Sitemap page subtasks

After `page_subtasks.py` and the person's yes: one `clickup_create_task` per entry of `create` (`parent` = `parent_id`, `name`, `status`, `tags`, `markdown_description`, `assignee` resolved as in step 3, `department` and `position` mapped as in step 3). Then one `update_many` with all the new ids and the entry's `start_ms` / `due_ms`. Read back (step 7) and run `check_list.py` again: page subtasks under W2-5 are allowed and listed in the plan record.
