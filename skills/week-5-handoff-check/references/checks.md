# Checks and file formats

## BugHerd status file: `qa/<slug>/<slug>-bugherd-status.json`

Written by you from BugHerd (or from what the PM told you), read by `week5_handoff.py run`.

```json
{
  "read_on": "2026-11-17",
  "source": "BugHerd connector",
  "tasks": [
    {"bugherd_task_id": "25", "finding_id": "QA-dcc6e684",
     "title": "/services/drain-cleaning/: The image ... has no alt text.",
     "status": "SEO Review", "severity": "important",
     "deferred": "The client is sending a new header photo; the alt text goes on with it after launch"},
    {"bugherd_task_id": "31", "finding_id": "CE-66f3ebb0", "title": "...", "status": "done",
     "severity": "important", "deferred": ""}
  ]
}
```

- `bugherd_task_id`: the per-project task number, as in the task files.
- `finding_id`: the `QA-` or `CE-` id. Tasks this process created end their description with it (`(Staging QA <date>, QA-xxxxxxxx)` or `(Client edits <date>, CE-xxxxxxxx)`), so copy it from there; leave it empty for a task someone made by hand on the board.
- `status`: BugHerd's own status or column name, copied as BugHerd shows it (`done`, `closed`, `Copy Review`, `Dev Ready`, `backlog` ...). `done`, `closed` and `archived` count as done; anything else is open.
- `severity`: BugHerd's severity (`critical`, `important`, `normal`, `minor`), or empty if BugHerd has none.
- `deferred`: empty, or the PM's reason for taking that task to post-launch. Only the PM defers.
- `source`: `BugHerd connector`, `PM in chat`, or `export: <file>`.

With the connector: `list_projects` (or the routing file's project), then `list_project_tasks` for that project with done and closed tasks included, and `get_task_details` for any task whose status the list does not show. One entry per task on the board.

## AM review file: `qa/<slug>/<slug>-am-review.md`

```
Client: <client>
QA report reviewed: qa/<slug>/<slug>-staging-qa-<date>.md
AM items: <what the AM settled, or none open>

AM sign-off: <AM name>, <YYYY-MM-DD>
```

Only the `AM sign-off:` line is checked. The AM writes it after reviewing staging and the `## AM Items` of the QA report, before the client sees the link.

## The eight checks

| # | Check | PASS when | Owner on FAIL |
|---|---|---|---|
| 1 | Dev handoff index | the index exists and its last line is `GO` | PM |
| 2 | Staging QA re-run | the newest QA report has `## Re-run Status` and a `RESULT:` line, and is not older than the newest Week 5 feedback file | PM |
| 3 | Open CRITICAL | the newest report has its Findings table, the table has no CRITICAL row, and the report does not say `RESULT: NOT READY` | the finding's department, else PM |
| 4 | Open MAJOR | every MAJOR row's BugHerd task has a `deferred` reason in the status file | the finding's department |
| 5 | BugHerd tasks | the status file exists, `read_on` is on or after the newest QA report and Week 5 feedback file and not after today, every task id in the task files is in it, every task (other than the open findings of checks 3 and 4) is done, deferred, MINOR, or a FIXED QA finding, no task the task files call CRITICAL is open (deferral and BugHerd severity do not count for it), and no task in a task file lacks a `bugherd_task_id` | the task's department, else PM |
| 6 | Week 5 email | the email exists with valid `Send date:` and `Reply by:` lines and was sent on or before today | AM |
| 7 | Client edits | every Week 5 feedback file has rows, every row has a known `Class` and every Scope Change has a `PM/AM:` note; or there is none and the reply-by date has passed and the email's `No-reply line:` is `yes` | AM |
| 8 | AM sign-off | `AM sign-off: <name>, <YYYY-MM-DD>` is in the AM review file, dated on or before today | AM |

GO when all eight PASS. The newest QA report and the newest feedback file are chosen by the date in the file name; only feedback files with `Week: 5` count, but the client-edit task files of every Week 5 round are checked.

Notes on the rules:
- An open CRITICAL or MAJOR finding is listed once under Blocking, with its BugHerd task and status, and is not listed again under check 5.
- A deferred MAJOR finding, a deferred task, and open MINOR items go to `## Carried to Post-Launch` and into the go-live message.
- Severity comes from the task files; BugHerd's `severity` is used only for a task with no `finding_id` from them.
- Lines of the QA report's `## Not Checked` go to `## Notes`, so the PM sees what the re-run could not confirm.
- A task whose QA finding the re-run marked FIXED but which is still open in BugHerd goes to `## Close in BugHerd`; it does not block.
- No feedback and the reply-by date not yet passed: NO-GO, waiting on the client. No feedback, date passed, `No-reply line: dropped`: NO-GO, the AM gets an answer. No feedback, date passed, `No-reply line: yes`: PASS, and `## Notes` says the client did not verify the site.

## Go-live message: `handoff/<slug>/<slug>-go-live-message.md`

Written by the script on GO, for the PM to send dev. Header lines (`Go-live message:`, `Date:`, `Final sweep:`, `Staging:`, `Production:`), then `Subject: All good to go: <client>`, the cleared Build pages with their URLs, `At launch:` (every `## Launch Toggles` line of the QA report), `Carried to post-launch`, `Not in this launch` (pages whose priority is not Build, and Scope Changes) and the PM's sign-off.
