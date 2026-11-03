# Week 5: the client's staging edits

In Week 5 the client looks over the staging site and sends edits: by replying to the staging email, as tasks they leave on the client's BugHerd project (they are guests there), or both. Each edit gets a class, a page, a department and an action; the edits that are work become BugHerd tasks in the same format as staging-site-qa's, so the PM works one board. Secrets, verbatim quotes, numbers and the WISE voice work as in Sorting Rules and Reply Voice; this file replaces their types, affects, impact and owner for this reply.

## Files read

From the working folder (the folder holding `kickoff/`). `feedback.py scope kickoff/<slug> --week 5` prints what it found.

- The client's email, saved word for word as in SKILL.md (optional when all edits are in BugHerd).
- The client's BugHerd tasks, saved by you as `feedback/<slug>/<date>-bugherd-client-tasks.json` (optional when all edits came by email). See "Reading BugHerd" below.
- `qa/<slug>/<slug>-staging-qa-<date>.md` (staging-site-qa): the newest one's `Staging:` line (`Staging: <base URL> (saved pages: ...)`) gives the staging site (contract `staging-site-qa-to-client-feedback`). Without a report, give `staging_url` in the plan; with neither, the host of the BugHerd task URLs is used, else the plan is refused.
- `handoff/<slug>/<slug>-dev-handoff-index.md` (dev-handoff-index): its `- URL:` lines are the pages the build has. A Mechanical or Strategic edit must name one of them (**checked**).
- `qa/routing.md`: the `BugHerd project:` line and the `| Department | Column | Assignee |` table. Without it, columns default to Content `Copy Review`, SEO `SEO Review`, Design `Design Review`, Development `Dev Ready`, and `assignee` stays empty for the PM to fill. Names are never written anywhere else. The routing file wins: Strategic edits go to whatever column it gives SEO (`SEO Review` by default).
- `emails/<slug>/<slug>-week-5-email.md` (week-5-client-email), when it exists: its `Reply by:` date goes in the header and its figures may be repeated in the reply.

Once a staging QA report exists, a plan without `"week": 5` is refused (**checked**).

## Reading BugHerd

Only the client's own tasks count: the ones a guest (client) created, not the team's QA tasks. With the BugHerd connector, find the client's project (the routing file's `BugHerd project:` line, else the project named for the client), list its tasks with descriptions (`list_project_tasks`, full view), keep those whose requester is a client or guest, and save them word for word:

```json
[{"task_id": "14", "url": "https://<staging host>/services/hardscaping/", "requester": "<client name>",
  "created_at": "YYYY-MM-DD", "description": "<the client's words, exactly>"}]
```

`task_id` is the per-project number. Never tidy a description: it is the quote source for that task. If the connector is not connected, ask the PM for an export and save it in this shape. Every saved task needs at least one item (**checked**).

## Classes

| Class | When | Department | Task |
|---|---|---|---|
| `Mechanical` | Facts, typos, names, numbers, small wording that does not touch a heading or keyword; a broken thing (a form that does not send, a dead link); swapping in the right photo. | `Content`, `Design` or `Development` (**checked**) | new task in that department's column |
| `Strategic` | Page titles or headings (H1), service descriptions that change what a page targets, CTA wording or placement, adding or removing a section, adding or removing a service. SEO decides it before it is built. | `SEO` (**checked**) | new task in `SEO Review` |
| `Scope Change` | A page the build does not have, a redesign, new functionality, anything that goes back to design or needs significant new content. A design opinion ("not crazy about the green") is a Scope Change: design direction was settled in Week 3. | `Account Management` (**checked**) | none; listed for the PM/AM |
| `Question` | The client asks something the AM answers. | `Account Management` | none |
| `Approval` | The client signs off ("everything else looks great"). | `Account Management` | none |

When in doubt between Mechanical and Strategic, choose Strategic: an SEO look costs little. A Strategic edit can be a good idea; the class only makes sure SEO sees it first.

## The plan

```json
{"week": 5, "date": "2026-11-12", "from": "client-email.txt", "contact": "Dana Whitlock", "am": "Riley Shaw",
 "staging_url": "",
 "items": [
  {"feedback": "On the About page, Marcus's last name is spelled Hollaway. It's Holloway.", "source": "email",
   "page": "/about/", "class": "Mechanical", "department": "Content", "severity": "MAJOR",
   "action": "Correct the spelling to Marcus Holloway"},
  {"feedback": "The estimate form says Submit but nothing happens when I press it.", "source": "bugherd:15",
   "page": "/contact/", "class": "Mechanical", "department": "Development", "severity": "CRITICAL",
   "action": "Fix the estimate form so it sends and shows a confirmation"},
  {"feedback": "We started offering snow removal this winter, so we'd love a page for it too.", "source": "email",
   "page": "new page", "class": "Scope Change", "department": "Account Management",
   "action": "Discuss a snow removal page",
   "pm_am_note": "A sixth page is beyond the five-page SOW; quote it as a change order or plan it after launch"}
 ],
 "facts": [], "reply": {"subject": "...", "body": "Hi Dana,\n\n..."}}
```

