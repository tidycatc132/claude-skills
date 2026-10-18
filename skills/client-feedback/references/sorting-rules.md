# Sorting rules

How to turn the client's reply into `feedback-plan.json`. The script rejects a plan that breaks the mechanical rules (marked **checked**); the judgment is yours.

## The plan file

```json
{
  "date": "2026-12-02",
  "from": "feedback-email.txt",
  "contact": "Lena Ortiz",
  "am": "Sam Reyes",
  "items": [
    {"feedback": "The copy is spot on, no changes from us.", "type": "approval", "affects": "homepage copy", "impact": "none", "action": "Record approval of the copy; no changes", "owner": "AM"},
    {"feedback": "Could the second design use our cream and rust colors instead of grey?", "type": "design", "affects": "homepage design: Option 2", "impact": "low", "action": "Recolor Option 2 in the brand cream and rust", "owner": "Design"},
    {"feedback": "We'd love an online ordering page for custom cakes too.", "type": "scope", "affects": "site scope", "impact": "high", "action": "Tell Lena online ordering is beyond the SOW; send a change order if she wants it", "owner": "AM", "verdict": "outside", "pages": null, "basis": "Online ordering is not among the SOW's included services."}
  ],
  "facts": [
    {"section": "Services", "fact": "Custom cakes now need two weeks' notice", "evidence": "custom cakes need two weeks' notice now"},
    {"section": "Scope Summary", "fact": "CONFLICT: Lena Ortiz asked for an online ordering page for custom cakes; the SOW includes website design and build and on-page SEO only (SOW pages: 8); the build follows the SOW until a signed change", "evidence": "We'd love an online ordering page for custom cakes too."}
  ],
  "reply": {"subject": "Re: your homepage is ready to review", "body": "Hi Lena,\n\n..."}
}
```

- `date`: the day the client wrote, from the email's date line (**checked** `YYYY-MM-DD`); today only when the text has no date. `from`: the feedback file name. `contact`: the full name of the person who wrote, as they sign or as the context names them. `am`: the AM's full name, or `""`.
- `items`: in the order the client raised them. `facts` and `reply` are described below. `pages`, `verdict` and `basis` belong to scope items only (**checked**).

## Splitting the reply into items

- One item per point the team acts on or answers. A paragraph with a fix and a question is two items; three sentences about one change are one item.
- `feedback` is the client's own words, copied exactly, cut to the part that carries the point (**checked**: verbatim from the client's text, at most 300 characters, one line, no `|`; drop a sentence rather than edit it).
- Every question the client asks must sit inside some item's quote (**checked**), including a "Can you do that?" after a request; put it in the request's quote.
- Greetings, thanks and small talk are not items. Logins or passwords are never quoted (see Secrets).
- A file the client sent ("logo attached") or an access step they took ("I invited you to Analytics") is a `content` item (it feeds the build) with Affects `intake items` or `platform access`, Impact `none`, owner `AM` (log it and confirm receipt) or `Dev` (accept the invite), and also a fact (below).

## Types

| Type | When | Impact |
|---|---|---|
| `approval` | The client signs off on something as it is ("the copy sounds like us", "go ahead with Option A"). | `none` (**checked**) |
| `content` | A change to the words: a wrong fact in the copy, a headline they dislike, a service to add to the homepage. | `low` for a word or fact fix, `medium` for reworking a section |
| `design` | A change to how it looks, or a choice between options ("we like the second one", "use our brand red"). | `none` for a plain pick, `low` for a colour or detail, `medium` for a layout change, `high` for a new direction |
| `scope` | A request for pages, deliverables or services the build may not include (more pages, a new page type, a blog, a second language, a logo). | `high` (**checked**) |
| `question` | The client asks something the AM answers. | `none` or `low` (**checked**) |

A request that changes the copy because the business changed ("we cater weddings now, mention it under cakes") is `content`, with the new fact also in `facts`. A request is `scope` only when it adds to what is built, not when it changes what is on the homepage.

