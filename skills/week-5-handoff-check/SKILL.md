---
name: week-5-handoff-check
description: Runs the go/no-go final sweep ending a website build's Week 5 and, on GO, writes the all good to go message to dev. A script checks that the dev handoff index ends GO, the newest staging QA is a re-run with no open CRITICAL and every open MAJOR deferred, every QA and client-edit BugHerd task is done or deferred, the Week 5 email's send date has passed, the client's staging edits are classed with a PM/AM note on each Scope Change (or the reply-by date passed with no reply) and the AM signed off, then gives GO or NO-GO with owners. Use when the PM asks for the Week 5 final sweep, the launch go/no-go, whether a site is cleared to deploy, or the go message to dev once nothing blocks launch. Do NOT use for the staging QA or a re-run (use staging-site-qa), sorting the client's edits (use client-feedback), the staging email (use week-5-client-email), the Week 1 or 2 checks (use week-1-handoff-check, week-2-handoff-check), the dev index (use dev-handoff-index), or a technical SEO audit (use technical-seo-checker).
---

# Week 5 handoff check

The last step before launch. The PM runs it once QA tasks are processed, the client has had the staging site and their edits are dealt with. A script decides GO or NO-GO from the build's own files; your part is reading BugHerd into one status file, running the script and reporting. On GO the script also writes the message the PM sends dev. You never send it.

## Inputs

All paths are relative to the client's working folder; `<slug>` is the client folder name.

| File | From | What is read |
|---|---|---|
| `handoff/<slug>/<slug>-dev-handoff-index.md` | dev-handoff-index | last line `GO`; each page's `- Page:`, `- URL:` and `- Priority:` (Build pages are the ones cleared) |
| newest `qa/<slug>/<slug>-staging-qa-<YYYY-MM-DD>.md` | staging-site-qa | `Staging:`, the Findings table, `## Re-run Status` (must exist: a re-run), `## Launch Toggles`, last `RESULT:` line |
| `qa/<slug>/<slug>-bugherd-tasks.json` | staging-site-qa | `finding_id`, `status`, `bugherd_task_id`, `severity`, `department` |
| `feedback/<slug>/<date>-feedback.md` whose `Week:` line is 5, and its `<date>-bugherd-tasks.json` | client-feedback | the `Class` of each row, `## Scope Changes` lines with their `PM/AM note`, and the client-edit `tasks` (`CE-` ids) |
| `emails/<slug>/<slug>-week-5-email.md` | week-5-client-email | `Client:`, `Send date:`, `Reply by:`, `No-reply line:` |
| `qa/<slug>/<slug>-bugherd-status.json` | you, from BugHerd | every task on the client's BugHerd project: status, severity, and the PM's deferral reason |
| `qa/<slug>/<slug>-am-review.md` | the AM | a line `AM sign-off: <name>, <YYYY-MM-DD>` |
| `kickoff/<slug>/<slug>-context.md` | new-build-kickoff | client name and the `- Website:` line (production domain) |

Formats of the status file and the AM review file, and every check's exact rule: `references/checks.md`. Load it before you write the status file or explain a result.

## Outputs

- `handoff/<slug>/<slug>-week-5-handoff.md`: header lines, `## Checks` (`| # | Check | Result | Detail | Owner |`, eight rows, each PASS or FAIL), `## Blocking` (each item with its owner), `## Carried to Post-Launch`, `## Scope Changes`, `## Close in BugHerd`, `## Notes`, and a last line `GO` or `NO-GO`.
- On GO only, `handoff/<slug>/<slug>-go-live-message.md`: pages cleared for launch, the launch toggles from the QA report (removing noindex and the like), items carried to post-launch, and what is not in this launch (Post-Launch pages, Scope Changes). Every run first removes an earlier go-live message it wrote, so a stale GO cannot be sent after a NO-GO or a STOP.

## Steps

Run the script as one plain `python3` command per call from the working folder, with paths as arguments: no `&&`, `|`, `cd` or loops. Read and find files with the file-reading and search tools, not shell commands. If a call is denied, retry the same plain `python3` command once; a denied `ls` says nothing about `python3`. Never work out the result yourself instead of running the script.

1. **Read BugHerd into the status file.** If `qa/<slug>/<slug>-bugherd-status.json` does not exist, run `python3 <skill-folder>/scripts/week5_handoff.py status-template --slug <slug>`; it lists the task ids from the task files and the tasks never created. Then fill it as `references/checks.md` says:
   - With the BugHerd connector: the project from the `BugHerd project:` line of `qa/routing.md` (else the one named for the client), list all its tasks including done and closed ones, and record each task's own status and severity. Add every task on the board, not only the template's ids.
   - Without the connector: use the statuses the PM gave you in the conversation, or ask the PM for them or for an export. Set `source` to say where they came from.
   - Never guess or carry over a status. A task you could not read stays blank; the check fails on it, which is right.
   - `deferred` holds the PM's reason, only when the PM deferred that task. CRITICAL findings cannot be deferred; say so if asked.
   - Set `read_on` to today. If the file already exists from an earlier sweep, update it in place and re-read every status.
2. **AM sign-off.** If `qa/<slug>/<slug>-am-review.md` has no sign-off line and the AM tells you in this conversation that they reviewed the staging site, add `AM sign-off: <their name>, <date>`. Otherwise leave it; the check fails and names the AM.
3. **Run the sweep.** `python3 <skill-folder>/scripts/week5_handoff.py run --slug <slug> --today <YYYY-MM-DD> --pm "<PM name>"` (`--pm` signs the go-live message; leave it out if not given). Never edit the handoff or the message by hand: fix the input and run again.
4. **No reply?** When the sweep passes on the no-reply path (`client not verified` in its Client edits row) and the user has not already said the client never replied, ask the PM or AM to confirm no reply came by email before you call it GO: a reply nobody has run client-feedback on yet looks the same.
5. **Report to the PM.** Lead with GO or NO-GO. On NO-GO list each blocking item with its owner, exactly as the script wrote them. On GO give the path of the go-live message and the launch toggles, and say the PM sends it to dev. Either way, list what is carried to post-launch, the Scope Changes for the PM/AM, any tasks to close in BugHerd, the client-not-verified note when the script wrote one, and the `## Notes` lines on what the QA re-run did not check.

## Rules

- The script decides GO or NO-GO. Do not soften a NO-GO or call a FAIL row minor.
- MINOR findings and MINOR tasks are post-launch backlog by definition and never block. MAJOR blocks unless the PM deferred it with a reason. CRITICAL always blocks, QA finding or client edit, whatever its deferral or BugHerd severity says; the task file's severity wins over BugHerd's.
- A QA finding the re-run marked FIXED whose BugHerd task is still open does not block; it goes under `## Close in BugHerd`.
- No reply from the client by the reply-by date is fine only when the email said we would go ahead without one (`No-reply line: yes`); the handoff then notes the client did not verify the site.
- Nothing here goes to the client. The go-live client email belongs to Week 6.