- `from`: the email file name, or the BugHerd file name when there is no email. `date`: the email's date, else the newest task's `created_at`. `staging_url` only when no QA report gives it.
- `source`: `email` or `bugherd:<task_id>`. The quote must be verbatim from that source (**checked**). An item from a BugHerd task names the task's page (**checked**).
- `page`: a path from the dev handoff index (`/about/`), `site-wide` (footer, header, every page), or `new page` (Scope Change only, **checked**).
- `severity` (Mechanical and Strategic only, **checked**), as the guide defines it: `CRITICAL` must be fixed before launch (broken functionality, wrong contact details, missing content or page); `MAJOR` should be fixed before launch (most client corrections); `MINOR` can wait for after launch.
- `action`: one imperative line a department can act on. Clients can read the BugHerd task, so it stays client-safe: no budget, scope or internal notes (**checked** in the task file), and no SEO reasoning such as target keywords; that goes in your answer to the PM.
- `pm_am_note` (Scope Change only, **checked**): one line for the PM/AM on what the request means for scope, timeline or design and what to decide.
- `facts` work as in Sorting Rules (a new service, a changed phone number). The scope `CONFLICT` rule does not apply: Scope Changes go to the PM/AM through this file.

## What the script writes

- `feedback/<slug>/<date>-feedback.md`: header (`Client:`, `Date:`, `From:`, `Scope source:`, `Week: 5`, `Staging:`, `BugHerd export:`, `Dev handoff index:`, `Week 5 email:`, `BugHerd tasks:`), `## Summary`, `## Feedback Items` as `| # | Feedback | Source | Page URL | Class | Department | Action | Task |` (Task is the `CE-xxxxxxxx` id, with `(BugHerd #n)` for a client's own task, or `none`), `## SEO Review` (each Strategic edit), `## Scope Changes` (each as `- #<n> <page>: PM/AM: <note>`), `## Reply Draft`.
- `feedback/<slug>/<date>-bugherd-tasks.json`: one object per Mechanical or Strategic edit with staging-site-qa's keys in its order: `finding_id` (`CE-` + a hash of page and quote, stable across re-renders), `status` (`NEW`), `create`, `bugherd_task_id`, `page_url`, `department`, `column`, `assignee`, `severity`, `bugherd_severity`, `title`, `description`. An edit that came from the client's BugHerd task carries that task's id and `create: false`: the task exists, it only needs moving.
- The updates file, when there are facts, as in SKILL.md.

`feedback.py contract week-5 <feedback.md>` prints what week-5-handoff-check reads: `Week:`, the `Class` rows (class, department, task, `PM/AM note`) and the `tasks`.

## Preview, go, then BugHerd

BugHerd is visible to the client, so nothing goes there without the PM's go for this run.

1. After `RESULT: PASS`, show the PM: the Mechanical edits by department and column with the assignee, the Strategic edits waiting for SEO, each Scope Change with its PM/AM note, and the client tasks that will be moved. Name any department with no assignee. Stop and wait.
2. On the PM's go, with the BugHerd connector on the client's project: match each `assignee` to a project user (ask the PM about a name with no match); confirm each `column` is one of the project's statuses (a missing column: tell the PM, leave those tasks in Feedback).
3. Objects with `create: true`: `create_tasks` (up to 40 per call) with `title`, `description`, `url` = `page_url`, `severity` = `bugherd_severity`, `status` = `column`, `assignees`, and `tags` = the department. Then record the ids: `python3 <skill-dir>/scripts/feedback.py created feedback/<slug>/<date>-bugherd-tasks.json CE-xxxxxxxx=<id> ...`.
4. Objects with `create: false` and a `bugherd_task_id` from the client: `update_task` with `status` = `column` and `severity` = `bugherd_severity`, and set the assignee. Leave the client's description as it is.
5. Report what was created and moved per column, and anything that failed. Without the connector, say so and give the PM the task file.

## The reply

In WISE's voice, as in Reply Voice, at most 300 words, in this order where the client raised them:

- Thank them and say what they approved.
- Confirm the Mechanical edits plainly: we will fix, correct, update or swap them (**checked**: the reply confirms at least one).
- For each Strategic edit: thank them for the suggestion without judging it yet (praise reads as a yes before SEO has looked), say our SEO team will review it before it changes (**checked**), and that the AM comes back after. Never say it is done or will be done before the review (**checked** for plain cases).
- For each Scope Change: name it and say kindly that it goes beyond what this build covers (a design opinion too, by name), and offer a call to talk it through (**checked**); a quote or change order can follow the call. For a design opinion, note that the design direction was agreed earlier and offer to talk about specific concerns. Never agree to build it (**checked** for plain cases).
- Answer questions; give no launch date the files do not hold.
- No internal words (**checked**): Mechanical, Strategic, Scope Change, punch list, severities in capitals, `CE-`/`QA-` ids, column names, PM/AM.
