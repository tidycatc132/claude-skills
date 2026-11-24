# What `week2_email.py check` tests

Each row prints `PASS` or `FAIL`, then the run prints `RESULT: PASS` or `RESULT: FAIL`. Fix the email, never the inputs.

| Row | Passes when | Usual fix |
|---|---|---|
| header | `Client:`, `To:`, `Send date:`, `Reply by:`, `Attach:` and `Links:` match the facts and the arguments exactly | Copy the values from facts; `Links: none` when no link was given |
| subject | a `Subject:` line of 1 to 90 characters | Shorten it |
| greeting | a line equal to the facts `greeting` | Use it exactly, on its own line |
| word count | under 250 words from the greeting to the end, still-owed lines included | Cut the opening, lead-ins and bullets |
| sign-off | the last two lines are the AM's name and the title | Put the closing sentence above them |
| deck is primary | a paragraph names `deck_file` and says "first" | Say in that paragraph to open the deck first |
| pdf is the reference | a paragraph names `pdf_file` and says "reference" | Call the PDF the reference copy |
| focus | "direction", "sitemap" and "page content" (or "page copy") all appear | Name all three |
| feedback questions | the three questions appear word for word | Paste them |
| reply-by date | `reply_by_text` appears once, and the prose has no other date, weekday name, "tomorrow" or "next week" (the subject is scanned too; the still-owed lines are not) | Remove other dates; months alone ("in November") are fine |
| reply-by window | the reply-by date is 3 to 5 business days after the send date (skipped with `--user-date`) | Drop `--reply-by` to use the default, unless the AM chose the date |
| walkthrough offer | "walkthrough" or "walk-through" appears | Offer a walkthrough call |
| recommendations | 2 or 3 bullets that are not still-owed lines, each sharing at least three key words with a different Key Strategic Bet | Restate the bet closer to its own words; one bullet per bet |
| still owed | every `asks` line appears exactly, on its own line | Paste the line from facts unchanged |
| figures | every number written in digits, and every number word from four up, in the subject and body is in the briefing's Executive Summary, Key Strategic Bets or Numbers the AM Should Know, the deck, or a missing-items note (the page count is allowed; list numbers, dates and slide numbers in those files do not count) | Use the source figure or drop it |
| no promises | no ranking promise such as "top 3", "page one", "first page" or "number one" | Say what we will do, not where they will rank |
| internal language | none of: wrong if, calibration, AM briefing, briefing, internal, key strategic bets, anticipated, confirm with SEO, or a `[NEEDS INPUT` style flag | Say it in client words |
| voice | no filler phrase and at most one exclamation mark | Plain words |
| copy not reused | no run of 8 words taken from any page's `article.md` | Describe the page; don't quote it |
| links | the body holds every link given and no other | Add the missing link or delete the extra one |

`INPUT MISSING OR INVALID` means an input file is missing or malformed: report it and stop. Do not write the email.
