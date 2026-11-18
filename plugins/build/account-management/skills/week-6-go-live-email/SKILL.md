---
name: week-6-go-live-email
description: Drafts the Week 6 go-live confirmation email a WISE PM sends a website client when the new site is ready to launch. A script reads the Week 5 handoff, the dev handoff index, the client context and voice file, prints the header and the real page count, then checks the draft (under 200 words, page numbers match the index, only the integrations the PM named, no internal terms, no structured data claim) and writes a warning above the email when the Week 5 handoff is missing or not GO. Use when the PM asks for the go-live email, the launch confirmation email, or to tell the client the site is ready to launch or confirm the agreed launch date. Do NOT use for the Week 5 staging review email (use week-5-client-email), the go message to dev (use week-5-handoff-check), the post-launch transition email or close-out (use project-close-out), or other client emails (use week-1-client-email, week-2-client-email, welcome-email).
---

# Week 6 go-live email

The first Week 6 step. Staging is signed off, the Week 5 final sweep said GO, and the PM now tells the client the site is ready: either asking them to confirm they are ready to go live, or confirming the launch date and time already agreed. You draft the email; the PM sends it. A script supplies every fact (header, page count, warnings) and checks the draft, so the email only says what was built.

## Inputs

All paths are relative to the client's working folder; `<slug>` is the client folder name.

| Input | From | What is read |
|---|---|---|
| `handoff/<slug>/<slug>-week-5-handoff.md` | week-5-handoff-check | the last line, `GO` or `NO-GO`; `Checked:`; the `## Blocking` items (counted, never quoted) |
| `handoff/<slug>/<slug>-dev-handoff-index.md` | dev-handoff-index | each page block's `Page` and `Priority` under its group heading; only `Build` pages count |
| `kickoff/<slug>/<slug>-context.md` | new-build-kickoff | `- Name:` (business name) and a `- Primary contact:` or `- Contact:` line |
| `client-reference/<slug>/voice.md` | client-reference-kit, optional | the Email row of the Tone Matrix |
| Launch date and time | the PM, at run time, optional | `--launch "YYYY-MM-DD HH:MM"` (time optional) |
| Integrations going live | the PM, at run time | `--integrations "contact form; live chat"`, exactly what the PM named |
| Sender | the PM, optional | `--sender "<name>"` and `--role "<role>"` |

## Output

`emails/<slug>/<slug>-go-live-email.md`:

1. Warning lines (`WARNING: ...`) and a blank line, only when the Week 5 handoff is missing, ends `NO-GO`, or ends neither. The check script writes and removes these; never write them yourself. They sit outside the email and the PM deletes them before sending.
2. The header, six lines, exactly as `facts` prints them: `Client:`, `To:`, `Week 5 handoff:` (path and `(GO)`, `(NO-GO)`, `(no result line)` or `(missing)`), `Pages launching:` (total and count by group), `Launch:` (`client to confirm` or the agreed date and time), `Integrations:` (as named, or `none named`).
3. A blank line, then `Subject: <subject>`.
4. The body, under 200 words from the greeting to the sign-off. Content rules: `references/email-rules.md`. Load it before you write the body.

## Steps

Run the script as one plain `python3` command per call from the working folder, with paths as arguments: no `&&`, `|`, `cd` or loops. Read and find files with the file-reading and search tools, not shell commands. If a call is denied, retry the same plain `python3` command once.

1. **Collect the run-time facts.** From the request: the agreed launch date and time if there is one, the integrations going live as the PM named them (forms, live chat, analytics, Juvo, booking and so on), and who signs. If the PM named no integrations, do not invent any: pass none and the email lists none. If the PM says they are the PM, pass `--role "Project Manager"`; with no sender, the sign-off is the default `Account Manager, WISE Digital Partners`.
2. **Get the facts.** `python3 <skill-folder>/scripts/golive_email.py facts --slug <slug> [--launch "..."] [--integrations "..."] [--sender "..."] [--role "..."] [--contact "..."]`. If it prints `Contact: unknown`, ask the PM who the email goes to and pass `--contact`. If it stops because the index or context is missing, tell the PM which skill to run first.
3. **Write the email** to `emails/<slug>/<slug>-go-live-email.md`: the header exactly as printed, a blank line, the Subject line, then the body following `references/email-rules.md` and the voice row `facts` printed.
4. **Check it.** `python3 <skill-folder>/scripts/golive_email.py check --slug <slug>` with the same options as `facts`. It writes the warning lines at the top, then prints PASS or FAIL for each rule. Fix every FAIL in the email (never by changing the facts) and run it again until it passes. When a later final sweep ends GO, run `facts` and `check` again: the warning goes and the `Week 5 handoff:` header line must change to `(GO)`.
5. **Report to the PM.** Give the path and the subject, and say the check passed. If a warning was written, lead with it, in these words: do not send this email yet; the Week 5 handoff is missing (or ends NO-GO, with the number of blocking items), and it goes only after a new week-5-handoff-check run ends GO. Then say they run this skill's check again and the warning is removed. Say the PM sends the email; you never send it.

## Rules

- The page count is the number of Build pages in the dev handoff index. Pages marked Post-Launch are not counted or named.
- Only integrations the PM named go in the email. Never claim structured data, schema, Juvo, live chat or analytics unless the PM named it. The script polices forms, live chat, analytics, Juvo and booking; anything else (newsletter, payments, CRM) is on you.
- Nothing internal reaches the client: no QA, BugHerd, severities, GO or NO-GO, handoff, deferred items or blocking items, even when the handoff lists them.
- A missing or NO-GO handoff does not stop the draft; the warning does the stopping. Never soften it or remove it by hand.
