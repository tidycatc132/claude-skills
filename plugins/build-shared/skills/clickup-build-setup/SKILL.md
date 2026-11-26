---
name: clickup-build-setup
description: Creates a new WISE website build's ClickUp list with every step from Week 1 to Post Launch as a task, grouped under Deliverable parents, dated in business days from the kickoff date, with week milestones, waiting-on dependencies, starting statuses and the message to type into Claude in each task. A script plans every task and date; Claude shows a preview and creates the list only after a yes, then reads it back and checks it. Second mode adds one subtask per sitemap page under Write the sitemap pages once the sitemap is approved. Also builds test-run lists. Use when the PM asks to set up the ClickUp plan, project list or build tasks for a new client, or to add the sitemap pages to ClickUp. Do NOT use for the Day 1 kickoff files (use new-build-kickoff), logging an agent's progress on existing tasks (use clickup-progress-sync), the Month 1 retainer tasks (use retainer-roadmap), planning the sitemap itself (use site-structure-optimizer), or paid media recommendations as tasks (use optimization-task-pusher).
---

# ClickUp Build Setup

Creates one build's ClickUp list from the fixed plan in [build-plan.json](references/build-plan.json): 14 Deliverable groups (15 with paid media), 7 week milestones, about 50 step tasks with their sub-steps, and the waiting-on links between them. Nothing reaches ClickUp until the person approves the preview.

## Two modes

- **Set up** (Week 1 step 1b, run by the PM): "Set up the ClickUp plan for [Client]. Code [ABC]. Kickoff date [date]. AM [name], PM [name], ...".
- **Sitemap pages** (after step 11): "Add the sitemap pages to ClickUp for [Client]".

## Inputs

| Input | Where it comes from | Needed |
|---|---|---|
| Client name | the message, else the first line `Client: <name>` of `kickoff/<slug>/<slug>-context.md` | yes |
| Client code | the message: three letters or digits, as in `[ABC]` | yes, ask if missing |
| Kickoff date (Day 1) | the message, `YYYY-MM-DD`, a business day | yes, ask if missing |
| Paid media signed | the message; else whether `kickoff/<slug>/<slug>-paid-media-brief.md` exists (the slug is the kickoff folder's name, and `plan_build.py` makes the same one: `&` becomes `and`) | yes |
| People by role | the message: `AM`, `PM`, `SEO`, `Editor`, `Designer`, `Developer`, `PaidMedia` | no: a role with no name gets no assignee |
| Test run | the message says test or test run | no |
| List name | only when the person gives an exact name (it must start with `[CODE] `): pass it as `--list-name` | no |
| Readback | a readback file the person names; else the one you write in executing.md step 7 | check only |
| Sitemap report | the report the person names, else the newest `seo-reports/site-structure-optimizer/*.md` with a table under a heading containing `URL map` (`Page`, `URL`, `Parent`, `Nav location`, `Priority`) | pages mode only |

Ask once, in one message, only for what is missing. Never invent a code, a date or a name. Names stay in this run's files; they are never written into the skill.

## Output

Folder `clickup/<slug>/`:

- `<slug>-clickup-ops.json`: every item (`key`, `ref`, `level`, `parent_key`, `name`, `kind`, `task_type`, `status`, `assignee`, `position`, `department`, `tags`, `start_date`, `due_date`, `start_ms`, `due_ms`, `markdown_description`), `date_batches` and `dependencies`, in run order
- `<slug>-clickup-preview.md`: the table the person approves, ending `PLAN: OK`
- `<slug>-clickup-ids.json`: item key to ClickUp task id, written while creating
- `<slug>-clickup-readback.json`: what ClickUp holds after the run
- `<slug>-clickup-plan.md`: list link and id, the check table, every task's link, ending `RESULT: PASS` or `RESULT: FAIL`
- pages mode: `<slug>-page-subtasks.json`

## Set up: steps

Run each script by its path in this skill's folder as one plain `python3` command with paths as arguments. Never chain, pipe or `cd`. If a Bash call is denied, run the same command again on its own; do not write a script's output by hand.

1. **Plan.** `python3 <skill-dir>/scripts/plan_build.py --client "<Client>" --code <ABC> --kickoff <YYYY-MM-DD> --paid-media yes|no --person AM="<name>" ...` (one `--person` per named role; add `--test-run` for a test list; `--holiday YYYY-MM-DD` for an extra day off). On `ERROR:` fix the input it names and rerun.
2. **Preview.** Show the preview file's summary lines (list name, kickoff and last day, item and dependency counts, holidays skipped, roles with no assignee) and the table, and ask: "Reply yes to create this list in ClickUp." Stop here until the person says yes. No connector call that writes anything happens before that yes.
3. **Create.** Follow [executing.md](references/executing.md) exactly: folder and existing-list check, create the list, look up fields and people, create items level by level, set dates with `update_many`, then add dependencies, then read back.
4. **Check.** `python3 <skill-dir>/scripts/check_list.py clickup/<slug>/<slug>-clickup-ops.json <readback file>`, where the readback file is the one the person named, else `clickup/<slug>/<slug>-clickup-readback.json`. Fix what it lists (executing.md step 8) and rerun until `RESULT: PASS`, or stop after two date-fix rounds and report.

If there is no ClickUp connector, do steps 1 and 2, say the list could not be created, and stop. When the person only asks to check a list that already exists, run step 4 on the readback they give and report; do not call ClickUp unless they ask for the fixes.

## Sitemap pages: steps

1. Read back the existing list (executing.md step 7) into `clickup/<slug>/<slug>-clickup-readback.json`.
2. `python3 <skill-dir>/scripts/page_subtasks.py --report <sitemap report> --ops clickup/<slug>/<slug>-clickup-ops.json --readback clickup/<slug>/<slug>-clickup-readback.json`
3. Show its table and ask for a yes. Then create the subtasks (executing.md, Sitemap page subtasks), read back and run `check_list.py` again.

A rerun adds only pages that are not there yet. The homepage is never added (it is written in Week 1).

## Rules the plan encodes

- Days are business days from Day 1, skipping weekends and the default holidays (New Year's Day, Memorial Day, Independence Day, Labor Day, Thanksgiving, Christmas Day, moved to the nearest weekday when they fall on a weekend). Week 1 runs D1 to D9, Week 2 D10 to D14, Week 3 D15 to D19, Week 4 D20 to D24, Week 5 D25 to D29, Week 6 D30 to D31, After launch D32 to D37.
- A test run uses the 15-day test schedule (`test_start`, `test_due` in the plan), puts `TEST` before the client name in the list name, tags every item `test-run` and adds a `TEST · Issues log` task.
- Website Design is one task from D5 to D19 that waits only on the Kickoff Call transcript (step 9); Homepage Design needs at least one design. There are no design brief tasks.
- Paid media tasks (the `Paid Media (only if signed)` group) are created only when paid media is signed.
- A task that waits on nothing starts `to do`; one that waits starts `internal dependency`; groups start `to do`.
- Every task description has the plan ref, who does it, the Claude skill, the message to type and the done-when line.

To change a task, a day or a dependency, edit `references/build-plan.json` in a reviewed change; never patch the ops file.

## Answer

Give the list link, the counts, the check table from `<slug>-clickup-plan.md` and anything left to do by hand: people who did not resolve, fields or options that were missing, and that the PM closes `Create the ClickUp plan` after checking the list. End with the `RESULT:` line. In the preview turn, end with the yes question instead.