When the client picks a design option, the pick is one item; each change they want to it is its own item.

## Affects, action, owner

- Affects: `homepage copy` and `homepage design` for the Week 1 deliverables, `site scope` for scope items (**checked**), `timeline` for dates and launch questions, `platform access` and `intake items` for access and files, `client context` for a fact with nothing to change on the page, `other` for anything else. Add a detail after a colon when it helps: `homepage design: Option B`.
- Action: one imperative line saying what happens next, specific enough to do ("Change the opening hours in the footer to 7am"). For an approval: "Record approval; no changes".
- Owner: `Content` for copy changes, `Design` for design changes, `SEO` for page or keyword questions inside scope, `Dev` for access invites to accept, `AM` for questions, approvals, files received, timeline and every scope request outside or unclear (**checked**).

## Scope requests

Compare each scope request with the scope source that `feedback.py scope` prints: `SOW pages`, `Included services`, the quoted scope lines and the `Excluded:` bullets.

- `outside`: the request goes beyond what the scope source allows (more pages than the count or the page-type limits, a service listed as excluded or not listed). More pages than the whole `SOW pages` count is always outside (**checked**); page-type limits in the quoted scope line ("up to 2 location pages") are yours to compare, and the script cannot check them.
- `unclear`: the scope source cannot settle it, typically deal terms with `SOW pages: unknown`; `within` is never allowed then (**checked**).
- `within`: the scope source plainly covers it. Not a conflict.
- `pages`: the number of pages asked for when the client gives one, else `null`. `basis`: one sentence comparing the request with the scope source in plain words.

Each `outside` or `unclear` request also needs a `Scope Summary` fact (**checked**), in client-context-update's conflict form: it starts `CONFLICT:`, quotes or names what the client asked for, gives the scope source's line, and ends that the build follows the scope source `until a signed change` (**checked**). The plan example above shows one.

## Facts for the context

Facts are what the client told us about the business or the project that the context should hold. Each becomes one row of the updates file, and client-context-update decides how it merges, so state the fact as the client states it.

- `section`: a context heading without `## ` (`Snapshot`, `Business Overview`, `Services`, `Customers and Service Area`, `Goals and Conversion`, `Differentiators and Proof`, `Competitors`, `Website Today`, `Scope Summary`), or `Platform Access` or `Intake Items` (**checked**).
- `fact`: one plain statement, no source tag (**checked**), no number that is not in the client's text, the context or the date (**checked**).
- `evidence`: the client's own words, copied exactly (**checked**); the script writes it as `<contact> (email): "<quote>"`.
- A correction to the copy that is also a business fact (a wrong opening year) is a fact; a wording preference (the headline is stiff) is not.
- `Platform Access` facts start `<Platform>: <status>` with names and statuses as client-context-update uses them: platforms `Domain`, `Hosting`, `Website login`, `Google Analytics`, `Google Search Console`, `Google Business Profile`, `Google Tag Manager`, `Google Ads`, `Meta ads`, `Microsoft Ads`, `CRM, forms or call tracking`; statuses `invite sent`, `needs help`, `someone else manages it`, `not set up`, `not sure`, `no answer`, `n/a` (**checked**). A client never makes access `confirmed`; only WISE does after checking the invite. A client who sends a login instead of an invite is `no answer`, with a note that an invite is still needed.
- `Intake Items` facts start `<Item>: <status>` with the item names and statuses of client-context-update (`Logo files: received`, `Photos: partial, team photos still to come`) (**checked**).
- A design pick or approval is not a context fact.

## Secrets

If the client's text contains a login, username, password, PIN or code, it goes nowhere: not in a quote, a fact, the reply or your answer (**checked**: the script refuses a plan that carries one and checks the files). Record the point as a `platform access` item ("Ask for an invite instead of a login; suggest changing the password"), and have the reply ask for an invite and suggest changing the password, without repeating it.
