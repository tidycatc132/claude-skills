# Merge rules

How to turn one source into the plan that `update_context.py apply` writes. The script rejects a plan that breaks the mechanical rules; the judgment rules below are yours.

## The plan file

`context-update-plan.json`, in the working directory:

```json
{
  "source": "intake",
  "source_file": "intake-submission.md",
  "date": "2026-11-03",
  "changes": [
    {"change": "resolved-gap", "section": "Competitors", "before": "GAP: two or three competitors", "fact": "Loses jobs mostly to Rooter Bros and Tacoma Drain Pros"},
    {"change": "updated", "section": "Services", "before": "Gutter cleaning", "fact": "Stopped offering gutter cleaning in August; refers it to a partner"},
    {"change": "conflict", "section": "Business Overview", "before": "three trucks", "fact": "CONFLICT: family-run with three trucks per the Sales call [transcript], five trucks per the intake form [intake]; the build uses five, the client's own written answer [transcript, intake]"},
    {"change": "added", "section": "Differentiators and Proof", "fact": "Licensed and bonded in Washington, license number on file"}
  ],
  "answers": {"1": "Rooter Bros and Tacoma Drain Pros, mostly."},
  "intake": {"Logo files": "received", "Team members": {"status": "missing", "note": "left blank on the form"}},
  "access": {"Hosting": {"status": "someone else manages it", "note": "previous web agency"}}
}
```

- `source`: `intake`, `call`, `client` or `user` (the kinds in SKILL.md). `source_file`: the file name, or `client-email-<date>` / `team-note-<date>` for pasted text. `date`: when the source was written (submission, call or email date), `YYYY-MM-DD`; today's date only when the source has none.
- `section`: a context heading without `## `, for example `Services`. Never `Sources`: the script adds the source's bullet there itself.
- `before`: enough of the existing bullet's text to match exactly one bullet in that section.
- `fact`: one line, no leading `- `. Leave the tag off and the script appends `[<source>]`; write tags yourself only when two sources agree (`[transcript, intake]`) or for a `CONFLICT:`.
- `answers`, `intake`, `access`: optional; include only what this source settles. Statuses not mentioned keep their current value (or the default on the first run).

## Change types

| Change | Use when | `before` |
|---|---|---|
| `added` | A new fact with no bullet on that topic yet. | none |
| `updated` | The source changes or adds to an existing fact and the source is the better authority (see below), or confirms it (then keep the text and merge the tags, `[transcript, intake]`). | the old bullet |
| `resolved-gap` | The source answers a `GAP:` bullet. The fact states the answer, never "answered". | the `GAP:` bullet |
| `conflict` | The source disagrees with an existing fact and neither clearly wins, or the topic is scope. | the old bullet |

A fact says only what the source says, in its terms. Do not borrow the gap question's framing ("wants to reach", "plans to") when the source only lists something, and do not write about the source itself ("listed on the form", "X is not listed"): a form that lists Independence under service areas gives `Serves Independence`, not `Wants to reach Independence`.

When a source changes a fact, change every bullet that states the old version (Snapshot often repeats a section), so the context never says both.

One topic per bullet. Do not paraphrase existing bullets you are not changing. A partial answer resolves the gap only for what it answers; write the rest as an `added` bullet only if it is a fact, never a new `GAP:` (the script rejects new `GAP:` bullets; open questions go to the Kickoff Call through the missing items and Open Items).

When an `R` item in `## Open Items` is now answered, add an `updated` change to that bullet saying so and where (`R6 Competitors: answered in intake form`); no tag needed in `## Open Items`.

## Which version wins

