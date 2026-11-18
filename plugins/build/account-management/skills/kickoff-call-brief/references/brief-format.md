# Brief format

The checker (`kickoff_call_brief.py check`) enforces every rule marked **(checked)**. The others are judgment.

## Layout

- Line 1: `Client: <Client Name>`, the name exactly as on the context's first line. **(checked)**
- Then a blank line and `# Kickoff Call brief for <Client Name>`. **(checked)**
- Then the six `## ` sections below, in this order, and no other `## ` heading. **(checked)**
- At most 120 lines in all. No placeholders such as `[FILL ...]` or `<...>`. **(checked)**

## `## Call Goals`

1 to 5 bullets **(checked)**: what the AM must leave the call with, most important first. Each bullet is an outcome ("Settle the primary way new clients should contact the firm"), not a topic, and ends with the ids of the open items it covers in parentheses, `(R4, Q1)`, `(access)` when it is about the Access to Confirm list, or source tags such as `[transcript]` (only the context's tags: transcript, site, sow, notes, user, maps, intake, call, client) when it restates a known fact. **(checked)** A goal never introduces a fact the context does not state.

Good goals usually cover: the questions that block the sitemap or homepage (conversion action, priority services, service area, page count), the scope items to confirm, and access that blocks Week 1 work.

## `## What We Know`

1 to 10 bullets **(checked)**, each a bullet copied word for word, source tag included, from the list `items` prints (tagged context facts outside Scope Summary, Open Items and Sources; never a `GAP:` or `CONFLICT:` bullet). **(checked)** Bullets only, no prose. **(checked)**

Pick what the AM should have in mind when talking to this client: who the client is, the services that matter most to grow, the ideal customer, the service area, the main goal, the strongest differentiators, and the main competitor. Skip what the call does not touch (internal tools, kickoff date). Do not shorten or merge bullets; choose shorter ones instead.

## `## Questions to Settle`

A numbered list, one line per group that `items` prints under "Questions to Settle". **(checked)** Each line is `N. (<ids>) <what to ask>`, with the ids exactly as printed, in the printed order (`(R4, Q1)`). **(checked)** When two printed groups ask the same thing (a `GAP: two or three competitors` bullet and `R6, Q1`), merge them into one line, `(G1, R6, Q1)`, so the client is not asked twice; each group's ids stay together in their printed order. **(checked)** Every open id appears exactly once in the brief, answered ones never. **(checked)**

The text after the ids is what the AM says on the call, in plain words a business owner understands, at least four words: **(checked)**

- For an `R` item asked in a gap question (`R4, Q1`): ask the gap question again, shortened if it is long.
- For an `R` item left for the call: ask for what the requirement needs (see the R list below).
- For a `G` gap: ask for the missing fact.
- For a `C` conflict: give both versions and ask which is right ("Sales heard 2009, the intake form says 2011: which year did you start?").

Never write internal notes ("asked in Q1", "left for the call") as the question. No SEO jargon. Order the lines by what blocks the build most; the ids stay attached to their line.

R list: R1 services and which to grow; R2 customer types; R3 service area; R4 main goal and primary conversion action; R5 differentiators; R6 competitors; R7 page count and page list; R8 current pages to keep or redirect; R9 launch timing; R10 results, numbers, guarantees.

## `## Scope to Confirm`

- First two lines, copied exactly from `items` **(checked)**:
  - `- Page count in scope: <value from the SOW pages: line, with its tag>`
  - `- Paid media: <in scope | interest only | not in scope>` (in scope when `<slug>-paid-media-brief.md` exists; interest only when Scope Summary has a `GAP:` bullet about paid media).
- Then one bullet per group printed under "Scope to Confirm" (`R7`, and every `GAP:` or `CONFLICT:` in Scope Summary): `- (<ids>) <what to confirm>`. **(checked)** Quote who promised what and say the scope source still decides; the AM confirms, never agrees to more pages or deliverables on the call.

## `## Access to Confirm`

The lines `items` prints, copied exactly, in the same order. **(checked)** They come from the missing items file's Kickoff Call Agenda (minus the gap answers item, which Questions to Settle covers), or, before the intake form is merged, a `no record yet` line per intake item and platform.

## `## Relationship Notes`

The heading and nothing under it: the AM fills it in. **(checked)**

## Example

Invented client, shortened:

```
Client: Northgate Pool Care

# Kickoff Call brief for Northgate Pool Care

## Call Goals
- Settle how new customers should reach Northgate first (R4, Q1)
- Confirm the page count before the sitemap starts (C2)
- Get Search Console and Business Profile access moving (access)

## What We Know
- Weekly pool maintenance is the service the owners most want to grow [transcript]
- Serves Mesa, Gilbert and Chandler [transcript, intake]

## Questions to Settle
1. (R4, Q1) When someone finds you online, should they call, fill out a form, or book a visit?
2. (C1) The Sales call said 12 technicians, the intake form says 9: how many are on the team today?
3. (R9, Q3) Is there a date the site has to be live by, such as before summer?

## Scope to Confirm
- Page count in scope: 10 [sow]
- Paid media: not in scope
- (C2) Sales mentioned "a page for every city"; the SOW says up to 10 pages, so confirm city pages fit inside the 10 or need a signed change.

## Access to Confirm
- Google Search Console: not sure
- Google Business Profile: invite sent

## Relationship Notes
```
