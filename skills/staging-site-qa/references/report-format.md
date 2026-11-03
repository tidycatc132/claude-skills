# File formats

## Review notes: `qa/<slug>/<slug>-review-notes.md`

Written by you, only when you have Design findings or AM items to add. Both sections are optional.

```
## Design Findings

| Page URL | Severity | Finding | Fix | Evidence |
|---|---|---|---|---|
| /about/ | MAJOR | The crew photo is cut off on mobile. | Crop the photo to the 3:2 frame on small screens. | qa/<slug>/screens/about-mobile.png |
| /services/drain-cleaning/ | MINOR | The header photo is 800 x 450; the checklist asks for 1600 x 900. | Upload the 1600 x 900 WebP. | asset checklist: Service header photo (2): 1600 x 900, WebP |

## AM Items

- The client has not sent the team photo for the about page.
```

`report` rejects a row whose page is not a Build page, whose severity is not CRITICAL, MAJOR or MINOR, or whose evidence is not a screenshot from this scan or a line of the asset checklist, copied exactly.

## Routing: `qa/routing.md`

Kept in the client's working folder (never in a shared repo), filled once by the PM.

```
BugHerd project: <project name or id>

| Department | Column | Assignee |
|---|---|---|
| Content | Copy Review | <name> |
| SEO | SEO Review | <name> |
| Design | Design Review | <name> |
| Development | Dev Ready | <name> |
```

Without the file, columns default to Content `Copy Review`, SEO `SEO Review`, Design `Design Review`, Development `Dev Ready`, and `assignee` is empty until the PM names someone.

## Report: `qa/<slug>/<slug>-staging-qa-<YYYY-MM-DD>.md`

```
Client: <client>
Checked: <date>
Staging: <base URL> (saved pages: <folder>/)
Dev handoff index: <path> (<its last line>)
Design QA and dev prep: <path or none>
Compared with: <earlier report path> | none (first run)
Screenshots: qa/<slug>/screens/ (<n> files) | none (<reason>)

# Staging QA: <client>

## Summary

Pages checked: <n> of <n> Build pages (<n> missing on staging); skipped (not Build): <n>
Open findings: <n> CRITICAL, <n> MAJOR, <n> MINOR
By department: Content <n>, SEO <n>, Design <n>, Development <n>
Re-run: <n> FIXED, <n> OPEN, <n> NEW          (re-runs only)
AM items: <n>
Launch toggles: <n>
Structured data: not in the current process

## Findings

| # | Page URL | Department | Severity | Finding | Fix |
|---|---|---|---|---|---|
| QA-76c273e5 | /about/ | SEO | MAJOR | The meta title is "..."; the approved title is "...". | Set the meta title to "...". |

## Re-run Status                                  (re-runs only)

| Finding ID | Status | Page URL | Department | Severity | Finding |

## Launch Toggles
## AM Items
## Not Checked

RESULT: READY | CONDITIONAL | NOT READY
```

The `Staging:` header line is read by client-feedback for the staging base URL (contract `staging-site-qa-to-client-feedback`). The Findings table holds open findings only (first run: all; re-run: OPEN and NEW), CRITICAL first. FIXED findings appear only in Re-run Status. A pipe inside a cell is written `\|`. Design findings end with `(seen in <screenshot>)` or `(asset checklist: <line>)`.

## Task file: `qa/<slug>/<slug>-bugherd-tasks.json`

A JSON list, in Findings table order, then the FIXED findings of a re-run:

```
{
  "finding_id": "QA-76c273e5",
  "status": "NEW",                 NEW | OPEN | FIXED
  "create": true,                  true only for NEW with no bugherd_task_id
  "bugherd_task_id": "",           filled by `qa.py created` once the task exists; carried to later runs
                                   (a FIXED object keeps it for closing; a finding that returns after FIXED gets a new task)
  "page_url": "https://<staging host>/about/",
  "department": "SEO",             Content | SEO | Design | Development
  "column": "SEO Review",
  "assignee": "<name or empty>",
  "severity": "MAJOR",             CRITICAL | MAJOR | MINOR
  "bugherd_severity": "important", critical | important | minor
  "title": "/about/: The meta title is ...",
  "description": "<finding> <fix> (Staging QA <date>, <finding_id>)"
}
```

`check` passes only when the open objects match the Findings table row for row, every object has all the keys above, `create` is true exactly for NEW findings with no `bugherd_task_id`, re-run statuses match the Re-run Status table, and no title or description holds internal wording.
