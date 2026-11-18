# Week 2 reply and nudge

The Week 2 email (week-2-client-email) sends the Growth Blueprint deck and the page content and asks three questions: Does this feel right? Does anything surprise you? Is anything missing? It asks for an answer by its `Reply by:` date. Everything in Sorting Rules and Reply Voice still applies; this file adds what changes for that reply, and the nudge when no reply comes.

## Files read

From the working folder (the folder holding `kickoff/`):

- `blueprint/<slug>/<slug>-growth-blueprint.md` (growth-blueprint). Required: without it the script refuses a Week 2 plan. Its `##` sections are the names `Affects` and `changes` may use: `Executive Summary`, `Business and Market Overview`, `Competitive Analysis`, `Strategic Positioning`, `Keyword Opportunity`, `Site Architecture and Content Plan`, `Growth Strategy`, `Measurement and Next Steps`.
- `content/<url-slug>/article.md` (seo-content-writer), one folder per page. The folder name (`<url-slug>`, not the file path) is the page's name in `Affects` and `changes`; the Summary expands it to the file path.
- `emails/<slug>/<slug>-week-2-email.md` (week-2-client-email), when it exists: its `Reply by: YYYY-MM-DD` line goes into the report header and drives the nudge (with `Send date: YYYY-MM-DD`), and its figures may be repeated in the reply. Only three header lines are read: `Client:`, `Send date:` and `Reply by:`, both dates as `YYYY-MM-DD` (contracts `week-2-client-email-to-client-feedback` and `growth-blueprint-to-client-feedback` pin the header and the section names; `feedback.py contract` prints what is read). Once that email exists, a plan without `"week": 2` for a reply that mentions the Blueprint or the deck is refused (**checked**).

`feedback.py scope kickoff/<slug> --week 2` prints all of these, with the deck slides each Blueprint section feeds.

## The plan

Add `"week": 2`. Each item may carry `changes`: `{"blueprint": [sections], "pages": [url-slugs]}`. The script works out the deck slides from the sections and writes the Impact cell as `<level>: Blueprint <sections>; deck slides <numbers>; pages <url-slugs>`.

```json
{"feedback": "We'd much rather lead with dental and wellness, that's where we want to grow.",
 "type": "strategy", "affects": "blueprint: Keyword Opportunity", "impact": "high",
 "action": "SEO decides whether dental and wellness move up to Tier 1, then updates the Blueprint", "owner": "SEO",
 "changes": {"blueprint": ["Executive Summary", "Keyword Opportunity", "Growth Strategy"], "pages": ["emergency-vet", "home"]}}
```

## Types in a Week 2 reply

`strategy` joins the five types. It is a point that changes the Blueprint's direction: which keywords or services lead, the positioning or a claim it rests on, which pages the sitemap holds or how they rank in priority (without adding pages to the build). It is owned by `SEO`, affects `blueprint: <section>`, and has impact `medium` (one section, wording or emphasis) or `high` (priorities or the sitemap, several sections and pages) (**checked**).

- Asking for more pages than the build includes is still `scope`, judged against the scope source as in Sorting Rules. A `within` request changes `Site Architecture and Content Plan` (**checked**); an `outside` or `unclear` one changes nothing until a signed change, so it has no `changes` (**checked**).
- A wrong fact or wording on one page is `content`, with `affects` `page: <url-slug>` and that page in `changes.pages` (**checked**). If the same fact also sits in the Blueprint, add the section.
- "The direction feels right", "the sitemap makes sense" is `approval` with `affects` `blueprint: <section>`, no `changes`.
- `homepage design` still applies when the client answers about the homepage options in this reply.

Every item that changes something lists everything it changes: the sections, then the pages built on them (a new keyword priority usually changes the Executive Summary, Keyword Opportunity, Growth Strategy and the pages that led with the old priority). Questions and approvals change nothing (**checked**).

## SEO review

The report gets a `## SEO Review` section before the reply. With any strategy item it says `Status: hold the reply until SEO signs off the items below` and lists each one; the AM does not send the reply until SEO has decided. With none it says the reply can go once the AM has read it (**checked**). In your answer, say plainly which items wait for SEO.

## The reply

Follow the Week 2 email's framing: answer what felt right, what surprised them and what is missing, in that order where the client raised them, about the overall direction, the sitemap and the page content.

- Name the Blueprint or the deck (**checked**).
- For each strategy point: thank them, show you understood the reason, and say SEO will review it and the AM comes back before the plan changes. Never say the Blueprint, priorities or positioning have already changed, and never promise the change before the review. The script catches the plain cases (a sentence naming the Blueprint, deck, priorities, keywords, positioning, sitemap, strategy or direction that says "we've updated" or "we'll switch" without a review or a hand-back); the rest is yours, and the SEO hold stops the send either way.
- Page fixes (a wrong fact, a misspelt name) can be agreed plainly.
- Scope, secrets, numbers and the 300-word cap work as in Reply Voice. The reply-by date and figures from the Week 2 email or the Blueprint may be repeated.

## No reply by the reply-by date: the nudge

When the client has not answered and the Week 2 email's `Reply by:` date has passed, write a short nudge instead of a feedback file.

Run each step as the one plain `python3` command shown, exactly as in SKILL.md; check for an existing reply with the file-search tool, not `ls`. A nudge only in chat is not done: the file and the check's `RESULT: PASS` are.

1. Write `nudge-plan.json`: `{"contact": "<full name>", "am": "<AM name or empty>", "reply": {"subject": "...", "body": "Hi <first name>,\n\n..."}}`.
2. Run `python3 <skill-dir>/scripts/feedback.py nudge kickoff/<slug> --plan nudge-plan.json --today <YYYY-MM-DD> --dry-run`, fix until `PLAN OK`, then run it without `--dry-run`. It writes `feedback/<slug>/<today>-week-2-nudge.md` (`## Notes`, which say Week 3 proceeds with the Blueprint as is, then `## Nudge Draft`) and checks it.
3. It refuses before the reply-by date (`NOT DUE`) and when a Week 2 feedback file already exists (`REPLY LOGGED`); then write nothing.

The nudge body, at most 150 words in WISE's voice (**checked**): a friendly reminder that names the Blueprint or deck, says that so the build keeps moving we will go ahead with the Blueprint as it stands (go ahead, move ahead or proceed), says their thoughts or feedback are still welcome, and offers the walkthrough call again. No new deadline: the only date it may give is the missed reply-by date. The script refuses other month-and-day dates, other weekdays, numeric dates and phrases such as "next week"; vaguer deadlines are yours to avoid. No guilt, no pressure, no stock phrases.