- **Scope never moves.** The scope source (SOW, or the signed deal terms) owns `## Scope Summary`. A page count, deliverable or service promised on a call, asked for by the client or written on the form is a `conflict` bullet in `## Scope Summary` that quotes it, names who said it, and says the build follows the scope source until a signed change. The `SOW pages:` line stays as it is.
- **Business facts: the client's own, newer word wins** over the Sales transcript and the site, when it is direct and specific (the form, the client on the Kickoff Call, a client email). Use `updated` when the change is plainly a change over time ("we stopped doing X in September"); use `conflict` when it reads like a contradiction (a different founding year, a different count) so the AM confirms it. A `CONFLICT:` bullet keeps every other detail of the old bullet, gives both versions with their tags inside the sentence, says which one the build follows for now, and ends with both tags.
- **Team notes** (`user`) win on what WISE itself has checked: access that arrived, whether a website exists, what the scope source says. On anything else about the business they are a `conflict` for the AM to confirm.
- **A later source can settle an open `CONFLICT:`**: use `updated` with the `CONFLICT:` bullet as `before` and the settled fact (tagged with every source that supports it) as `fact`; the change log keeps the conflict.
- **Only a real difference is a scope conflict.** A page count or deliverable that differs from the scope source is a `conflict`; a remark that does not contradict it (a delivery date for an interim deliverable, a restated scope) is no change, or an `added` bullet if it is a new fact.
- **Second-hand statements** (the AM's summary of what the client meant, "I think they said") do not override anything; add them only if no bullet covers the topic, tagged with their source.

## Where facts go

| Source content | Section |
|---|---|
| Services offered, stopped, prioritised | `## Services` |
| Who buys, segments, areas served (`NAP Service Areas`) | `## Customers and Service Area` |
| Founding year, team size, ownership, location count, hours, address | `## Business Overview` |
| Goals, conversion action, booking or phone preferences | `## Goals and Conversion` |
| Why clients choose them, accreditations, results, numbers (`CNT Credentials`) | `## Differentiators and Proof` |
| Competitors named | `## Competitors` |
| The current website, its platform and what to keep (`ACC Website Platform` when it describes the site) | `## Website Today` |
| Page counts, deliverables, scope requests | `## Scope Summary` (a `conflict` when it differs from the scope source, otherwise an `added` fact) |

Websites the client names as design references are both: mark `Sites they like` received and add the names (and URLs if given) as a fact under `Goals and Conversion`, since the design brief reads them from the context. Other contact names and emails, approvers, logos, photos, testimonial text, preferences and access details are not context facts: they go in the missing items file as statuses and short notes. A testimonial's existence can be a fact in `## Differentiators and Proof` ("two client testimonials supplied on the intake form"); do not copy testimonial text into the context.

## Gap answers

The form's `GAP Answers` field (and any later source) answers the numbered questions in `<slug>-gap-questions.md`. For each question with a real answer: put the client's answer, close to their words, in `answers` under its number, and resolve the matching `GAP:` bullet in the context (or update the matching fact). A blank, "not sure" or "let's discuss" answer is not an answer: leave the question blank and the gap open. A question already answered by an earlier source is not answered again; a new answer that differs is a `conflict` in the context.

## Intake items

Item names are fixed (the script rejects others): `Primary contact`, `Website approver`, `Business name, address, phone and hours`, `Logo files`, `Brand guidelines`, `Photos`, `Testimonials or reviews`, `Team members`, `Certifications, awards and memberships`, `Legal or compliance language`, `Sites they like`, `Things to avoid`, `Gap question answers`.

Statuses: `received` (supplied), `partial` (some supplied, more expected, for example 2 of 3 gap answers), `missing` (blank or not yet sent), `none` (the client says they have none, for example "no brand guidelines" or photo status "No, plan for stock"), `n/a` (does not apply). The note says what arrived or what is still owed, in a few words. A blank form field is `missing`, never `none`.

## Platform access

Platform names are fixed: `Domain`, `Hosting`, `Website login`, `Google Analytics`, `Google Search Console`, `Google Business Profile`, `Google Tag Manager`, `Google Ads`, `Meta ads`, `Microsoft Ads`, `CRM, forms or call tracking`.

| Form option or source says | Status |
|---|---|
| Access verified by WISE (Dev or the AM says the invite arrived and works) | `confirmed` |
| Invite sent | `invite sent` |
| I need help | `needs help` |
| Someone else manages it | `someone else manages it` (note: who) |
| We don't have this | `not set up` |
| Not sure | `not sure` |
| Blank | `no answer` |
| Not needed for this build | `n/a` (note: why) |

Only WISE confirms access: a client saying "invite sent" is `invite sent`, not `confirmed`. The client holding an account and offering to add us is `no answer` until an invite is sent (note: who holds it). On the first run the script defaults the three ad platforms to `n/a` when there is no paid media brief in the folder, and `Website login` to `n/a` when the URL inventory is empty (no current website); override with a status when a source says otherwise (for example a source describes a live site: set `Website login` to `no answer`). The note may name the provider and the account holder; never a username, password or code.

## Never

- Copy a password, login, PIN or security code into any file, note or the chat answer. Leave it out and name only the field it was in.
- Delete a fact. Replace it with `updated` or `conflict` so the change log keeps it.
- Invent a fact, number, name or credential the source does not contain.
- Edit `<slug>-context.md`, `<slug>-change-log.md` or `<slug>-missing-items.md` by hand.
