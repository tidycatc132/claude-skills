# Week 1 email file

Path: `emails/<slug>/<slug>-week-1-email.md`, where `<slug>` is the kickoff folder name (`kickoff/<slug>/<slug>-missing-items.md`). `week1_email.py facts` prints it as `out_path`.

```
Client: <Client Name>
Subject: <subject line>

Hi <greeting name>,

<opening paragraph>

Homepage copy: <content link>          (or a sentence saying the copy is attached)

Design options:
<Option name>: <link>
<Option name>: <link>

What we'd like from you by <Weekday, Month D>:
1. <messaging question>
2. <design question>
3. <facts question>

<calibration paragraph with the fallback>

Details the copy still needs:
- <detail>

Still needed for the build:
- <ask line from facts>
- Access to: <platforms>

Next steps: <what happens next>

<AM full name>
Account Manager, WISE Digital Partners
```

## Lines and blocks

- Line 1 `Client: <Client Name>`, the name from the missing items file's `Client:` line. Line 2 `Subject: ` and at most 70 characters that name the client and say the homepage is ready to review. Line 3 blank. Everything after is the email as pasted, in plain text: no `#` headings, no `**` bold, no `* ` bullets.
- Greeting: `Hi <first name>,` from the contact the user names, or `Hi Dr. <last name>,` when the user gives the contact as Dr.
- Opening: one or two sentences saying the homepage copy and the design options are ready, with one specific detail from the copy (the main service or audience the H1 names) in your own words.
- Copy: with a content link, the line `Homepage copy: <link>` exactly as given. Without one, say the homepage copy is attached. Never make up a link.
- `Design options:` then one line per option, `<name>: <link>`, in the order the user gave them, names and links exactly as given. No blank lines inside the block. Never add a description to the line; a sentence about the options can go in the opening.
- `What we'd like from you by <reply_by_text>:` then exactly three numbered lines, each a question:
  1. whether the messaging sounds like their business,
  2. which design direction they lean toward, saying they don't have to pick one and can tell us what they like and don't like in each,
  3. whether any fact in the copy is wrong.
- Calibration paragraph, right after the questions: this is a check on direction before we produce the remaining pages, not final approval; and if we haven't heard back by `<reply_by_text>`, we'll move ahead with the recommended option (name it when the user gives one, else "the option our design team recommends").
- `Details the copy still needs:` only when `facts` lists `flags`: one `- ` line per flag, in order, rewritten in plain client words (drop internal words like "primary conversion action"; "the phone number to show on the site" is fine). Never copy the bracket markers. With no flags, leave the block out.
- `Still needed for the build:` only when `facts` lists `asks`: each `asks` line as printed, in order. An intake line may add a short `: <what exactly>` or ` (<note>)` after the printed text; the access line may add how to give access (invite WISE as a user, never send passwords). With no asks, leave the block out.
- `Next steps: ` then one or two sentences: we fold their feedback into the homepage and move on to the remaining pages; what they'll see next.
- Sign-off: the AM's full name, then `Account Manager, WISE Digital Partners`, as the last two lines.
- Each block is separated by one blank line. At most 250 words outside the option lines, numbered questions and `- ` lines.

## Dates

`reply_by` is the user's date when they give one (pass `--reply-by` to `facts` and `--user-date` to `check`), else 3 business days after the send date. A date the skill chooses must fall 3 to 5 business days after sending. Write it as `reply_by_text` prints it, for example `Wednesday, October 21`.

## The missing items file

`week1_email.py` reads `kickoff/<slug>/<slug>-missing-items.md` as client-context-update writes it and rejects any other names or statuses (`MISSING ITEMS INVALID`), so nothing drops out of the email silently.

- `Client: <Client Name>` line.
- `| Item | Status | Note |` rows. Items: `Primary contact`, `Website approver`, `Business name, address, phone and hours`, `Logo files`, `Brand guidelines`, `Photos`, `Testimonials or reviews`, `Team members`, `Certifications, awards and memberships`, `Legal or compliance language`, `Sites they like`, `Things to avoid`, `Gap question answers`. Statuses: `received`, `partial`, `missing`, `none`, `n/a`. The email asks for `missing` and `partial` items, under client-facing names (`Gap question answers` becomes `Answers to our open questions`).
- `| Platform | Status | Note |` rows. Platforms: `Domain`, `Hosting`, `Website login`, `Google Analytics`, `Google Search Console`, `Google Business Profile`, `Google Tag Manager`, `Google Ads`, `Meta ads`, `Microsoft Ads`, `CRM, forms or call tracking`. Statuses: `confirmed`, `invite sent`, `needs help`, `someone else manages it`, `not set up`, `not sure`, `no answer`, `n/a`. The email asks for `needs help`, `someone else manages it`, `not sure` and `no answer`, in one `- Access to: ` line with the platforms separated by `; `. `invite sent` waits on WISE, and `not set up` is set up by WISE, so neither is asked for.
