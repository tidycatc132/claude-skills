# Creating the BugHerd tasks

Only after the PM has seen the preview and said go. One BugHerd project per client.

If the BugHerd connector is not connected in this session, say so, leave `create` as it is, and give the PM the task file to import or enter by hand. Do not try another route.

1. **Find the project.** Use the `BugHerd project:` line of `qa/routing.md`; if it is a name, or there is no line, list the projects with the BugHerd connector and pick the one named for the client. If none or several match, ask the PM which one.
2. **Match assignees.** List the project's users (`list_project_users`) and match each department's `assignee` against display name or email. A name with no match: ask the PM, and create that department's tasks unassigned only if the PM says so.
3. **Check the columns.** Get the project details and confirm each `column` value is one of the project's statuses. If a column is missing, tell the PM and leave those tasks in Feedback (no status) rather than inventing a column.
4. **Create in batches.** `create_tasks` takes up to 40 tasks per call. For every object with `"create": true` send: `title`, `description`, `url` = `page_url`, `severity` = `bugherd_severity`, `status` = `column`, `assignees` = the matched user, and `tags` = the department name. Never send AM items or objects with `create: false`.
5. **Record the ids.** `create_tasks` returns results in the order sent. Run `python3 <skill-folder>/scripts/qa.py created --slug <slug> QA-xxxxxxxx=<id> ...` with each created task's id. A task that failed gets no id, so the next run offers it again.
6. **Report back.** Count created tasks per column, list any that failed with the error, and list `FIXED` findings so the PM can close their old tasks. Do not close or change existing tasks unless the PM asks.

Task creation is a step other people see (clients can be guests on the project), so it is never done without the PM's go for this run.
