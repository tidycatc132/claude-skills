---
name: optimization-task-pusher
description: Convert approved paid media recommendations (from weekly optimization, audits, anomaly triage, policy reviews, or QBR plans) into ClickUp tasks with clear titles, descriptions, owners, due dates, priority, client and platform tags, expected impact, approval status, source links, dependencies, and checklists, avoiding duplicates with existing tasks. Use whenever the user says push these to ClickUp, create tasks from the recommendations, assign the optimization work, log the changes, turn the audit into tasks, or put the action items in the task board, even if they do not name ClickUp.
---

# Optimization Task Pusher

Recommendations that stay in a document do not happen. The handoff from analysis to execution is where most paid media improvements die: unclear owners, no due date, missing context, or duplicates of tasks someone already opened. This skill turns the approved actions into well-formed tasks a person can pick up and finish without asking questions.

## Principle: approved, specific, owned, and traceable
Only create tasks for actions a human has approved or that are explicitly marked as not needing approval. Each task states exactly what to change, where, by how much, why, and what result to expect, and links back to the evidence. One action per task.

## Inputs
- The source output (weekly optimization, audit, triage, or plan) and the list of approved actions; if approval status is unclear, create nothing for unapproved items and list them back as awaiting approval
- `clients/<slug>/context.md`: client name, owners, ClickUp location, approver, naming conventions
- ClickUp workspace structure: the client's space, folder, or list; status names; custom fields; assignee mapping
- Existing open tasks for the client (to detect duplicates)

## Process
1. **Find the destination.** Look up the client's list in ClickUp. If several candidates exist, choose the one for paid media; if none exists, report that and propose a location rather than creating clutter.
2. **Determine today's date and time zone** from the ClickUp user's current time before converting relative dates; never compute dates from your own clock.
3. **Check for duplicates.** Search existing open tasks for the same client, platform, and subject. If a matching task exists, add a comment with the new evidence instead of creating another, or update the existing task, and report what was merged.
4. **Write each task:**
   - **Title:** verb first, specific, with client and platform tags following the naming convention (for example `[Google Ads] Add 42 negative keywords to Plumbing campaigns`)
   - **Description:** what to change (exact campaign names, values, and file references), why (the evidence and numbers), expected impact with range, risk and rollback, how to verify success, and the link to the source document or change sheet
   - **Attachments:** the change sheet or build file, where applicable
   - **Owner:** assign by role mapping (search specialist, social specialist, creative, tracking, developer, account manager) to the actual people in the workspace
   - **Due date:** based on priority and learning-period or dependency constraints (for example, do not schedule a bid strategy change within 14 days of the last one); mark urgent items (tracking broken, billing failure) as high priority with same-day dates
   - **Priority and tags:** by expected impact and urgency, with platform and client tags
   - **Approval field:** who approved and when, or the approver needed
   - **Dependencies:** link tasks that must happen in sequence (build, then policy review, then launch)
   - **Checklist:** the steps to execute and the verification step, including logging the change
5. **Add follow-up tasks** where the plan calls for them: a review task after the evaluation window with the metric and threshold to check, and a monitoring task for items on the monitor list with the date they become judgeable.
6. **Create the tasks in one batch** where the tool supports it, then verify by reading them back (count, owners, dates).
7. **Report back** with a summary table of tasks created, merged, and skipped.

## Output
Return to the lead:
```
Tasks created: count and a table (title as an inline link, owner, due date, priority).
Tasks merged into existing: list with reasons.
Skipped: unapproved or ambiguous items awaiting a decision.
Issues: missing owners, missing list, conflicts with learning periods.
```
When mentioning ClickUp tasks, use inline markdown links with the task name as the anchor text, not bare URLs.

## Rules
- Do not create tasks for unapproved recommendations. Do not assign work to people who are not in the workspace; flag the gap.
- Never modify or delete existing tasks beyond adding context or updating fields the user asked for.
- Do not put sensitive client data (lead details, credentials) in task descriptions.
- Do not apply the changes in the ad accounts; this skill only creates the work items.
